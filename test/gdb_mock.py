import sys
import unittest.mock

import numpy as np


class GdbMock:
    """Mock gdb and gdb_arrays modules by replacing them in sys.modules"""
    def __init__(self, random=False):
        self.vars = {}
        self.random = random

        class Dummy:
            def __init__(self, *args, **kwargs):
                pass

        MockGDB = unittest.mock.Mock()
        MockGDB.Command = Dummy

        class MockGDBArray:
            @staticmethod
            def gdb_array_eval(name, start=0, stop=None, step=1):
                try:
                    return self.gdb_array_eval(name, start, stop, step)
                except KeyError:
                    if self.random:
                        return np.random.rand(len(range(start, stop, step)))
                    else:
                        raise

        # we have to match the names imported in cmd_grammar.py:parse_variable()
        # so that a call to gdb_array_eval will be replaced by our mock
        sys.modules['gdb'] = MockGDB
        sys.modules['gdb_arrays'] = MockGDBArray
        sys.modules['gdb_plot.gdb_arrays'] = MockGDBArray

    def gdb_array_eval(self, name, start=0, stop=None, step=1):
        arr = np.array(self.vars[name])
        try:
            stop = len(arr) if stop is None else stop
            return arr[start:stop:step]
        except TypeError:  # len() of unsized object
            return arr


gdb_mock = GdbMock()
