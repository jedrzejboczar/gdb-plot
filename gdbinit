python

import os
import sys

gdbplot_env = 'GDB_PLOT_ROOT_DIR'

if gdbplot_env not in os.environ:
    print('WARNING: gdb-plot: environmental variable %s not found: cannot load gdb-plot' % gdbplot_env)
else:
    sys.path.insert(0, os.path.expanduser(os.environ[gdbplot_env]))

    import plotter
    import show_frame
    import savemat

end
