import unittest
from unittest import mock

import numpy as np

from test.gdb_mock import gdb_mock
from gdb_plot import plot


def _as_list(x):
    print('_as_list: %s' % x)
    try:
        return list(x)
    except TypeError:
        return [x]

@mock.patch('gdb_plot.plot.plt')
class TestPlot(unittest.TestCase):
    def setUp(self):
        gdb_mock.vars = {
            'x1': 1,
            'x2': 2,
            'x3': 3,
            'a1': [1, 3, 5, 7, 9],
            'a2': [4, 3, 2, 4, 8, 2, 0],
        }
        self.fig, self.axes = mock.Mock(), mock.Mock()
        self.subplots = mock.Mock(return_value=(self.fig, self.axes))

    def cmp_np(self, a, b, cmp=None, msg=None):
        # compare maybe-numpy-arrays as lists
        if cmp is None:
            cmp = self.assertListEqual
        np.testing.assert_array_equal(list(a), list(b), err_msg=msg)
        #  cmp(list(a), list(b), msg=msg)

    def cmp_calls(self, calls, calls_ref):
        for call, call_ref in zip(calls, calls_ref):
            for argi in range(len(call_ref.args)):
                self.cmp_np(call.args[argi], call_ref.args[argi], msg='args[%d]' % argi)
            self.assertDictEqual(call.kwargs, call_ref.kwargs)

    def test_single(self, mock_plt):
        mock_plt.subplots = self.subplots

        p = plot.Plot()
        p.invoke('a1', from_tty=False)

        self.subplots.assert_called_once()
        self.axes.plot.assert_called_once()
        self.cmp_np(self.axes.plot.call_args.args[0], [0, 1, 2, 3, 4], msg='t')
        self.cmp_np(self.axes.plot.call_args.args[1], [1, 3, 5, 7, 9], msg='a1')
        self.assertEqual(self.axes.plot.call_args.kwargs, {'label': 'a1'})

    def test_multiple(self, mock_plt):
        mock_plt.subplots = self.subplots

        p = plot.Plot()
        p.invoke('a1 a2@5', from_tty=False)

        calls_ref = [
            mock.call([0, 1, 2, 3, 4], [1, 3, 5, 7, 9], label='a1'),
            mock.call([0, 1, 2, 3, 4], [4, 3, 2, 4, 8], label='a2@5'),
        ]

        self.subplots.assert_called_once()
        self.cmp_calls(self.axes.plot.call_args_list, calls_ref)

    def test_kwargs(self, mock_plt):
        mock_plt.subplots = self.subplots

        p = plot.Plot()
        p.invoke('a1 !c red !m o !lw 3 !l dashed !ms 5', from_tty=False)

        calls_ref = [
            mock.call([0, 1, 2, 3, 4], [1, 3, 5, 7, 9], label='a1',
                      color='red', marker='o', linewidth=3.0,
                      linestyle='dashed', markersize=5.0),
        ]

        self.subplots.assert_called_once()
        self.cmp_calls(self.axes.plot.call_args_list, calls_ref)

    def test_labels(self, mock_plt):
        mock_plt.subplots = self.subplots

        p = plot.Plot()
        p.invoke("""a1 "array 1" a2@1:-1 'array 2'""", from_tty=False)

        calls_ref = [
            mock.call([0, 1, 2, 3, 4], [1, 3, 5, 7, 9], label='array 1'),
            mock.call([0, 1, 2, 3, 4], [3, 2, 4, 8, 2], label='array 2'),
        ]

        self.subplots.assert_called_once()
        self.cmp_calls(self.axes.plot.call_args_list, calls_ref)
