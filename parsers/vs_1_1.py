import parser
from typing import Callable
from shtypes import *
import copy

def _setoutputused(output: str) -> bool:
    if output in _invalidoutputs: 
        _invalidoutputs[output]()
    used = _outputsused[output]
    _outputsused[output] = True
    return used

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
    if 'Registers:' not in lines:
        return header

    # set uniforms
    uniflines = lines[lines.index("Registers:")+3:]
    header.uniforms = [unifparse(line) for line in uniflines]
    return header

def bodyparse(lines: list[str], outshader) -> None:
    shader.body = []
    for line in lines:
        instr = parser.toinstr(line)
        for op in instr.operands:
            if op.name in _possibleoutputs:
                if _setoutputused(op.name): 
                    continue
                    raise Exception(f"Output {op.name} already assigned")
                setattr(outshader.header.outputs, _outputstoname[op.name], op.name)
        # add a line to properly declare outputs the line before (if there are any)
        shader.body += _instr[instr.opcode[0]](instr.opcode, instr.operands)

def _parsedcl(opcode, operands, header: shader_header) -> None: 
    if operands[0].name in ['2d', 'cube', 'volume', '3d']: # texture samplers
        raise Exception("Texture samplers not supported")
    
    if (opcode[1] == 'texcoord'): opcode[1] += '0'
    # in vs1_1 only inputs are listed with dcl, outputs are only listed when used
    header.inputs += [f'.in {opcode[1]} {operands[0]}']

def addconstant(opcode: list[str], operands: list[register], out: shader_header):
    unif: constantunif = constantunif()
    unif.id = int(operands[0].name[1:])
    unif.values = [op.name for op in operands[1:]]
    match opcode[0]:
        case 'def': unif.type = uniftype.FLOAT_UNIF
        case 'defb': unif.type = uniftype.BOOL_UNIF
        case 'defi': unif.type = uniftype.INT_UNIF
    out.constants += [unif]

def vs(opcode, operands, out):
    out.type = shadertype.VERTEX_SHADER
    out.version = '1_1'

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
    
    out.header = headerparse(header)
    setupparse(out.header, setup)
    bodyparse(body, out) # also includes header because in this version, outputs are only declared by instructions
    
    return out

_outputsused: dict[str, bool] = {
    'oPos': False,
    'oD0': False,
    'oT0': False,
    'oT1': False,
    'oT2': False,
    'oT3': False
}

_outputstoname: dict[str, str] = {
    'oPos': 'position',
    'oD0': 'color',
    'oT0': 'texcoord0',
    'oT1': 'texcoord1',
    'oT2': 'texcoord2',
    'oT3': 'texcoord0w'
}

_invalidoutputs: dict[str, Callable[[], None]] = {
    'oD1': lambda: (_ for _ in ()).throw(Exception('More than 1 color output register not supported')),
    'oT4': lambda: (_ for _ in ()).throw(Exception('More than 3 texcoord output registers not supported')),
    'oT5': lambda: (_ for _ in ()).throw(Exception('More than 3 texcoord output registers not supported')),
    'oT6': lambda: (_ for _ in ()).throw(Exception('More than 3 texcoord output registers not supported')),
    'oT7': lambda: (_ for _ in ()).throw(Exception('More than 3 texcoord output registers not supported')),
    'oFog': lambda: (_ for _ in ()).throw(Exception('Fog output register not supported')),
    'oPts': lambda: (_ for _ in ()).throw(Exception('Point size output register not supported')),
}

_possibleoutputs = (list(_outputstoname.keys()) + list(_invalidoutputs.keys()))

def _type1(opcode, operands: list[register]) -> list[instr]:
    if operands[1].is_constant() and operands[2].is_constant():
        intermediate = operands[0]
        if operands[0].is_output():
            intermediate = register("dummy").mark_to_be_replaced()
        return [_instr['mov'](['mov'], [intermediate, operands[2]])[0], instr(opcode, [operands[0], operands[1], intermediate])]
    else:
        if operands[2].is_constant():
            return [instr(opcode, [operands[0], operands[2], operands[1]])]

    return [instr(opcode, operands)]

def _type1i(opcode, operands: list[register]) -> list[instr]:
    if operands[1].is_constant() and operands[2].is_constant():
        intermediate = operands[0]
        if operands[0].is_output():
            intermediate = register("dummy").mark_to_be_replaced()
        return _instr['mov'](['mov'], [intermediate, operands[1]]) + [instr(opcode, [operands[0], intermediate, operands[2]])]
    else:
        return [instr(opcode, operands)]

def _type1u(opcode, operands: list[register]) -> list[instr]:
    return [instr(opcode, operands)]
    
def _frc(opcode, operands: list[register]) -> list[instr]:
    intermediate: register = register("dummy")
    intermediate.mark_to_be_replaced()
    if operands[0] == operands[1] or operands[0].is_output(): 
        return _type1u(['flr'], [intermediate, operands[1]]) + _instr['sub'](['sub'], [operands[0], operands[1], intermediate])
    return _type1u(['flr'], operands) + _instr['sub'](['sub'], [operands[0], operands[1], operands[0]])

def _mad(opcode, operands: list[register]) -> list[instr]:
    numconstants = sum([op.is_constant() for op in operands])
    # if there are no constants or there is a single uniform in either src2 or src3 do nothing
    # technically this instruction shouldn't be used since mad actually rounds the intermediate value but i'll fix it later
    if numconstants == 0 or (numconstants == 1 and not operands[1].is_constant()): return [instr(['mad'], operands)]
    
    intermediate: register = operands[0]
    if operands[0].is_output() or operands[0] in operands[1:]:
        intermediate = register("dummy")
        intermediate.mark_to_be_replaced()
        
    return _instr['mul'](['mul'], [intermediate, operands[1], operands[2]]) + _instr['add'](['add'], [operands[0], operands[3], intermediate])

_instr: dict[str, Callable[[list[str], list[register]], list[instr]]] = {
    'add': _type1,
    'dp3': _type1,
    'dp4': _type1,
    'dst': _type1i,
    'exp': lambda opcode, operands: _type1u(['ex2'], operands),
    'expp': lambda opcode, operands: _type1u(['ex2'], operands),
    'frc': _frc,
    # 'lit': lambda opcode, operands: f'max {operands[0]}.x, {operands[1]}\n',
    'log': lambda opcode, operands: _type1u(['lg2'], operands),
    'logp': lambda opcode, operands: _type1u(['lg2'], operands),
    'mad': _mad,
    'max': _type1,
    'min': _type1,
    # required because in vs_1_1 the mova instruction doesn't exist so mov is used for both
    'mov': lambda opcode, operands: _type1u(['mova'], operands) if operands[0].is_addressing() else _type1u(opcode, operands),
    'mul': _type1,
    'nop': lambda opcode, operands: [instr(['nop'])],
    'rcp': _type1u,
    'rsq': _type1u,
    'sge': _type1i,
    'slt': _type1i,
    'sub': lambda opcode, operands: _instr['add'](['add'], [operands[0], operands[1], copy.deepcopy(operands[2]).negate()]),
}