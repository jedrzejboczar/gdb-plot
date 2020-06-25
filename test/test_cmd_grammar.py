import unittest

from test.gdb_mock import gdb_mock
from gdb_plot.cmd_grammar import command, variable


class TestPlotCmd(unittest.TestCase):
    def setUp(self):
        gdb_mock.vars = {
            'x1': 1,
            'x2': 2,
            'x3': 3,
            'a1': [1, 3, 5],
            'a2': [4, 3, 2],
            'a3': [8, 6, 4, 2, 0],
        }

    def test_var_no_range(self):
        for v in ['x1', 'x2', 'x3']:
            self.assertEqual(variable.parseString(v)[0], gdb_mock.vars[v])
        for v in ['a1', 'a2']:
            self.assertListEqual(list(variable.parseString(v)[0]), gdb_mock.vars[v])

    def test_var_range(self):
        def check(s, v):
            self.assertListEqual(list(variable.parseString(s)[0]), v)
        check('a1@2', [1, 3])
        check('a1@1:3', [3, 5])
        check('a1@0:3:2', [1, 5])

    def test_var_nontrivial_range(self):
        def check(s, v):
            self.assertListEqual(list(variable.parseString(s)[0]), v)
        a3 = gdb_mock.vars['a3']
        check('a3@0:5', a3)
        check('a3@4:0:-1', a3[4:0:-1])
        check('a3@5:0:-1', a3[5:0:-1])
        check('a3@4:0:-2', a3[4:0:-2])
        check('a3@:3', a3[:3])
        check('a3@::2', a3[::2])
        check('a3@::-1', a3[::-1])
        check('a3@2::-1', a3[2::-1])


if __name__ == "__main__":
    mock_gdb()
    command.runTests('''
var1@5 "that's variable 1" var1@2 + 3 !c orange
!dt 0.01 var1@3 * 2 "this" var1@2 + 3 !c orange !m .
!fs 1000 var1@3 * 2 "this" var1@2 + 3 !c orange !m .
!fs 1000 sin(var1@3 * 2 ** 2) + 1 'weird construct' !c red var1@2 + 3 !c orange !m .
    ''')
