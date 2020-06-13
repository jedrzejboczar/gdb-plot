import math
import unittest

from pyparsing import MatchFirst, Keyword
from gdb_plot.math_grammar import construct_grammar, constants


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
    variable = MatchFirst([Keyword(c) for c in constants])
    variable.setParseAction(lambda tokens: constants[tokens[0]])
    expr = construct_grammar(variable)
    return expr

class TestGrammarMeta(type):
    def __new__(mcs, name, bases, attrs):
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

        return super(TestGrammarMeta, mcs).__new__(mcs, name, bases, attrs)

class TestGrammar(unittest.TestCase, metaclass=TestGrammarMeta):
    pass
