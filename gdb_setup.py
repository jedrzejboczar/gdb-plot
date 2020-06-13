import os
import sys

this_file = os.path.expanduser(__file__)
gdb_plot_path = os.path.dirname(os.path.abspath(os.path.realpath(this_file)))
sys.path.insert(0, gdb_plot_path)

import gdb_plot
