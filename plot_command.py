"""
Defines grammar for parsing plotting commands. Basing on arithemtics grammar,
extends it to support GDB variables with array indexing, and to add commands
for plotting.
"""

import operator
import unittest
from functools import reduce

import numpy as np
from pyparsing import (
    alphanums,
    alphas,
    hexnums,
    infixNotation,
    printables,
    nums,
    oneOf,
    opAssoc,
    Combine,
    Forward,
    Keyword,
    MatchFirst,
    Optional,
    ParserElement,
    Regex,
    Suppress,
    Word,
    Literal,
    ZeroOrMore,
    Group,
    WordStart,
    WordEnd,
    LineStart,
    LineEnd,
    StringStart,
    StringEnd,
    QuotedString,
    OneOrMore,
)

import arithmetics

### Variable grammar ###########################################################

_int = arithmetics.integer
vrange = Combine(Optional(_int('start') + ':') + _int('stop') + Optional(':' + _int('step')))
varname = Word(alphas + '_', alphanums + '_')
variable = Combine(varname('name') + Optional(Combine('@' + vrange)))

def parse_variable(tokens):
    import gdb
    import gdb_arrays

    try:
        kwargs = {}
        if tokens.start:
            kwargs['start'] = tokens.start
        if tokens.stop:
            kwargs['stop'] = tokens.stop
        if tokens.step:
            kwargs['step'] = tokens.step
        return gdb_arrays.gdb_array_eval(tokens.name, **kwargs)
    except gdb.error:
        if tokens.stop:
            raise RuntimeError('constant with @range: %s' % tokens)
        return arithmetics.constants[tokens.name]

def _fake_parse_variable(tokens):
    if tokens.stop:
        return np.random.rand(len(range(tokens.start or 0, tokens.stop, tokens.step or 1)))
    else:
        return np.array([np.random.rand()])

variable.setParseAction(parse_variable)

expr = arithmetics.construct_grammar(variable)

### Command grammar ############################################################

# features?
# * do maths, e.g:      plot (var1@100 + 3 * 4) / 2
# * plot multiple:      plot var1@10 var2@1000
# * with time:          plot --dt 0.001 var1@10
# * with labels:        plot var1@100 "variable 1" var2@100 "variable 2"
# * color/markers:      plot var1@100 -c 'orange' -m '.-' var2@100 "variable 2" -c 'C1'
# * multiple axes:      plot --axes 2:1 var1@100 -c 'orange' -m '.-' var2@100 "variable 2" -c 'C1'
# * axis options:       plot --grid --aspect=equal var1@100

string = QuotedString("'") | QuotedString('"')  # | Word(alphanums)
boolean = oneOf('0 1 true false', caseless=True, asKeyword=True)

def parse_boolean(tokens):
    if tokens[0].lower == 'true':
        return True
    if tokens[0].lower == 'False':
        return False
    return bool(tokens[0])

boolean.addParseAction(parse_boolean)

def param(keyword, name, word):
    return '!' + Keyword(keyword) + word(name)

# global
dt = param('dt', 'dt', arithmetics.real)
fs = param('fs', 'fs', arithmetics.real)
t0 = param('t0', 't0', arithmetics.real)
grid = param('g', 'grid', boolean)
legend = param('l', 'legend', boolean)
axis_equal = param('eq', 'axis_equal', Optional(boolean, default=True))
global_params = Optional(dt ^ fs) & Optional(t0, default=0) & Optional(grid) \
    & Optional(legend) & Optional(axis_equal)

_local_param_defs = {
    'color':      ('c',  Word(alphanums)),
    'marker':     ('m',  Word(printables)),
    'linestyle':  ('l',  Word(alphas)),
    'linewidth':  ('lw', arithmetics.real),
    'markersize': ('ms', arithmetics.real),
    'fmt':        ('f',  Word(printables)),
}
_local_params = [Optional(param(keyword, name, word))
                 for name, (keyword, word) in _local_param_defs.items()]
local_params = reduce(operator.and_, _local_params)

record = Group(expr('expr') + Optional(string('label')) + local_params)('record')
command = StringStart() + global_params + Group(OneOrMore(record))('records') + StringEnd()

### Tests ######################################################################

def _mock_gdb(gdb_array_eval_handler=None):
    """Mock gdb and gdb_arrays modules by replacing them in sys.modules"""

    import sys

    class MockGDB:
        error = Exception

    class MockGDBArray:
        @staticmethod
        def gdb_array_eval(name, start=0, stop=None, step=1):
            return np.random.rand(len(range(start, stop, step)))

    if gdb_array_eval_handler:
        MockGDBArray.gdb_array_eval = gdb_array_eval_handler

    sys.modules['gdb'] = MockGDB
    sys.modules['gdb_arrays'] = MockGDBArray


class TestPlotCmd(unittest.TestCase):
    def gdb_array_eval(self, name, start=0, stop=None, step=1):
        arr = np.array(self.vars[name])
        try:
            stop = len(arr) if stop is None else stop
            return arr[start:stop:step]
        except TypeError:  # len() of unsized object
            return arr

    def setUp(self):
        # some useful defaults
        self.vars = {
            'x1': 1,
            'x2': 2,
            'x3': 3,
            'a1': [1, 3, 5],
            'a2': [4, 3, 2],
        }
        _mock_gdb(self.gdb_array_eval)

    def test_var_no_range(self):
        for v in ['x1', 'x2', 'x3']:
            self.assertEqual(variable.parseString(v)[0], self.vars[v])
        for v in ['a1', 'a2']:
            self.assertListEqual(list(variable.parseString(v)[0]), self.vars[v])

    def test_var_range(self):
        def check(s, v):
            self.assertListEqual(list(variable.parseString(s)[0]), v)
        check('a1@2', [1, 3])
        check('a1@1:3', [3, 5])
        check('a1@0:3:2', [1, 5])


if __name__ == "__main__":
    _mock_gdb()
    command.runTests('''
var1@5 "that's variable 1" var1@2 + 3 !c orange
!dt 0.01 var1@3 * 2 "this" var1@2 + 3 !c orange !m .
!fs 1000 var1@3 * 2 "this" var1@2 + 3 !c orange !m .
!fs 1000 sin(var1@3 * 2 ** 2) + 1 'weird construct' !c red var1@2 + 3 !c orange !m .
    ''')
