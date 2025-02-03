import lineparser
import os
import pathlib
import sys
import colorama
colorama.init()

class _testresult:
    passed: bool
    correct: list[str]
    failed: str | list[str]
    expected: str | list[str]
class _test:
    name: str = ''
    input: list[str] = []
    expected: list[str] = []
    result: _testresult
    def __str__(self):
        return f'Name: {self.name}\nInput: {self.input}\nExpected: {self.expected}'
def _findlineidxofrepeatedchar(lines: list[str], char: str) -> int:
    for i, line in enumerate(lines):
        if line.strip() == '': continue
        ret = True
        for c in line.strip():
            if c != char:
                ret = False
                break
        if ret: return i
    return -1
def _splitfileintotests(f) -> list[_test]:
    filecontents: list[str] = f.readlines()
    tests = []
    while (i := _findlineidxofrepeatedchar(filecontents, '=')) != -1:
        filecontents = filecontents[i:] # remove everything before this test
        t = _test()
        
        t.name = filecontents[1].strip()
        filecontents = filecontents[3:]
        t.input = [line.strip() for line in filecontents[0:_findlineidxofrepeatedchar(filecontents, '-')]]
        filecontents = filecontents[_findlineidxofrepeatedchar(filecontents, '-'):]
        testendidx = _findlineidxofrepeatedchar(filecontents, '=')
        if testendidx == -1: # end of file
            testendidx = len(filecontents)
        t.expected = [line.strip() for line in filecontents[1:testendidx]]
        filecontents = filecontents[testendidx:]
        
        tests.append(t)
    
    return tests
    
def _flatten(l: list[str | list[str]]):
        flat_list = []
        for row in l:
            if isinstance(row, str): flat_list.append(row)
            else: flat_list.extend(row)
        return flat_list
        
def _parsetestinputwithbetterformatting(t):
    return [x for x in [''.join(_flatten([lineparser.parse(line) for line in t.input])).split('\n')][0] if x]
def _testfile(f) -> list[_test]:
    tests = _splitfileintotests(f)
    for t in tests:
        result = _testresult()
        result.passed = True
        result.correct = t.input
        parseddata = _parsetestinputwithbetterformatting(t)
        linenum = 0
        expected = list(filter(None,t.expected))
        for i, line in enumerate(t.input):
            outlen = len(lineparser.parse(line))
            expectedlines = expected[linenum:linenum+outlen]
            gotlines = parseddata[linenum:linenum+outlen]
            if expectedlines != gotlines:
                result.passed = False
                result.correct = t.input[:linenum]
                result.failed = gotlines
                result.expected = expectedlines
                break
            linenum += outlen
        t.result = result
    return tests
    
def runtests(filter: list[str] | None):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    failedtests = []
    for file in os.listdir(f'{dir_path}/test/corpus'):
        with open(f'{dir_path}/test/corpus/{file}', 'r') as f:
            results = _testfile(f)
            filtermatched = False
            for t in results:
                if filter:
                    if t.name not in filter:
                        continue
                filtermatched = True
            if filtermatched: 
                print(f'{pathlib.Path(f.name).stem}:')
                for t in [r for r in results if not filter or r.name in filter]:
                    if t.result.passed:
                        print('\t✓ ' + colorama.Fore.GREEN + t.name + colorama.Style.RESET_ALL)
                    else:
                        print('\t✗ ' + colorama.Fore.RED + t.name + colorama.Style.RESET_ALL)
                        failedtests.append(t)
    print()
    if failedtests:
        print(f'{len(failedtests)} failure{'' if len(failedtests) == 1 else 's'}:')
        print()
        print(f'correct / {colorama.Fore.GREEN}expected{colorama.Style.RESET_ALL} / {colorama.Fore.RED}unexpected{colorama.Style.RESET_ALL}')
        for i, ft in enumerate(failedtests):
            print()
            print(f'{i+1}. {ft.name}:')
            [print(f'\t{line}') for line in ft.result.correct]
            [print(f'\t{colorama.Fore.RED}{line}{colorama.Style.RESET_ALL}') for line in ft.result.failed]
            [print(f'\t{colorama.Fore.GREEN}{line}{colorama.Style.RESET_ALL}') for line in ft.result.expected] if isinstance(ft.result.expected, list) else [print(colorama.Fore.GREEN + f'\t{ft.result.expected}' + colorama.Style.RESET_ALL)]
            print()
    sys.exit(0)