"""
Implements a grammar for parsing mathematical expressions with support for
complex numbers, operations on numpy arrays, some mathematical functions and arbitrary, user
variables (grammar and variable retrival are defined by the user).
"""

import numpy as np

from pyparsing import (
    hexnums,
    infixNotation,
    nums,
    oneOf,
    opAssoc,
    Combine,
    Forward,
    Keyword,
    MatchFirst,
    ParserElement,
    Regex,
    Suppress,
    Word,
)

# GREAT speedup by caching
ParserElement.enablePackrat()


def _eval_single(op_map):
    def handler(tokens):
        op, val = tokens[0]
        return op_map[op](val)
    return handler


def _eval_func(op_map):
    def handler(tokens):
        op = tokens[0]
        val = tokens[1]
        return op_map[op](val)
    return handler


def _grouped(iterable, n):
    "s -> (s0,s1,s2,...sn-1), (sn,sn+1,sn+2,...s2n-1), (s2n,s2n+1,s2n+2,...s3n-1), ..."
    return zip(*[iter(iterable)] * n)


def _eval_pair(op_map, reverse=False):
    def handler(tokens):
        vals = tokens[0]
        if reverse:
            vals = vals[::-1]
        res = vals[0]
        for op, val in _grouped(vals[1:], 2):
            if reverse:
                res = op_map[op](val, res)
            else:
                res = op_map[op](res, val)
        return res
    return handler


### Grammar ####################################################################

real = Regex(r"\d+(?:\.\d*)?(?:[eE][+-]?\d+)?")
decimal = Word(nums)
hexa = Combine('0x' + Word(hexnums))
binary = Combine('0b' + Word('0' + '1'))
imaginary = Combine(real + 'j')

real.setParseAction(lambda tokens: float(tokens[0]))
decimal.setParseAction(lambda tokens: int(tokens[0], 10))
hexa.setParseAction(lambda tokens: int(tokens[0], 16))
binary.setParseAction(lambda tokens: int(tokens[0], 2))
imaginary.setParseAction(lambda tokens: complex(tokens[0]))

integer = binary | hexa | decimal
number = binary | hexa | imaginary | real

fn_map = {
    'abs': np.abs,
    'sin': np.sin,
    'cos': np.cos,
    'tan': np.tan,
    'exp': np.exp,
    'sgn': np.sign,
    'real': np.real,
    'imag': np.imag,
    'sqrt': np.sqrt,
}

op1_map = {
    '+': lambda x: x,
    '-': np.negative,
    '~': np.bitwise_not,
}

op2_map = {
    '**': np.power,
    '*':  np.multiply,
    '/':  np.divide,
    '@':  np.matmul,
    '+':  np.add,
    '-':  np.subtract,
    '&':  np.bitwise_and,
    '|':  np.bitwise_or,
    '^':  np.bitwise_xor,
    '!=': np.not_equal,
    '==': np.equal,
    '<':  np.less,
    '<=': np.less_equal,
    '>':  np.greater,
    '>=': np.greater_equal,
}

def construct_grammar(variable):
    """Construct grammar with a given variable parser

    Implements a grammar for parsing mathematical expressions with support for
    operations on numpy arrays, some mathematical functions and arbitrary, user
    variable names resolved at runtime.  Variables syntax is defined by the
    `variable` parameter, which should use `setParseAction` to define the
    action that will evaluate the variable.
    """
    expr = Forward()
    func_call = Forward()

    expr_atom = func_call | variable | number
    expr <<= infixNotation(
        expr_atom,
        [
            ('**',                     2, opAssoc.LEFT,  _eval_pair(op2_map, reverse=True)),
            (oneOf('+ - ~'),           1, opAssoc.RIGHT, _eval_single(op1_map)),
            (oneOf('* /'),             2, opAssoc.LEFT,  _eval_pair(op2_map)),
            (oneOf('+ -'),             2, opAssoc.LEFT,  _eval_pair(op2_map)),
            ('&',                      2, opAssoc.LEFT,  _eval_pair(op2_map)),
            ('^',                      2, opAssoc.LEFT,  _eval_pair(op2_map)),
            ('|',                      2, opAssoc.LEFT,  _eval_pair(op2_map)),
            (oneOf('!= == < <= > >='), 2, opAssoc.LEFT,  _eval_pair(op2_map)),
        ]
    )

    func_ident = MatchFirst([Keyword(fn) for fn in fn_map.keys()])
    func_call <<= func_ident + Suppress('(') + expr + Suppress(')')
    func_call.setParseAction(_eval_func(fn_map))

    return expr

constants = {
    'pi': np.pi,
    'e': np.e,
}

### Tests ######################################################################

import math
import unittest

test_cases = [
    '3 + 5 + 2',
    '3 * 5 * 2',
    '3 ** 5 ** 2',
    '3 / 5 / 2',
    '3 - 5 / 2',
    '(3 - 5) / 2',
    '2 * (3 - 5)',
    '0b101 & 0b110',
    '0b101 | 0b110',
    '0b101 ^ 0b110',
    '0b101 ^ 0b110 & 0b100',
    '(0b101 ^ 0b110) & 0b100',
    '0b101 | 0b110 & 0b100',
    '(0b101 | 0b110) & 0b100',
    '2 * (3 + 4) - 2**(9 * 2) / 3**3 * 1.5',
    '2 > 2',
    '20 > 2',
    '2 <= 2',
    '20 <= 2',
    '20 == 2',
    '20 != 2',
    '2 == 2',
    '2 != 2',
    '2 < 2',
    '2 < 20',
    'sin((2 + 3) / 4)',
    'sin((2 + cos(3)) / cos(4)**2)',
    'sin(pi/2)**2 + cos(pi/2) ** 2',
    '(sin(pi/2)**2 + cos(pi/2) ** 2) == 1',
    'pi > 3.1415',
    'pi < 3.1416',
    'e > 2.7182',
    'e < 2.7183',
    '3 + 4j',
    '1j * 1j',
    'real(3 + 2j)',
    'imag(3 + 2j)',
]

def test_grammar():
    variable = MatchFirst([Keyword(c) for c in constants.keys()])
    variable.setParseAction(lambda tokens: constants[tokens[0]])
    expr = construct_grammar(variable)
    return expr

class TestGrammarMeta(type):
    def __new__(cls, name, bases, attrs):
        def _sanitize_name(s):
            for char in '':
                s = s.replace(char, '?')
            return s.replace(' ', '_')

        math_maps = {
            'sin': math.sin,
            'cos': math.cos,
            'pi': math.pi,
            'e': math.e,
            'real': lambda num: num.real,
            'imag': lambda num: num.imag,
        }

        expr = test_grammar()

        for case in test_cases:
            def handler(self, _case=case):
                res = expr.parseString(_case)[0]
                ref = eval(_case, math_maps)
                #  print('%s vs %s' % (res, ref))
                self.assertEqual(res, ref)

            handler.__name__ = 'test_{}'.format(_sanitize_name(case))
            attrs[handler.__name__] = handler

        return super(TestGrammarMeta, cls).__new__(cls, name, bases, attrs)

class TestGrammar(unittest.TestCase, metaclass=TestGrammarMeta):
    pass
