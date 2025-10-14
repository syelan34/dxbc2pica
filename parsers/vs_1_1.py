import parser
from typing import Callable
from shtypes import *
import copy

# def clearstate():
#     for key in _outputsused.keys():
#         _outputsused[key] = False

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
            if op in _possibleoutputs:
                if _setoutputused(op): 
                    continue
                    raise Exception(f"Output {op} already assigned")
                setattr(outshader.header.outputs, _outputstoname[op], op)
        # add a line to properly declare outputs the line before (if there are any)
        shader.body += _instr[opcode[0]](opcode, [register(op) for op in operands])

def _parsedcl(opcode, operands, header: shader_header) -> None: 
    if operands[0] in ['2d', 'cube', 'volume', '3d']: # texture samplers
        raise Exception("Texture samplers not supported")
    
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
    if 'c' in operands[1].name and 'c' in operands[2].name:
        return [_instr['mov'](['mov'], [operands[0], operands[1]])[0], instr(opcode[0], [operands[0], operands[2], operands[0]])]
    else:
        if 'c' in operands[2].name:
            return [instr(opcode[0], [operands[0], operands[2], operands[1]])]
        return [instr(opcode[0], operands)]
        
def _type1i(opcode, operands: list[register]) -> list[instr]:
    if 'c' in operands[1].name and 'c' in operands[2].name:
        return _instr['mov'](['mov'], [operands[0], operands[1]]) + [instr(opcode[0], [operands[0], operands[2].negate(), operands[0].negate()])]
    else:
        return [instr(opcode[0], operands)]

def _type1u(opcode, operands: list[register]) -> list[instr]:
    return [instr(opcode[0], operands)]
    
def _frc(opcode, operands: list[register]) -> list[instr]:
    intermediate: register = register("dummy")
    intermediate.mark_to_be_replaced()
    if operands[0] == operands[1] or operands[0].is_output(): 
        return _type1u(['flr'], [intermediate, operands[1]]) + _instr['sub'](['sub'], [operands[0], operands[1], intermediate])
    return _type1u(['flr'], operands) + _instr['sub'](['sub'], [operands[0], operands[1], operands[0]])

def _mad(opcode, operands: list[register]) -> list[instr]:
    numconstants = sum([op.is_constant() for op in operands])
    # if there are no constants or there is a uniform in either src2 or src3 do nothing
    if numconstants == 0 or (numconstants == 1 and 'c' not in operands[3].name): return [instr('mad', operands)]
    
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
    'nop': lambda opcode, operands: [instr('nop')],
    'rcp': _type1u,
    'rsq': _type1u,
    'sge': _type1i,
    'slt': _type1i,
    'sub': lambda opcode, operands: _instr['add'](['add'], [operands[0], operands[1], copy.deepcopy(operands[2]).negate()]),
}