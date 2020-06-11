"""
Utilities for interfacing with GDB and extracting C/C++ array data as Python
numpy arrays. Tries to support both regular arrays, raw pointers, as well as
some common array types that hold information about their length.
"""

from typing import Union

import gdb
import numpy as np


def gdb_type_code_str(code: int) -> str:
    """Map gdb.Type.code to its name"""
    code_map = {getattr(gdb, c): c for c in dir(gdb) if c.startswith('TYPE_CODE')}
    return code_map[code]


def is_complex(value: gdb.Value) -> bool:
    # std::complex will be a struct with one field _M_value of complex type
    return value.type.code == gdb.TYPE_CODE_STRUCT and \
        value.type.fields()[0].name == '_M_value' and \
        value.type.fields()[0].type.strip_typedefs().code == gdb.TYPE_CODE_COMLEX


def parse_complex(value: gdb.Value) -> complex:
    # example "0.25 + -0.33 * I"
    real, imag = str(value).split('+')
    imag = imag.split('*')
    return float(real) + float(imag) * 1j


def parse_simple(value: gdb.Value) -> Union[float, complex]:
    """Parse either a simple number (float/int) or a complex value (std::complex)"""
    return float(value) if not is_complex(value) else parse_complex(value)


def gdb_array_eval(name: str, start: int = 0, stop: int = None, step: int = 1) -> np.array:
    """Retrieve data from GDB varable into numpy array

    Supports arrays, raw pointers (unknown length) and some special types:
    * std::vector
    * Eigen::Array
    * Boost::Numerics::...
    """
    value = gdb.parse_and_eval(name)
    base_type = value.type.strip_typedefs()
    code = base_type.code

    if code in [gdb.TYPE_CODE_INT, gdb.TYPE_CODE_FLT]:
        return np.array([parse_simple(value)])
    if code == gdb.TYPE_CODE_ARRAY:
        _lower, upper = base_type.range()
        if stop is None:
            stop = upper
        values = [parse_simple(value[i]) for i in range(start, min(stop, upper), step)]
        return np.array(values)
    if code == gdb.TYPE_CODE_PTR:
        assert stop is not None, 'Unknown length of raw pointer type: %s' % value.type
        values = [parse_simple(value[i]) for i in range(start, stop, step)]
        return np.array(values)
    if code == gdb.TYPE_CODE_STRUCT:
        if 'boost' in base_type:
            raise NotImplementedError('boost')
            #  return parse_boost(value, length)
        elif 'std::vector' in base_type:
            raise NotImplementedError('std::vector')
            #  return parse_stl_vector(value, length)
        elif 'Eigen::Array' in base_type:
            raise NotImplementedError('Eigen::Array')
            #  return parse_stl_vector(value, length)
    raise NotImplementedError('value.type = {}, .code = {}'.format(
        value.type, gdb_type_code_str(code)))

#  def parse_boost(value, length=None):
