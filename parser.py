import inout
from shtypes import *
from inout import comment
import copy
import parsers.vs_1_1, parsers.vs_2_0, parsers.vs_2_x, parsers.vs_3_0

from typing import Callable


shaderparsers: dict[str, Callable[[list[str]], shader]] = {
    'vs_1_1':  parsers.vs_1_1.shaderparse,
    'vs_2_0':  parsers.vs_2_0.shaderparse,
    'vs_2_x':  parsers.vs_2_x.shaderparse,
    'vs_2_sw': parsers.vs_2_x.shaderparse,
    'vs_3_0':  parsers.vs_3_0.shaderparse,
    'vs_3_sw': parsers.vs_3_0.shaderparse,
}

def getunusedregs(shader: shader) -> list[register]:
    regsused: list[str] = []
    for instr in shader.body:
        for reg in instr.operands:
            regsused.append(reg.name)
    return list(filter(lambda reg: reg.name != '', [register(f'r{i}') if f'r{i}' not in regsused else register('') for i in range(16)]))
    
    
def findfreescratchreg(input: shader, index: int) -> register:
    # a register is free whenever the next time it's used is writing to it
    
    flowcontrol = [
        'break', 'breakc', 'call', 'callc', 'callu', '.else', '.end', 'ifc', 'ifu', 'for' # for loop is usually fine except for when loop is zero
    ]
    
    numinstructions = len(shader.body[index+1:])
    
    
    for i in range(16):
        for (instr_idx, instruction) in enumerate(shader.body[index+1:]):
            # check for flow control instructions
            if instruction.opcode in flowcontrol:
                # finally, double check there's no unused registers that we can utilize
                unused = getunusedregs(input)
                if len(unused) == 0:
                    raise Exception("No unused registers, unable to determine whether others are available due to possible jump")
                else:
                    return unused[0]
            else:
                read = sum([r.name == f'r{i}' and not r.tobereplaced for r in instruction.operands[1:]]) > 0
                
                if read: 
                    break # register is read after this line, therefore we can't use it
                
                written = instruction.dest().name == f'r{i}' and not instruction.dest().tobereplaced
                if written or instr_idx + index == len(shader.body) - 1: return register(f'r{i}')
                # if this is the last instruction and the register still hasn't been touched at all then we can use it
                if instr_idx+1 == numinstructions:
                    return register(f'r{i}')
        
    # finally, double check there's no unused registers that we can utilize
    unused = getunusedregs(input)
    if len(unused) == 0:
        raise Exception("No unused registers, unable to determine whether others are available due to possible jump")
    else:
        return unused[0]
    raise Exception("No registers guaranteed available to use")

def parseshader(shader, version) -> shader:
    return fixupshader(shaderparsers[version](shader))
    return shaderparsers[version](shader)

def fixupshader(input: shader) -> shader:
    # fix register overwrites
    for (index, instr) in enumerate(input.body):
        for (opid, reg) in enumerate(instr.operands):
            if reg.tobereplaced != 0:
                print(f'replacing {reg.as_line()} in instruction {instr.as_line()}')
                freereg = findfreescratchreg(input, index)
                print(f'using register {freereg.as_line()}')
                reg.tobereplaced = 0
                reg.name = freereg.name
    
    # fix double output write
    for (index, instr) in enumerate(input.body):
        num_outputs_in_instr_operands = sum([reg.name in vars(shader.header.outputs).values() for reg in instr.operands[1:]])
        
        if num_outputs_in_instr_operands > 0: # there is an output being read from in this instruction (not allowed)
            
            # figure out which output registers are being read from
            # make a deep copy because otherwise that list can be overwritten when we fix up the instruction
            outputsread = copy.deepcopy(list(filter(lambda op: op[1].name in vars(shader.header.outputs).values(), enumerate(instr.operands[1:]))))
            
            # look backwards to see when each output was last written to, and replace both with any free scratch register
            for outputindex, outputread in outputsread:
                for previousinstrindex, previousinstr in enumerate(input.body[index-1::-1]):
                    if previousinstr.dest() == outputread:
                        freereg = findfreescratchreg(input, index)
                        previousinstr.operands[0].name = freereg.name
                        instr.operands[outputindex + 1].name = freereg.name
    return input

def outputshader(shader) -> None:
    # print file info
    
    inout.printline(comment(f'DirectX Shader Model: {['vs_', 'gs_'][shader.header.type.value]}{shader.header.version}'))
    inout.printline()
    
    # print header
    inout.printline(comment("Uniforms"))
    [inout.printline(unif.as_instr()) for unif in shader.header.uniforms]
    inout.printline()
    
    inout.printline(comment("Constants"))
    [inout.printline(unif.as_instr()) for unif in shader.header.constants]
    inout.printline()
    
    inout.printline(comment("Outputs"))
    inout.printline(shader.header.outputs.as_instr())
    inout.printline()
    
    # print body
    
    inout.printline(comment("Main Body"))
    
    inout.printline('.proc main')
    
    inout.printline([instr.as_line() for instr in shader.body])
    
    inout.printline('end')
    inout.printline('.end')
    inout.printline()
    
    # Ending info
    
    inout.printline(comment(f'{len(shader.body) + 1} instruction slots used ({round((len(shader.body) + 1)/512*100, 2)}%)'))
    pass

# def parse(line) -> list[instr]:
#     try:
#         # remove leading and trailing whitespace
#         line = line.strip()
#         if line == '': # ignore empty lines
#             return []
#         # handle comments
#         # if line.startswith('//'):
#         #     return [comment(line[3:])]
#         # handle version
#         # if line.startswith('vs_'):
#         #     return _parse_version(line)
#         components = line.replace(',', '').split()
#         opcode = components[0].split("_")
#         operands = components[1:]
#         opbase = [op.split('.')[0] for op in operands]
#         return [
#             filter(
#                 None, 
#                 [
#                     f'.out {op} {_outputstoname[op]}\n' 
#                     for op in opbase
#                     if op in _possibleoutputs and not _setoutputused(op)
#                 ] + 
#                 _instr[opcode[0]](opcode, operands)
#             )
#         ]
#     except KeyError:
#         # return [comment(f'Unexpected string: {line}')]
#         return []


# def _negate(operand: str) -> str:
#     return operand.replace('-', '') if '-' in operand else '-' + operand

# def _parse_version(line):
#     if line not in ['vs_1_1', 'vs_2_0', 'vs_2_x', 'vs_2_sw', 'vs_3_0', 'vs_3_sw']:
#         raise Exception(f'Only vs_3_0 or lower is supported, got {line}')
#     else: 
#         return [comment('Vertex Shader generated by dxbc2pica 0.0.1'), comment(f'd3d version: {line}'), comment()]

# def _parsebreak(opcode, operands) -> list[instr]:
#     if len(opcode) == 1:
#         return [instr(opcode[0])]
#     else:
#         return _instr['setp'](['setp'], [operands[0], operands[1]]) + [instr('breakc', ['cmp.x'])]

# def _parsedcl(opcode, operands) -> list[str]: 
#     if operands[0] in ['2d', 'cube', 'volume', '3d']: # texture samplers
#         raise Exception("Texture samplers not supported")
    
#     # output reg or input reg?
#     outopcode = '.out -' if ('o' in operands[0]) else '.in'

#     if opcode[1] == 'texcoord': # force there to be a number
#         return [f'{outopcode} {opcode[1]}0 {operands[0]}{inout.ignoretab()}\n']
#     return [f'{outopcode} {opcode[1]} {operands[0]}{inout.ignoretab()}\n']

# def _type1(opcode, operands) -> list[instr]:
#     if 'c' in operands[1] and 'c' in operands[2]:
#         return [_instr['mov'](['mov'], [operands[0], operands[1]])[0], instr(opcode[0], [operands[0], operands[2], operands[0]])]
#     else:
#         if 'c' in operands[2]:
#             return [instr(opcode[0], [operands[0], operands[2], operands[1]])]
#             # return [f'{opcode[0]} {operands[0]}, {operands[2]}, {operands[1]}\n']
#         return [instr(opcode[0], operands)]
        
# def _type1i(opcode, operands) -> list[instr]:
#     if 'c' in operands[1] and 'c' in operands[2]:
#         return _instr['mov'](['mov'], [operands[0], operands[1]]) + [instr(opcode[0], [operands[0], _negate(operands[2]), _negate(operands[0])])]
#     else:
#         return [instr(opcode[0], operands)]

# def _type1u(opcode, operands) -> list[instr]:
#     return [instr(opcode[0], operands)]

# def _parseif(opcode, operands) -> list[str]:
#     inout.inctab_after();
#     if len(opcode) == 1: 
#         if 'p' in operands[0]: return [f'ifc {operands[0].replace('p0', 'cmp')}\n']
#         else: return [f'ifu {operands[0]}\n']
#     return [
#         f'cmp {operands[0]}, {opcode[1]}, {opcode[1]}, {operands[1]}\n',
#         'ifc cmp.x\n'
#     ]
    
# def _parsemad(opcode, operands) -> list[instr]:
#     numconstants = sum(['c' in op for op in operands])
#     # if there are no constants or there is a uniform in either src2 or src3 do nothing
#     if sum(['c' in op for op in operands]) == 0 or (numconstants == 1 and 'c' not in operands[1]): return [instr('mad', operands)]
#     return _instr['mul'](['mul'], operands) + _instr['add'](['add'], [operands[0], operands[0], operands[3]])

# def _parsesetp(opcode, operands) -> list[str]:
#     _oppositecmp = {
#         'eq': 'eq',
#         'ne': 'ne',
#         'lt': 'gt',
#         'le': 'ge',
#         'gt': 'lt',
#         'ge': 'le'
#     }
#     if 'c' in operands[1] or 'c' in operands[2]:
#         return [f'cmp {operands[2]}, {_oppositecmp[opcode[1]]}, {_oppositecmp[opcode[1]]}, {operands[1]}\n']
#     return [f'cmp {operands[1]}, {opcode[1]}, {opcode[1]}, {operands[2]}\n']
    
# def _setoutputused(output: str) -> bool:
#     if output in _invalidoutputs: 
#         _invalidoutputs[output]()
#     used = _outputsused[output]
#     _outputsused[output] = True
#     return used

# # yet to implement:
# # lit - vs
# # m3x2 - vs (generally unused, low prio)
# # m3x3 - vs (generally unused, low prio)
# # m3x4 - vs (generally unused, low prio)
# # m4x3 - vs (generally unused, low prio)
# # m4x4 - vs (generally unused, low prio)
# # setp_comp - vs
# # sincos - vs (inadvisable to use, low prio)

# _instr: dict[str, Callable[[list[str], list[str]], list[instr]]] = {
#     'abs': lambda opcode, operands: _instr['max'](['max'], [operands[0], operands[1], _negate(operands[1])]),
#     'add': _type1,
#     # 'break': _parsebreak,
#     'breakp': lambda opcode, operands: [instr(opcode='breakc', operands=[operands[0].replace('p0', 'cmp')])],
#     'call': lambda opcode, operands: [instr(opcode, operands)],
#     # 'callnz': lambda opcode, operands: [f'call{'u' if 'b' in operands[1] else 'c'} {operands[1].replace('p0', 'cmp')}, {operands[0]}\n'],
#     'crs': lambda opcode, operands: (_ for _ in ()).throw(Exception('crs not supported, make sure your compiler is set not to keep macros')),
#     # 'dcl': _parsedcl,
#     # 'def': lambda opcode, operands: [f'.constf {operands[0]}({operands[1]}, {operands[2]}, {operands[3]}, {operands[4]}{inout.ignoretab()})\n'],
#     'defb': lambda opcode, operands: (_ for _ in ()).throw(Exception('defb not supported')),
#     # 'defi': lambda opcode, operands: [f'.consti {operands[0]}({operands[1]}, {operands[2]}, {operands[3]}, {operands[4]}){inout.ignoretab()}\n'],
#     'dp3': _type1,
#     'dp4': _type1,
#     'dst': _type1i,
#     'else': lambda opcode, operands: [instr('.else')],
#     'endif': lambda opcode, operands: [instr('.end')],
#     'endloop': lambda opcode, operands: [instr('.end')],
#     'endrep': lambda opcode, operands: [instr('.end')],
#     'exp': lambda opcode, operands: _type1u(['ex2'], operands),
#     'expp': lambda opcode, operands: _type1u(['ex2'], operands),
#     'frc': lambda opcode, operands: _type1u(['flr'], operands) + _instr['sub'](['sub'], [operands[0], operands[1], operands[0]]),
#     # 'if': _parseif,
#     'label': lambda opcode, operands: [instr(operands[0])],
#     # 'lit': lambda opcode, operands: f'max {operands[0]}.x, {operands[1]}\n',
#     'log': lambda opcode, operands: _type1u(['lg2'], operands),
#     'logp': lambda opcode, operands: _type1u(['lg2'], operands),
#     # 'loop': lambda opcode, operands: [f'for {operands[1]}\n'],
#     'lrp': lambda opcode, operands: _instr['sub'](['sub'], [operands[0], operands[2], operands[3]]) + _instr['mul'](['mul'], [operands[0], operands[1], operands[0]]) + _instr['add'](['add'], [operands[0], operands[0], operands[3]]),
#     'mad': _parsemad,
#     'max': _type1,
#     'min': _type1,
#     # # required because in vs_1_1 the mova instruction doesn't exist
#     'mov': lambda opcode, operands: _type1u(opcode, operands) if 'a0' not in operands[0] else _instr['mova'](['mova'], operands),
#     'mova': _type1u,
#     'mul': _type1,
#     'nop': lambda opcode, operands: [instr('nop')],
#     'nrm': lambda opcode, operands: _instr['dp4'](['dp4'], [operands[0], operands[1], operands[1]]) + _instr['rsq'](['rsq'], [operands[0], operands[0]]) + _instr['mul'](['mul'], [operands[0], operands[1], operands[0]]),
#     # # from Microsoft's documentation
#     'pow': lambda opcode, operands: _instr['abs'](['abs'], [operands[0], operands[1]]) + _instr['log'](['log'], [operands[0], operands[0]]) + _instr['mul'](['mul'], [operands[0], operands[2], operands[0]]) + _instr['exp'](['exp'], [operands[0], operands[0]]),
#     'rcp': _type1u,
#     # 'rep': lambda opcode, operands: [f'for {operands[0]}{inout.inctab_after()}\n'],
#     # 'ret': lambda opcode, operands: ['jmp'], # incomplete instruction, must be followed by a label
#     'rsq': _type1u,
#     # 'setp': _parsesetp,
#     'sge': _type1i,
#     # #TODO: use 4 instruction version in case of uniform instead of the autogenerated 5 using movs
#     'sgn': lambda opcode, operands: _instr['slt'](['slt'], [operands[2], _negate(operands[1]), operands[1]]) + _instr['slt'](['slt'], [operands[3], operands[1], _negate(operands[1])]) + _instr['sub'](['sub'], [operands[0], operands[2], operands[3]]),
#     'sincos': lambda opcode, operands: (_ for _ in ()).throw(Exception('sincos not supported')),
#     'slt': _type1i,
#     'sub': lambda opcode, operands: _instr['add'](['add'], [operands[0], operands[1], _negate(operands[2])]),
#     'texldl': lambda opcode, operands: (_ for _ in ()).throw(Exception('texldl not supported')),
# }