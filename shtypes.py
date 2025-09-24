from enum import Enum

class register:
    name: str
    swizzle: str | None
    def __init__(self, reg: str):
        splitreg = reg.split('.')
        self.name = splitreg[0]
        self.swizzle = splitreg[1] if len(splitreg) == 2 else None
    def __str__(self):
        return f'register(name: {self.name}, swizzle: {self.swizzle})'
    def as_line(self):
        return f'{self.name}.{self.swizzle}' if self.swizzle else self.name
    def __eq__(self, other) -> bool:
        return self.name == other.name and self.swizzle == other.swizzle
        
class instr:
    opcode: str
    operands: list[register]
    def __init__(self, opcode, operands = []):
        self.opcode = opcode
        self.operands = [register(operand) for operand in operands]
    def __str__(self):
        return f'instr(opcode: {self.opcode}, dest: {self.operands[0]}, operands: {[str(reg) for reg in self.operands[1:]]})'
    def as_line(self) -> str:
        return f'{self.opcode} {','.join([operand.as_line() for operand in self.operands])}'
    def dest(self) -> register:
        return self.operands[0]

class uniftype(Enum):
    FLOAT_UNIF = 'c'
    INT_UNIF = 'i'
    BOOL_UNIF = 'b'

class shadertype(Enum):
    VERTEX_SHADER = 0
    GEOMETRY_SHADER = 1
   
 
class shaderoutputs:
    position: str = ""
    color: str = ""
    texcoord0: str = ""
    texcoord1: str = ""
    texcoord2: str = ""
    def as_instr(self) -> list[str]:
        return [f'.out {val} {key}' for (key, val) in vars(self).items()]
    def __str__(self) -> str:
        attribs = [a for a in dir(self) if not 'str' in a and not a.startswith('__')]
        return f"{*[f"{attrib}: {getattr(self, attrib)}" if getattr(self, attrib) else f"{attrib}: unused" for attrib in attribs],}";

class uniform:
    type: uniftype = uniftype.FLOAT_UNIF
    id: int = 0
    size: int = 0
    name: str = ""
    def as_instr(self): return f'.{self.type.value if self.type.value != 'c' else 'f'}vec {self.name}{f'[{self.size}]' if self.size > 1 else ''} ; {self.type.value}{self.id}'
    def __str__(self): return f'uniform(type: {self.type}, id: {self.id}, size: {self.size}, name: {self.name})'

class constantunif:
    type: uniftype = uniftype.FLOAT_UNIF
    id: int = 0
    values: list
    def as_instr(self) -> str:
        return f".const{'f' if self.type.value == 'c' else self.type.value} {self.type.value}{self.id}{*[float(v) for v in self.values],}";
    def __str__(self) -> str:
        return f'constant(type:{self.type},id:{self.id},value:{self.values})'

class shader_header:
    version: str = ""
    type: shadertype = shadertype.VERTEX_SHADER
    uniforms: list[uniform] = []
    inputs: list[str] = []
    outputs: shaderoutputs = shaderoutputs()
    constants: list[constantunif] = []
    def __str__(self): 
        unifstrings = [str(unif) for unif in self.uniforms]
        conststrings = [str(unif) for unif in self.constants]
        return f'shader_header(type:{self.type},version:{self.version},uniforms:{*unifstrings,},inputs:{*self.inputs,},outputs:{self.outputs},constants:{*conststrings,})'

class shader:
    header: shader_header = shader_header()
    setup: list[str] = []
    body: list[instr] = []
    def __str__(self):
        return f'shader(header:{self.header},setup:{self.setup},body:{[str(instr) for instr in self.body]})'