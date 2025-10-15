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
    if operands[0].name in ['2d', 'cube', 'volume', '3d']: # texture samplers
        raise Exception("Texture samplers not supported")
    
    if (opcode[1] == 'texcoord'): opcode[1] += '0'
    # in vs1_1 only inputs are listed with dcl, outputs are only listed when used
    header.inputs += [f'.in {opcode[1]} {operands[0]}']

def vs(opcode, operands, out):
    out.type = shadertype.VERTEX_SHADER
    out.version = '2_0'

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
    
def _lrp(opcode, operands: list[register]) -> list[instr]:
    intermediate: register = operands[0]
    
    if operands[0] in operands[1:] or operands[0].is_output():
        intermediate = register("dummy").mark_to_be_replaced()

    return _instr['sub'](['sub'], [intermediate, operands[2], operands[3]]) + _instr['mad'](['mad'], [operands[0], operands[1], intermediate, operands[3]])


def _nrm(opcode, operands) -> list[instr]:
    intermediate: register = operands[0]
    
    if operands[1].name == operands[0].name or operands[0].is_output():
        intermediate = register("dummy").mark_to_be_replaced()
        
    return _instr['dp4'](['dp4'], [intermediate, operands[1], operands[1]]) + _instr['rsq'](['rsq'], [intermediate, intermediate]) + _instr['mul'](['mul'], [operands[0], operands[1], intermediate])    

# from Microsoft's documentation (https://learn.microsoft.com/en-us/windows/win32/direct3dhlsl/pow---vs)
def _pow(opcode, operands) -> list[instr]:
    intermediate: register = operands[0]
    
    if operands[1].name == operands[0].name or operands[0].is_output():
        intermediate = register("dummy").mark_to_be_replaced()
    
    return _instr['abs'](['abs'], [intermediate, operands[1]]) + _instr['log'](['log'], [intermediate, intermediate]) + _instr['mul'](['mul'], [intermediate, operands[2], intermediate]) + _instr['exp'](['exp'], [operands[0], intermediate])

def _crs(opcode, operands) -> list[instr]:
    intermediate = operands[0]
    
    if operands[0].name == operands[1].name or operands[0].is_output():
        intermediate = register("dummy").mark_to_be_replaced()

    return _instr['mul'](['mul'], [intermediate, operands[1].setswizzle("yzx"), operands[2].setswizzle("zxy")]) + _instr['mad'](['mad'], [operands[0], operands[1].setswizzle("zxy"), operands[2].setswizzle("yzx"), copy.deepcopy(intermediate).negate()])


def _sgn(opcode, operands) -> list[instr]:
    return _instr['slt'](['slt'], [operands[2], copy.deepcopy(operands[1]).negate(), operands[1]]) + _instr['slt'](['slt'], [operands[3], operands[1], copy.deepcopy(operands[1]).negate()]) + _instr['sub'](['sub'], [operands[0], operands[2], operands[3]])

vs_2_0_instr: dict[str, Callable[[list[str], list[register]], list[instr]]] = {
    'abs': lambda opcode, operands: _instr['max'](['max'], [operands[0], operands[1], copy.deepcopy(operands[1]).negate()]),
    'call': lambda opcode, operands: [instr([opcode[0]], operands)],
    'callnz': lambda opcode, operands: [instr(['callu'], [operands[1], operands[0]])],
    'crs': _crs,
    'else': lambda opcode, operands: [instr(['.else'])],
    'endif': lambda opcode, operands: [instr(['.end'])],
    'endloop': lambda opcode, operands: [instr(['.end'])],
    'endrep': lambda opcode, operands: [instr(['.end'])],
    'if': lambda opcode, operands: vs_1_1._type1u(['ifu'], operands),
    'label': lambda opcode, operands: [instr(['proc', 'start'],operands)],
    'loop': lambda opcode, operands: [instr(['for'], [operands[1]])],
    'lrp': _lrp,
    'mov': vs_1_1._type1u,
    'mova': vs_1_1._type1u,
    'nrm': _nrm,
    'pow': _pow,
    'rep': lambda opcode, operands: [instr(['for'], [operands[0]])],
    'ret': lambda opcode, operands: [instr(['proc', 'end'])],
    # #TODO: use 4 instruction version in case of uniform instead of the autogenerated 5 using movs
    'sgn': _sgn,
    'sincos': lambda opcode, operands: (_ for _ in ()).throw(Exception('sincos not supported')),
}

_instr = {**vs_1_1._instr, **vs_2_0_instr}