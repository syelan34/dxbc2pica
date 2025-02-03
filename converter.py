import sys
import argparse
import lineparser
import test
import output

_test: bool = False
_filter: list[str] | None = None

def get_input():
    global _test
    global _filter
    parser = argparse.ArgumentParser(description='Converts DirectX DXBC to PICA200 assembly')
    parser.add_argument('-t','--test', action='store_true', help='Run tests')
    parser.add_argument('-f','--filter', type=str, help='Filter test outputs', nargs='*', default=None)
    parser.add_argument('-i','--input', type=str, help='Input file')
    parser.add_argument('-o','--output', type=str, help='Output file')
    args = parser.parse_args()
    # print(args)
    _test = args.test
    _filter = args.filter
    # set input to either stdin or input file depending on what was passed
    if args.input is not None:
        sys.stdin = open(args.input, 'r')
    
    # set output to either stdout or output file depending on what was passed
    if args.output is not None:
        sys.stdout = open(args.output, 'w')

if __name__ == '__main__':
    get_input()
    if _test:
        test.runtests(_filter)
        exit(0)
    
    output.printline('.proc main\n')
    output.inctab()
    for line in sys.stdin:
        output.printline(lineparser.parse(line))
    output.printline('end\n')
    output.dectab()
    output.printline('.end\n')