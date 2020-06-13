#!/usr/bin/python

import gdb
import numpy as np
import matplotlib.pyplot as plt
import mpl_toolkits.mplot3d.axes3d as p3

from gdb_plot import cmd_grammar


class Plotter(gdb.Command):
    cmd_name = 'plot'

    def __init__(self):
        super().__init__(self.cmd_name, gdb.COMMAND_DATA, gdb.COMPLETE_SYMBOL)
        plt.ion()

    def invoke(self, arg, from_tty):
        plt.close()

        cmd = cmd_grammar.command.parseString(arg)

        dt = 1
        if cmd.dt:
            dt = cmd.dt
        elif cmd.fs:
            dt = 1 / cmd.fs

        fig, ax = plt.subplots()

        for record in cmd.records:
            n = len(record.expr)
            t = np.linspace(cmd.t0 or 0, n * dt, n)

            args = []
            if record.fmt:
                args.append(record.fmt)

            optionals = ['label', 'color', 'marker', 'linestyle', 'linewidth', 'markersize']
            kwargs = {}
            for name in optionals:
                if getattr(record, name):
                    kwargs[name] = getattr(record, name)

            ax.plot(t, record.expr, *args, **kwargs)

        ax.grid(cmd.grid if cmd.grid != '' else True)
        if cmd.legend == '' or cmd.legend:
            ax.legend()
        if cmd.axis_equal:
            ax.axis('equal')

        plt.show()
        plt.pause(0.2)


class Plot3D(gdb.Command):
    def __init__(self):
        super().__init__("plot3", gdb.COMMAND_OBSCURE)

    def invoke(self, arg, from_tty):
        args = arg.split()

        data = gp_get_data(args)
        fig = plt.figure()
        ax = p3.Axes3D(fig)
        ax.grid(True)
        for  u in data:
            if u.dtype.kind == 'c':
                ax.plt(list(range(len(u))), u.real, u.imag)
        leg = ax.legend((args),
            'upper right', shadow=False)
        leg.get_frame().set_alpha(0.5)
        plt.show()


Plotter()
Plot3D()
