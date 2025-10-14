import parser
from typing import Callable
from shtypes import *
import parsers.vs_2_0 as vs_2_0

_outputstoname: dict[str, str] = {
    'oPos': 'position',
    'oD0': 'color',
    'oT0': 'texcoord0',
    'oT1': 'texcoord1',
    'oT2': 'texcoord2',
    'oT3': 'texcoord0w'
}

def unifparse(line: str) -> uniform:
    unif = uniform()
    parts = [part for part in line.split(' ') if len(part) > 0]
    unif.type = uniftype(parts[1][0])
    unif.id = int(parts[1][1:])
    unif.size = int(parts[2])
    unif.name = parts[0]
    return unif
    
def headerparse(lines: list[str]) -> shader_header:
    header: shader_header = shader_header()
    # set uniforms
    uniflines = lines[lines.index("Registers:")+3:]
    header.uniforms = [unifparse(line) for line in uniflines]
    return header

def bodyparse(lines: list[str], outshader) -> None:
    shader.body = []
    for line in lines:
        components = line.replace(',', '').split()
        opcode = components[0].split("_")
        operands = components[1:]
        opbase = [op.split('.')[0] for op in operands]
        for op in opbase:
            if op in _outputstoname:
                setattr(outshader.header.outputs, _outputstoname[op], op)
        # add a line to properly declare outputs the line before (if there are any)
        shader.body += _instr[opcode[0]](opcode, [register(op) for op in operands])

def _parsedcl(opcode, operands, header: shader_header) -> None: 
    if (opcode[1] == 'texcoord'): opcode[1] += '0'
    # in vs1_1 only inputs are listed with dcl, outputs are only listed when used
    header.inputs += [f'.in {opcode[1]} {operands[0]}']

def addconstant(opcode, operands, out: shader_header):
    unif: constantunif = constantunif()
    unif.id = operands[0][1:]
    unif.values = operands[1:]
    match opcode[0]:
        case 'def': unif.type = uniftype.FLOAT_UNIF
        case 'defb': unif.type = uniftype.BOOL_UNIF
        case 'defi': unif.type = uniftype.INT_UNIF
    out.constants += [unif]

def vs(opcode, operands, out):
    out.type = shadertype.VERTEX_SHADER
    out.version = '2_x'

def setupparse(out: shader_header, lines):
    # set constant, inputs, outputs from the setup stuff
    setupinstr = {
        'vs': vs,
        'dcl': _parsedcl,
        'def': addconstant,
        'defb': addconstant,
        'defi': addconstant,
    }
    
    for line in lines:
        components = line.replace(',', '').split()
        opcode = components[0].split("_")
        operands = components[1:]
        setupinstr[opcode[0]](opcode, operands, out)

def shaderparse(sh) -> shader:
    out = shader()
    
    
    header = [line[3:].strip() for line in sh[:[sh.index(l) for l in sh if not l.startswith('//') and not l.isspace()][0]] if not (line[3:].isspace() or len(line[3:]) < 1)]
    body = [line.strip() for line in sh if not line.startswith('//') and not line.isspace()] # all non-commented lines
    setup = []
    
    setupcommands = ['vs_', 'def', 'dcl']
    
    for line in body:
        if not line[:3] in setupcommands:
            setup = body[:body.index(line)]
            body = body[body.index(line):]
            break
    
    out.header = headerparse(header)
    setupparse(out.header, setup)
    bodyparse(body, out) # also includes header because in this version, outputs are only declared by instructions
    
    return out
    
def _parseif(opcode, operands) -> list[instr]:
    if len(opcode) == 1: 
        if 'p' in operands[0]: return [instr('ifc', [operands[0].replace('p0', 'cmp')])]
        else: return [instr('ifu', operands)]#[f'ifu {operands[0]}\n']
    return [instr('cmp', [operands[0], opcode[1], opcode[1], operands[1]]), instr('ifc', 'cmp.x')]

def _parsesetp(opcode, operands: list[register]) -> list[instr]:
    _oppositecmp = {
        'eq': 'eq',
        'ne': 'ne',
        'lt': 'gt',
        'le': 'ge',
        'gt': 'lt',
        'ge': 'le'
    }
    if 'c' in operands[1].name or 'c' in operands[2].name:
        return [instr('cmp', [operands[2], register(_oppositecmp[opcode[1]]), register(_oppositecmp[opcode[1]]), operands[1]])]
    return [instr('cmp', [operands[1], opcode[1], opcode[1], operands[2]])]

def _parsebreak(opcode, operands) -> list[instr]:
    if len(opcode) == 1:
        return [instr('break')]
    else:
        return _instr['setp'](['setp'], [operands[0], operands[1]]) + [instr('breakc', [register('cmp.x')])]

# yet to implement:
# lit - vs
# m3x2 - vs (generally unused, low prio)
# m3x3 - vs (generally unused, low prio)
# m3x4 - vs (generally unused, low prio)
# m4x3 - vs (generally unused, low prio)
# m4x4 - vs (generally unused, low prio)
# setp_comp - vs
# sincos - vs (inadvisable to use, low prio)

vs_2_x_instr: dict[str, Callable[[list[str], list[register]], list[instr]]] = {
    'break': _parsebreak,
    'breakp': lambda opcode, operands: [instr('breakc', [operands[0]])],
    'callnz': lambda opcode, operands: [instr('call' + 'u' if operands[1].is_bool() else 'c', [operands[1], operands[0]])],
    'if': _parseif,
    'setp': _parsesetp,
}

_instr = {**vs_2_0._instr, **vs_2_x_instr}