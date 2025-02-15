from typing import Callable

def createbinary(lines: list[str]):
    constants = []
    
    pass


def _format1(opcode, operands):
    return 0
    
_bin: dict[str, Callable[[list[str], list[str]], int]] = {
    'mov': _format1
}

def _splitoperand(operand) -> tuple[bool, str, int, str]:
    return ('-' in operand, operand[1] if '-' in operand else operand[0], _getdigits(operand), operand.split('.')[1])

def _opcode(opcodestr) -> int:
    # from 3dbrew.org
    opcodes = [
        'add', 'dp3', 'dp4', 'dph', 'dst', 'ex2', 'lg2', 'litp', 'mul', 'sge', 'slt', 'flr', 'max', 'min',
        'rcp', 'rsq', '???', '???', 'mova', 'mov', '???', '???', '???', '???', 'dphi', 'dsti', 'sgei', 'slti',
        '???', '???', '???', '???', 'break', 'nop', 'end', 'breakc', 'call', 'callc', 'callu', 'ifu', 'ifc', 
        ''
    ]
    return opcodes.index(opcodestr)

def _getdigits(input: str) -> int:
    return int(''.join(ch for ch in input if ch.isdigit()))
    
    
# typedef struct {
#     u16 type; //  Constant type.
#     u16 ID;   // Constant ID.
#     union {
#         u32 boolUniform; // Bool uniform value.
#         u32 intUniform;  // Int uniform value.
#         struct {
#             u32 x; // Float24 uniform X component.
#             u32 y; // Float24 uniform Y component.
#             u32 z; // Float24 uniform Z component.
#             u32 w; // Float24 uniform W component.
#         } floatUniform;
#     } data;
# } DVLEConstEntry;
class constantentry:
    type: int # 0 = bool, 1 = ivec4, 2 = fvec4
    id: int
    def __int__(self):
        return self.type << 8
class outputentry:
    
    