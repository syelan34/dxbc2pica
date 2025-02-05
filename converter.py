import sys
import lineparser
import test
import inout

if __name__ == '__main__':
    # future steps:
    # - get input
    # - scan for meta info [todo]
    # - add meta info stuff [todo]
    # - go through instructions line by line
    t, filter = inout.get_input()
    if t:
        test.runtests(filter)
        exit(0)
    
    inout.printline('.proc main\n')
    inout.inctab()
    for line in sys.stdin:
        inout.printline(lineparser.parse(line))
    inout.printline('end\n')
    inout.dectab()
    inout.printline('.end\n')