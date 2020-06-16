"""
Defines grammar for parsing plotting commands. Basing on arithemtics grammar,
extends it to support GDB variables with array indexing, and to add commands
for plotting.
"""

import operator
from functools import reduce

import numpy as np
from pyparsing import (
    alphanums,
    alphas,
    oneOf,
    printables,
    Combine,
    Empty,
    Group,
    Keyword,
    OneOrMore,
    Optional,
    QuotedString,
    StringEnd,
    StringStart,
    Word,
)

from gdb_plot import math_grammar

### Variable grammar ###########################################################

_int = math_grammar.integer
vrange_3 = Combine(Optional(_int('start')) + ':' + Optional(_int('stop')) + ':' + Optional(_int('step')))
vrange_2 = Combine(Optional(_int('start')) + ':' + Optional(_int('stop')))
vrange_1 = _int('stop')
vrange = vrange_3 | vrange_2 | vrange_1
varname = Word(alphas + '_', alphanums + '_')
variable = Combine(varname('name') + Optional(Combine('@' + vrange)))

def parse_variable(tokens):
    import gdb
    from gdb_plot.gdb_arrays import gdb_array_eval

    try:
        s = slice(
            tokens.start if tokens.start != '' else None,
            tokens.stop if tokens.stop != '' else None,
            tokens.step if tokens.step != '' else None
        )
        return gdb_array_eval(tokens.name, s)
    except gdb.error:
        if tokens.stop:
            raise RuntimeError('constant with @range: %s' % tokens)
        return math_grammar.constants[tokens.name]

def _fake_parse_variable(tokens):
    if tokens.stop:
        return np.random.rand(len(range(tokens.start or 0, tokens.stop, tokens.step or 1)))
    else:
        return np.array([np.random.rand()])

variable.setParseAction(parse_variable)

expr = math_grammar.construct_grammar(variable)

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
dt = param('dt', 'dt', math_grammar.real)
fs = param('fs', 'fs', math_grammar.real)
t0 = param('t0', 't0', math_grammar.real)
grid = param('g', 'grid', boolean)
legend = param('l', 'legend', boolean)
axis_equal = param('eq', 'axis_equal', Optional(boolean, default=True))
global_params = Optional(dt ^ fs) & Optional(t0, default=0) & Optional(grid) \
    & Optional(legend) & Optional(axis_equal)

_local_param_defs = {
    'color':      ('c',  Word(alphanums)),
    'marker':     ('m',  Word(printables)),
    'linestyle':  ('l',  Word(alphas)),
    'linewidth':  ('lw', math_grammar.real),
    'markersize': ('ms', math_grammar.real),
    'fmt':        ('f',  Word(printables)),
}
_local_params = [Optional(param(keyword, name, word))
                 for name, (keyword, word) in _local_param_defs.items()]
local_params = reduce(operator.and_, _local_params)

marker = Empty().setParseAction(lambda s, loc, t: loc)
marked_expr = marker('_start') + expr('expr') + marker('_end')
record = Group(marked_expr + Optional(string('label')) + local_params)('record')

def save_string(s, loc, tokens):
    tokens['string'] = s[tokens._start:tokens._end]

marked_expr.addParseAction(save_string)

command = StringStart() + global_params + Group(OneOrMore(record))('records') + StringEnd()
