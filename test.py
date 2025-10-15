import parser
import os
import pathlib
import sys
import colorama
colorama.init()

from shtypes import *


def runtests(filter: list[str] | None):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    failedtests = []
    for version in os.listdir(f'{dir_path}/test/corpus'):
        for file in os.listdir(f'{dir_path}/test/corpus/{version}'):
            with open(f'{dir_path}/test/corpus/{version}/{file}', 'r') as f:
                results = testfilewithversion(f, version)
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
            [print(f'\t{line.as_line()}') for line in ft.result.correct]
            [print(f'\t{colorama.Fore.RED}{line.as_line()}{colorama.Style.RESET_ALL}') for line in ft.result.failed]
            [print(f'\t{colorama.Fore.GREEN}{line.as_line()}{colorama.Style.RESET_ALL}') for line in ft.result.expected]
            print()
    sys.exit(0)

class _testresult:
    passed: bool
    correct: list[instr]
    failed: list[instr]
    expected: list[instr]
    def __str__(self):
        return f'Passed: {self.passed}\n'

class _test:
    name: str = ''
    input: list[str] = []
    expected: list[instr] = []
    result: _testresult
    def __str__(self):
        return f'Name: {self.name}\nInput: {'\n'.join(self.input)}\nExpected: {'\n'.join([instr.as_line() for instr in self.expected])}\nResult: {self.result}'

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
        t.input = [line.strip() for line in filecontents[0:_findlineidxofrepeatedchar(filecontents, '-')] if line.strip()]
        filecontents = filecontents[_findlineidxofrepeatedchar(filecontents, '-'):]
        testendidx = _findlineidxofrepeatedchar(filecontents, '=')
        if testendidx == -1: # end of file
            testendidx = len(filecontents)
        t.expected = [parser.toinstr(line.strip()) for line in filecontents[1:testendidx] if line.strip()]
        filecontents = filecontents[testendidx:]
        
        tests.append(t)
    
    return tests

def _flatten(l: list[str | list[str]]):
    flat_list = []
    for row in l:
        if isinstance(row, str): flat_list.append(row)
        else: flat_list.extend(row)
    return flat_list

def testfilewithversion(f, version: str) -> list[_test]:
    tests = _splitfileintotests(f)
    for t in tests:
        t.result = getresultwithversion(t, version)
    return tests
    
def getresultwithversion(t, version) -> _testresult:
    result = _testresult()
    
    result.passed = True
    result.correct = t.input
    
    parsedshader = parser.parseshader(t.input, version)
    # remove the start and end procedure stuff since we aren't doing a whole shader we just want to test shaders
    parsedshader.body = parsedshader.body[2:len(parsedshader.body)-2]
    
    for i, instruction in enumerate(parsedshader.body):
        if i >= len(t.expected) or instruction != t.expected[i]:
            result.passed = False
            result.correct = parsedshader.body[:i]
            result.failed = parsedshader.body[i:]
            result.expected = t.expected[i:]
            return result
    
    # for i, line in enumerate(t.input):
    #     outlen = len(parser.parse(line))
    #     expectedlines = expected[linenum:linenum+outlen]
    #     gotlines = [instr.as_line() for instr in parsedshader.body[linenum:linenum+outlen]]
    #     for i, line in enumerate(expectedlines):
    #         if line != gotlines[i]:
    #             result.passed = False
    #             result.correct = parsedshader.body[:linenum+i]
    #             result.failed = gotlines[i:]
    #             result.expected = expectedlines[i:]
    #             return result
    #     linenum += outlen
    return result