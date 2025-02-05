import sys
import argparse

def get_input() -> tuple[bool, list[str]]:
    _test: bool = False
    _filter: list[str] = []
    parser = argparse.ArgumentParser(description='Converts DirectX DXBC to PICA200 assembly')
    parser.add_argument('-t','--test', action='store_true', help='Run tests')
    parser.add_argument('-f','--filter', type=str, help='Filter test outputs', nargs='*', default=None)
    parser.add_argument('-i','--input', type=str, help='Input file')
    parser.add_argument('-o','--output', type=str, help='Output file')
    args = parser.parse_args()
    _test = args.test
    _filter = args.filter
    if args.test: return (_test, _filter)
    # set input to either stdin or input file depending on what was passed
    if args.input is not None:
        sys.stdin = open(args.input, 'r')
    
    # set output to either stdout or output file depending on what was passed
    if args.output is not None:
        sys.stdout = open(args.output, 'w')
    return (False, [])

_realntabs = 0
_inctabafterflag = False
_ignoretabs = False
def printline(line):
    global _realntabs
    global _inctabafterflag
    global _ignoretabs
    ntabs = _realntabs
    if _ignoretabs:
        ntabs = 0
        _ignoretabs = False
    if isinstance(line, str): sys.stdout.write('\t' * ntabs + line.lstrip())
    elif isinstance(line, list) and isinstance(line[0], str): [sys.stdout.write('\t' * ntabs + l.lstrip()) for l in line]
    if _inctabafterflag:
        _realntabs += 1
        _inctabafterflag = False
    return ''
    
def settab(ntabs):
    global _realntabs
    _realntabs = ntabs
    return ''

def inctab():
    global _realntabs
    _realntabs += 1
    return ''

def inctab_after():
    global _inctabafterflag
    _inctabafterflag = True
    return ''
    
def dectab():
    global _realntabs
    _realntabs -= 1
    return ''

def ignoretab():
    global _ignoretab
    _ignoretab = True
    return ''