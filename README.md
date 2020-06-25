# gdb-plot

> This is a fork of https://github.com/bthcode/gdb-plot with some improvements.

This is a set of utilities for plotting and working with array data directly from GDB.
Features:

* plot an array directly from GDB command line
* export an array to .mat file (or other formats)
* print short summary of stack frame variables

## Overview

Support for:

 * c array, c pointer
 * STL vector
 * Eigen vector, Eigen array
 * Boost vector
 * Boost complex vector

## Installation

Clone this repository to `<your_directory>`.
There are two main ways of installing this plugin.

### Source it

This is the most straightforwad option.
Just add this line to your `~/.gdbinit`:

```
source <your_directory>/gdb_setup.py
```

and make sure you have all the requirements installed (`python -m pip install -r <your_directory>/requirements.txt`)

### Import it

As an alternative you can install the Python package with `pip` (optionally with `--user`):

```
python -m pip install <your_directory>
```

and then add the following to your `~/.gdbinit` (or call it manually every time):

```
python import gdb_plot
```
