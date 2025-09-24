from os import supports_fd
import sys
import parser
import test
import inout

supported_shader_models = [
    'vs_1_1', 'vs_2_0', 'vs_2_x', 'vs_2_sw', 'vs_3_0', 'vs_3_sw'#, "vs_4_0" # will eventually add vs_4_0 and gs_4_0 for geometry shader support
]

if __name__ == '__main__':
    # future steps:
    # - get input
    # - scan for meta info [todo]
    # - add meta info stuff [todo]
    # - go through instructions line by line
    t, filter, inputfilename = inout.get_input()
    if t:
        test.runtests(filter)
        exit(0)
        
    lines = [line for line in sys.stdin]
    # get header portion
    # this is all of the lines starting with '//' until the first one that doesn't
    shaderheader = [line[3:].strip() for line in lines[:[lines.index(l) for l in lines if not l.startswith('//') and not l.isspace()][0]] if not (line[3:].isspace() or len(line[3:]) < 1)]
    
    # get shader body
    shaderbody = [line.strip() for line in lines if not line.startswith('//') and not line.isspace()]
    
    if len(shaderheader) < 1: raise Exception(f"No header in shader {inputfilename}")
    if len(shaderbody) < 1: raise Exception(f"No body in shader {inputfilename}")
    
    # check version
    version = shaderbody[0]
    if version not in supported_shader_models: raise Exception(f"Unsupported shader model {version} (expected one of {*supported_shader_models,})")
    
    # parse header to get uniform info
    # header = parser.parseheader(shaderheader, version)
    shader = parser.parseshader(lines, version)
    
    #TODO fix multiple writes to output issue here
    
    # output shader
    print(shader)
    parser.outputshader(shader)
    
    # inout.printline('.proc main\n')
    # inout.inctab()
    # for line in shaderbody:
    #     inout.printline(lineparser.parse(line))
    # inout.printline('end\n')
    # inout.dectab()
    # inout.printline('.end\n')