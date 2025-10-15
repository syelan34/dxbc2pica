import parser
from typing import Callable
from shtypes import *
import parsers.vs_2_x as vs_2_x
import parsers.vs_1_1 as vs_1_1

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

def bodyparse(lines: list[str], outshader) -> None:
    shader.body = []
    for line in lines:
        instr = parser.toinstr(line)
        for op in instr.operands:
            if op.name in _outputstoname:
                setattr(outshader.header.outputs, _outputstoname[op.name], op.name)
        # add a line to properly declare outputs the line before (if there are any)
        shader.body += _instr[instr.opcode[0]](instr.opcode, instr.operands)

def _parsedcl(opcode, operands, header: shader_header) -> None:
    if ('s' in operands[0].name):
        raise Exception("Texture samplers not supported")
        
    if opcode[1] in _outputstoname:
        setattr(header.outputs, _outputstoname[opcode[1]], operands[0].name)
    else:
        raise Exception(f'Invalid Output {'_'.join(opcode)}')

def vs(opcode, operands, out):
    out.type = shadertype.VERTEX_SHADER
    out.version = '3_0'

def setupparse(out: shader_header, lines):
    # set constant, inputs, outputs from the setup stuff
    setupinstr = {
        'vs': vs,
        'dcl': _parsedcl,
        'def': vs_1_1.addconstant,
        'defb': vs_1_1.addconstant,
        'defi': vs_1_1.addconstant,
    }
    
    for line in lines:
        instr = parser.toinstr(line)
        setupinstr[instr.opcode[0]](instr.opcode, instr.operands, out)

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
    
    out.header = vs_1_1.headerparse(header)
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