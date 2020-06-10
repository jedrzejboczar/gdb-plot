import operator
from functools import reduce

try:
    import gdb
    _gdb = True
except ImportError:
    print('WARNING: could not import gdb: %s' % __file__)
    _gdb = False

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

import expression

### GDB introspection ##########################################################

def gdb_type_code_str(code):
    """Map GDB type code to its name"""
    code_map = {getattr(gdb, c): c for c in dir(gdb) if c.startswith('TYPE_CODE')}
    return code_map[code]

def is_complex(value):
    return value.type.code == gdb.TYPE_CODE_STRUCT and \
        value.type.fields()[0].name == '_M_value' and \
        value.type.fields()[0].type.strip_typedefs().code == gdb.TYPE_CODE_COMLEX

def parse_complex(value):
    """Convert complex gdb.Value to Python complex value"""
    # example "0.25 + -0.33 * I"
    real, imag = str(value).split('+')
    imag = imag.split('*')
    return float(real) + float(imag) * 1j

def parse_simple(value):
    """Parse either a simple number (float/int) or a complex value (std::complex)"""
    return float(value) if not is_complex(value) else parse_complex(value)

def gdb_array_eval(name: str, start: int = 0, stop: int = None, step: int = 1):
    """Retrieve data from GDB varable into numpy array

    Supports arrays, raw pointers (unknown length) and some special types:
    * std::vector
    * Eigen::Array
    * Boost::Numerics::...
    """
    value = gdb.parse_and_eval(name)
    base_type = value.type.strip_typedefs()
    code = base_type.code

    if code in [gdb.TYPE_CODE_INT, gdb.TYPE_CODE_FLT]:
        return np.array([parse_simple(value)])
    if code == gdb.TYPE_CODE_ARRAY:
        _lower, upper = base_type.range()
        if stop is None:
            stop = upper
        values = [parse_simple(value[i]) for i in range(start, min(stop, upper), step)]
        return np.array(values)
    if code == gdb.TYPE_CODE_PTR:
        assert stop is not None, 'Unknown length of raw pointer type: %s' % value.type
        values = [parse_simple(value[i]) for i in range(start, stop, step)]
        return np.array(values)
    if code == gdb.TYPE_CODE_STRUCT:
        if 'boost' in base_type:
            raise NotImplementedError('boost')
            #  return parse_boost(value, length)
        elif 'std::vector' in base_type:
            raise NotImplementedError('std::vector')
            #  return parse_stl_vector(value, length)
        elif 'Eigen::Array' in base_type:
            raise NotImplementedError('Eigen::Array')
            #  return parse_stl_vector(value, length)
    raise NotImplementedError('value.type = {}, .code = {}'.format(
        value.type, gdb_type_code_str(code)))

#  def parse_boost(value, length=None):

### Grammar ####################################################################

_int = expression.integer
vrange = Combine(Optional(_int('start') + ':') + _int('stop') + Optional(':' + _int('step')))
varname = Word(alphas + '_', alphanums + '_')
variable = Combine(varname('name') + Optional(Combine('@' + vrange)))

def parse_variable(tokens):
    try:
        kwargs = {}
        if tokens.start: kwargs['start'] = tokens.start
        if tokens.stop: kwargs['stop'] = tokens.stop
        if tokens.step: kwargs['step'] = tokens.step
        return gdb_array_eval(tokens.name, **kwargs)
    except gdb.error:
        if tokens.stop:
            raise RuntimeError('constant with @range: %s' % tokens)
        return expression.constants[tokens.name]

def _fake_parse_variable(tokens):
    if tokens.stop:
        return np.random.rand(len(range(tokens.start or 0, tokens.stop, tokens.step or 1)))
    else:
        return np.array([np.random.rand()])

if _gdb:
    variable.setParseAction(parse_variable)
else:
    variable.setParseAction(_fake_parse_variable)

expr = expression.construct_grammar(variable)

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
    elif tokens[0].lower == 'False':
        return False
    return bool(tokens[0])

boolean.addParseAction(parse_boolean)

def param(keyword, name, word):
    return '!' + Keyword(keyword) + word(name)

# global
dt = param('dt', 'dt', expression.real)
fs = param('fs', 'fs', expression.real)
t0 = param('t0', 't0', expression.real)
grid = param('g', 'grid', boolean)
legend = param('l', 'legend', boolean)
axis_equal = param('eq', 'axis_equal', Optional(boolean, default=True))
global_params = Optional(dt ^ fs) & Optional(t0, default=0) & Optional(grid) \
    & Optional(legend) & Optional(axis_equal)

_local_param_defs = {
    'color':      ('c',  Word(alphanums)),
    'marker':     ('m',  Word(printables)),
    'linestyle':  ('l',  Word(alphas)),
    'linewidth':  ('lw', expression.real),
    'markersize': ('ms', expression.real),
    'fmt':        ('f',  Word(printables)),
}
_local_params = [Optional(param(keyword, name, word))
                 for name, (keyword, word) in _local_param_defs.items()]
local_params = reduce(operator.and_, _local_params)

record = Group(expr('expr') + Optional(string('label')) + local_params)('record')
command = StringStart() + global_params + Group(OneOrMore(record))('records') + StringEnd()


if __name__ == "__main__":
    command.runTests('''
var1@5 "that's variable 1" var1@2 + 3 !c orange
!dt 0.01 var1@3 * 2 "this" var1@2 + 3 !c orange !m .
!fs 1000 var1@3 * 2 "this" var1@2 + 3 !c orange !m .
!fs 1000 sin(var1@3 * 2 ** 2) + 1 'weird construct' !c red var1@2 + 3 !c orange !m .
    ''')
