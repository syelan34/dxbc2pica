import parser
from typing import Callable
from shtypes import *
import parsers.vs_2_x as vs_2_x

def unifparse(line: str) -> uniform:
    unif = uniform()
    parts = [part for part in line.split(' ') if len(part) > 0]
    try:
        unif.type = uniftype(parts[1][0])
    except ValueError:
        raise Exception(f'Invalid uniform "{parts[1]}"')
    
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
    if ('s' in operands[0]):
        raise Exception("Texture samplers not supported")
        
    if opcode[1] in _outputstoname:
        setattr(header.outputs, _outputstoname[opcode[1]], operands[0])
    else:
        raise Exception(f'Invalid Output {'_'.join(opcode)}')

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
    out.version = '3_0'

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

_outputstoname: dict[str, str] = {
    'position': 'position',
    'color': 'color',
    'texcoord': 'texcoord0',
    'texcoord1': 'texcoord1',
    'texcoord2': 'texcoord2',
    'texcoord3': 'texcoord0w',
    'normal': 'normalquat',
    'tangent': 'view',
}

vs_3_0_instr: dict[str, Callable[[list[str], list[register]], list[instr]]] = {
    'texldl': lambda opcode, operands: (_ for _ in ()).throw(Exception('texldl not supported')),
}

_instr = {**vs_2_x._instr, **vs_3_0_instr}