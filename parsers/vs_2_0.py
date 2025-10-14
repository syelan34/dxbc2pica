import parser
from typing import Callable
from shtypes import *
import copy
import parsers.vs_1_1 as vs_1_1

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
    out.version = '2_0'

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


def _type1u(opcode, operands: list[register]) -> list[instr]:
    return [instr(opcode[0], operands)]
    
def _lrp(opcode, operands: list[register]) -> list[instr]:
    outputreg0 = copy.deepcopy(operands[0])
    outputreg1 = copy.deepcopy(operands[0])
    
    outputreg0.mark_to_be_replaced()

    return _instr['sub'](['sub'], [outputreg0, operands[2], operands[3]]) + _instr['mad'](['mad'], [outputreg1, operands[0], outputreg0, operands[3]])
    
# yet to implement:
# lit - vs
# m3x2 - vs (generally unused, low prio)
# m3x3 - vs (generally unused, low prio)
# m3x4 - vs (generally unused, low prio)
# m4x3 - vs (generally unused, low prio)
# m4x4 - vs (generally unused, low prio)
# setp_comp - vs
# sincos - vs (inadvisable to use, low prio)

vs_2_0_instr: dict[str, Callable[[list[str], list[register]], list[instr]]] = {
    'abs': lambda opcode, operands: _instr['max'](['max'], [operands[0], operands[1], operands[1].negate()]),
    'call': lambda opcode, operands: [instr(opcode[0], operands)],
    'callnz': lambda opcode, operands: [instr('callu', [operands[1], operands[0]])],
    'crs': lambda opcode, operands: (_ for _ in ()).throw(Exception('crs not supported, make sure your compiler is set not to keep macros')),
    'else': lambda opcode, operands: [instr('.else')],
    'endif': lambda opcode, operands: [instr('.end')],
    'endloop': lambda opcode, operands: [instr('.end')],
    'endrep': lambda opcode, operands: [instr('.end')],
    'if': lambda opcode, operands: _type1u(['ifu'], operands),
    'label': lambda opcode, operands: [instr(operands[0].name)],
    'loop': lambda opcode, operands: [instr('for', [operands[1]])],
    'lrp': _lrp,
    'mov': _type1u,
    'mova': _type1u,
    'nrm': lambda opcode, operands: 
        _instr['dp4'](['dp4'], [operands[0], operands[1], operands[1]]) + 
        _instr['rsq'](['rsq'], [operands[0], operands[0]]) + 
        _instr['mul'](['mul'], [operands[0], operands[1], operands[0]]),
    # from Microsoft's documentation (https://learn.microsoft.com/en-us/windows/win32/direct3dhlsl/pow---vs)
    'pow': lambda opcode, operands: 
        _instr['abs'](['abs'], [operands[0], operands[1]]) + 
        _instr['log'](['log'], [operands[0], operands[0]]) + 
        _instr['mul'](['mul'], [operands[0], operands[2], operands[0]]) + 
        _instr['exp'](['exp'], [operands[0], operands[0]]),
    'rep': lambda opcode, operands: [instr('for', [operands[0]])],
    'ret': lambda opcode, operands: [instr('jmp')], # incomplete instruction, must be followed by a label
    # #TODO: use 4 instruction version in case of uniform instead of the autogenerated 5 using movs
    'sgn': lambda opcode, operands: 
        _instr['slt'](['slt'], [operands[2], operands[1].negate(), operands[1]]) + 
        _instr['slt'](['slt'], [operands[3], operands[1], operands[1].negate()]) + 
        _instr['sub'](['sub'], [operands[0], operands[2], operands[3]]),
    'sincos': lambda opcode, operands: (_ for _ in ()).throw(Exception('sincos not supported')),
}

_instr = {**vs_1_1._instr, **vs_2_0_instr}