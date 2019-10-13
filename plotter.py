#!/usr/bin/python

__author__="Brian Hone"


import sys, os, string
import matplotlib.pyplot as plot
import mpl_toolkits.mplot3d.axes3d as p3
import numpy as np
import gdb
import re
import argparse

from gp_data_extractor import *

class Plotter(gdb.Command):
    cmd_name = 'plot'

    def __init__(self):
        super().__init__(self.cmd_name, gdb.COMMAND_DATA, gdb.COMPLETE_SYMBOL)
        self.parser = argparse.ArgumentParser(description='Creates plots from arrays.')
        self.parser.add_argument('arrays', metavar='array@len', nargs='+',
                    help='array variables in format name@len' +
                        ', it is possible to scale arrays with special syntax' +
                        ', e.g. array@len*10+3 (no spaces, this order, if no multiplication use 1, if no addition use 0)')
        self.parser.add_argument('--dt', type=float,
                    help='if given, will construct time as x axis values')
        self.parser.add_argument('--fs', type=float,
                    help='sampling frequency, works like --dt (but with inverse), specifying both is undefined')

    def parse_arrays_scalings(self, array_strings):
        basic_pattern = re.compile(r'(\w+@\d+)')  # matches the part "array@len"
        scaling_pattern = re.compile(r'([*/])([\d.]+)([+-])([\d.]+)')  # matches the part "*3.5+22"
        arrays, multips, added = [], [], []
        for arr in array_strings:
            multip = 1
            add = 0
            match = re.match(basic_pattern, arr)
            if not match or len(match.groups()) != 1:
                print('Error in argument "%s" (this should not have happend)' % arr)
                continue
            basic_string = match.groups()[0]
            scaling_string = arr[match.end():]
            print(scaling_string)
            if len(scaling_string) > 0:
                match = re.match(scaling_pattern, scaling_string)
                if not match or len(match.groups()) != 4:
                    print('Error parsing scaling for argument "%s"' % arr)
                    continue
                try:
                    multip = float(match.groups()[1])
                    if match.groups()[0] == '/':
                        multip = 1.0 / multip
                    add = float(match.groups()[3])
                    if match.groups()[0] == '-':
                        add = -add
                except:
                    raise
            arrays.append(basic_string)
            multips.append(multip)
            added.append(add)
        return arrays, multips, added

    def invoke(self, arg, from_tty):
        args = self.parser.parse_args(gdb.string_to_argv(arg))
        if args.fs:
            args.dt = 1.0 / args.fs
        arrays, multips, added = self.parse_arrays_scalings(args.arrays)
        data = gp_get_data(arrays)
        fig, ax = plot.subplots()
        for u, name, multip, add in zip(data, args.arrays, multips, added):
            u = np.array(u)
            if args.dt:
                t = np.linspace(0, len(u) * args.dt, len(u))
            else:
                t = np.arange(len(u))
            if u.dtype.kind == 'c':
                u = np.abs(u)
            print(multip)
            print(add)
            ax.plot(t, u * multip + add, label=name)
        ax.grid(True)
        ax.legend()
        plot.show()
# end class Plotter

class PlotThreeD( gdb.Command ):
    def __init__( self ):
        super( PlotThreeD, self ).__init__("plot3", gdb.COMMAND_OBSCURE )

    def invoke( self, arg, from_tty ):
        args = arg.split()

        data = gp_get_data( args )
        fig = plot.figure()
        ax = p3.Axes3D( fig )
        ax.grid( True )
        for  u in data:
            if u.dtype.kind == 'c':
                ax.plot( list(range(len(u))), u.real, u.imag )
        leg = ax.legend((args),
            'upper right', shadow=False)
        leg.get_frame().set_alpha(0.5)
        plot.show()
# end class PlotThreeD




Plotter()
PlotThreeD()
