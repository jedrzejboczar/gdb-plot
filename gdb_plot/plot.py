#!/usr/bin/python

import gdb
import numpy as np
import matplotlib.pyplot as plt
import mpl_toolkits.mplot3d.axes3d as axes3d
import pyparsing

from gdb_plot import cmd_grammar


class Plot(gdb.Command):
    cmd_name = 'plot'

    def __init__(self):
        super().__init__(self.cmd_name, gdb.COMMAND_DATA, gdb.COMPLETE_SYMBOL)

    def invoke(self, arg, from_tty):
        cmd = cmd_grammar.command.parseString(arg, parseAll=True)

        self.plot_init()
        fig, axis = plt.subplots()

        for record in cmd.records:
            t = self.generate_time(cmd, n=len(record.expr))
            args, kwargs = self.get_plot_args(record)
            axis.plot(t, record.expr, *args, **kwargs)

        self.configure_axis(cmd, axis)

        self.plot_show()

    def plot_init(self):
        plt.close()
        plt.ion()

    def plot_show(self):
        plt.show()
        plt.pause(0.2)

    def get_plot_args(self, record: pyparsing.ParseResults) -> dict:
        """Contruct arguments for Axes.plot() from cmd.record"""
        args = []
        if record.fmt:
            args.append(record.fmt)

        optionals = ['label', 'color', 'marker', 'linestyle', 'linewidth', 'markersize']
        kwargs = {}
        for name in optionals:
            if getattr(record, name):
                kwargs[name] = getattr(record, name)

        kwargs['label'] = kwargs.get('label', record.string.strip())

        return args, kwargs

    def generate_time(self, cmd: pyparsing.ParseResults, n: int) -> np.array:
        dt = cmd.dt or 1
        if cmd.fs:
            dt = 1 / cmd.fs
        t = np.linspace(cmd.t0 or 0, (n - 1) * dt, n)
        return t

    def configure_axis(self, cmd: pyparsing.ParseResults, axis: plt.Axes):
        axis.grid(cmd.grid if cmd.grid != '' else True)
        if cmd.legend or cmd.legend == '':  # defaults to 'yes'
            axis.legend()
        if cmd.axis_equal:
            axis.axis('equal')


# Basic implementation of 3D plotting, as the main focus is 2D plotting anyway
class Plot3D(Plot):
    cmd_name = 'plot3d'

    def __init__(self):
        gdb.Command.__init__(self.cmd_name, gdb.COMMAND_DATA, gdb.COMPLETE_SYMBOL)

    def invoke(self, arg, from_tty):
        cmd = cmd_grammar.command.parseString(arg, parseAll=True)

        if len(cmd.records) not in [2, 3]:
            raise gdb.GdbError('You must provide either 2 or 3 data records for a 3D plot')

        self.plot_init()
        fig = plt.figure()
        axis = axes3d.Axes3D(fig)

        args, kwargs = self.get_plot_args(cmd.records[0])
        if len(cmd.records) == 2:
            t = self.generate_time(cmd, n=len(record.expr))
            axis.plt(t, cmd.records[0].expr, cmd.records[1].expr, *args, **kwargs)
        else:
            axis.plt(cmd.records[0].expr, cmd.records[1].expr, cmd.records[2].expr, *args, **kwargs)

        self.configure_axis(cmd, axis)
        self.plot_show()
