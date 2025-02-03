import sys

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