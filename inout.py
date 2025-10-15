import sys
import argparse

output = sys.stdout

def get_input() -> tuple[bool, list[str], str]:
    global output
    _test: bool = False
    _filter: list[str] = []
    parser = argparse.ArgumentParser(description='Converts DirectX DXBC to PICA200 assembly')
    parser.add_argument('-t','--test', action='store_true', help='Run tests')
    parser.add_argument('-f','--filter', type=str, help='Filter test outputs', nargs='*', default=None)
    parser.add_argument('-i','--input', type=str, help='Input file')
    parser.add_argument('-o','--output', type=str, help='Output file')
    args = parser.parse_args()
    
    if args.test: return (True, args.filter, "testing")
    # set input to either stdin or input file depending on what was passed
    if args.input is not None:
        sys.stdin = open(args.input, 'r')
    
    # set output to either stdout or output file depending on what was passed
    if args.output is not None:
        output = open(args.output, 'w')
    return (False, [], args.input if args.input is not None else "<stdin>")


def printline(line: str | list[str] = ''):
    global output
    if isinstance(line, str): print(line.lstrip(), file=output)
    elif isinstance(line, list): [print(str(l).lstrip(), file=output) for l in line]
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

comment = lambda comment = '': '\n'.join(['; ' + line for line in comment.split('\n')])