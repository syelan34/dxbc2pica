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
    if numinstructions == 0:
        ops = shader.body[index].operands
        read = [r for r in ops[1:] if not r.tobereplaced]
        for i in range(16):
            if f'r{i}' not in [r.name for r in read]:
                return register(f"r{i}")
    
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
    for (index, instruction) in enumerate(input.body):
        # replace marked registers
        for (opid, reg) in enumerate(instruction.operands):
            if reg.tobereplaced:
                freereg = findfreescratchreg(input, index)
                reg.tobereplaced = False
                reg.name = freereg.name
        
        # fix ret instructions (since they're kinda multi line instructions)
        if instruction.opcode[0] == 'ret':
            # if ret is followed by a label then that should be a jmp instruction instead
            # if not then it's an `end` instruction (plus a .end instruction) (not doing this rn because i'm not sure how to distinguish a normal label and a subroutine)
            if index+1 < len(input.body):
                nextinstr = input.body[index+1]
                if nextinstr.opcode[0] == 'label':
                    input.body[index] = instr(['jmp'], nextinstr.operands)
                    del input.body[index+1]
                else:
                    input.body[index] = instr(['end'])
            else:
                input.body[index] = instr(['end'])
                #     input.body.insert(index+1, instr(['.end']))
        # any remaining label instructions are defining processes
        if instruction.opcode[0] == 'label':
            input.body[index] = instr([f'{instruction.operands[0].as_line()}:'])

    # if there's no end instruction at the end of the shader then include it here
    # also, we're kinda pretending there's no subroutines since fxc doesn't seem to output them and so I don't really know what they look like
    # so i'm not actually using this yet
    # if sum([instr.opcode[0] == 'end' for instr in input.body]) < 1:
    #     input.body += [instr(['end']), instr(['.end'])]
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

def toinstr(line:str) -> instr:
    components = line.strip().split(' ')
    opcode = components[0].split("_")
    operands = [register(op.strip()) for op in ''.join(components[1:]).split(',')] if len(components) > 1 else []
    return instr(opcode, operands)