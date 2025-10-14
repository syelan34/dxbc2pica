from enum import Enum

class register:
    n: int = 0
    negative: bool = False
    name: str = ''
    swizzle: str | None = None
    tobereplaced: int = 0 # marks as needing to be replaced with free register
    def __init__(self, reg: str):
        if self.name == 'p0': self.name = 'cmp'
        if len(reg) > 0:
            splitreg = reg.split('.')
            self.negative = (splitreg[0][0] == '-')
            self.name = splitreg[0][self.negative:]
            self.swizzle = splitreg[1] if len(splitreg) == 2 else None
        self.tobereplaced = 0
    def __eq__(self, other) -> bool:
        return self.name == other.name and self.swizzle == other.swizzle and self.negative == other.negative
    def __str__(self):
        return f'register(negative: {self.negative}, name: {self.name}, swizzle: {self.swizzle}, tobereplaced: {self.tobereplaced})'
    def as_line(self):
        return ('-' * self.negative) + (f'{self.name}.{self.swizzle}' if self.swizzle else self.name) + (f' <to be replaced: {self.tobereplaced}>' if self.tobereplaced != 0 else '')
    def negate(self):
        self.negative = not self.negative
        return self
    def mark_to_be_replaced(self):
        register.n += 1
        self.tobereplaced = register.n
        return self
    def setswizzle(self, swizzle):
        self.swizzle = swizzle
        return self
    def is_output(self):
        return self.name[0] == 'o'
    def is_constant(self):
        return self.name[0] == 'c' and self.name is not 'cmp'
    def is_scratch(self):
        return self.name[0] == 'r'
    def is_bool(self):
        return self.name[0] == 'b'
    def is_int(self):
        return self.name[0] == 'i'
    def is_addressing(self):
        return self.name[0] == 'a'
        
class instr:
    opcode: str
    operands: list[register]
    def __init__(self, opcode: str, operands: list[register] = []):
        self.opcode = opcode
        self.operands = operands
    def __str__(self):
        return f'instr(opcode: {self.opcode}, dest: {self.operands[0] if len(self.operands) > 0 else '<>'}, operands: {[str(reg) for reg in self.operands[1:]]})'
    def as_line(self) -> str:
        return f'{self.opcode} {','.join([operand.as_line() for operand in self.operands])}'
    def dest(self) -> register:
        return self.operands[0] if len(self.operands) > 0 else register('')

class uniftype(Enum):
    FLOAT_UNIF = 'c'
    INT_UNIF = 'i'
    BOOL_UNIF = 'b'

class shadertype(Enum):
    VERTEX_SHADER = 0
    GEOMETRY_SHADER = 1
   
 
class shaderoutputs:
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