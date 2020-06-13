import sys
import unittest
import unittest.mock

import numpy as np

from gdb_plot.cmd_grammar import command, variable


def _mock_gdb(gdb_array_eval_handler=None):
    """Mock gdb and gdb_arrays modules by replacing them in sys.modules"""

    class MockGDB:
        error = Exception
        Value = unittest.mock.Mock()

    class MockGDBArray:
        @staticmethod
        def gdb_array_eval(name, start=0, stop=None, step=1):
            return np.random.rand(len(range(start, stop, step)))

    if gdb_array_eval_handler:
        MockGDBArray.gdb_array_eval = gdb_array_eval_handler

    # we have to match the names imported in cmd_grammar.py:parse_variable()
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
