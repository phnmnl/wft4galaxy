from __future__ import print_function

import os as _os
import sys as _sys
import logging as _logging
from difflib import unified_diff as _unified_diff
from wft4galaxy import common as _common

_logger = _common.LoggerManager.get_logger(__name__)


def load_comparator(fully_qualified_comparator_function):
    """
    Utility function responsible for dynamically loading a comparator function
    given its fully qualified name.

    :type fully_qualified_comparator_function: str
    :param fully_qualified_comparator_function: fully qualified name of a comparator function

    :return: a callable reference to the loaded comparator function
    """
    mod = None
    try:
        components = fully_qualified_comparator_function.split('.')
        mod = __import__(components[0])
        for comp in components[1:]:
            mod = getattr(mod, comp)
    except ImportError as e:
        _logger.error(e)
    except AttributeError as e:
        _logger.error(e)
    except:
        _logger.error("Unexpected error: %s", _sys.exc_info()[0])
    return mod


def base_comparator(actual_output_filename, expected_output_filename):
    _logger.debug("Using default comparator....")
    with open(actual_output_filename) as aout, open(expected_output_filename) as eout:
        diff = _unified_diff(aout.readlines(), eout.readlines(), actual_output_filename, expected_output_filename)
        ldiff = list(diff)
        if len(ldiff) > 0:
            print("\n{0}\n...\n".format("".join(ldiff[:20])))
            diff_filename = _os.path.join(_os.path.dirname(actual_output_filename),
                                          _os.path.basename(actual_output_filename) + ".diff")
            with open(diff_filename, "w") as  out_fp:
                out_fp.writelines("%r\n" % item.rstrip('\n') for item in ldiff)
        return len(ldiff) == 0


def csv_same_row_and_col_lengths(actual_output_filename, expected_output_filename):
    import csv

    with open(actual_output_filename) as af, open(expected_output_filename) as ef:
        aout = csv.reader(af)
        eout = csv.reader(ef)
        colsActual = []
        colsExpected = []
        for row in aout:
            colsActual.append(len(row))

        for row in eout:
            colsExpected.append(len(row))

        if colsActual and colsExpected:
            return _common.cmp(colsActual, colsExpected) == 0
        return False


def _get_float(s):
    try:
        return float(s)
    except ValueError:
        return None


def _compare_strings_as_floats(precision, a, b):
    a_float = _get_float(a)
    b_float = _get_float(b)
    if a_float is not None and b_float is not None:
        return round(a_float, precision) == round(b_float, precision)
    else:
        return False


def rounded_comparison_csv(actual_output, expected_output):
    import csv
    try:
        from itertools import izip
    except ImportError:
        # in Python 3 zip() function returns an iterator
        izip = zip
    precision = 2
    try:
        with open(actual_output) as actual, open(expected_output) as expected:
            aout = csv.reader(actual)
            eout = csv.reader(expected)
            for expected_row in eout:
                actual_row = next(aout)
                for actual_field, expected_field in izip(actual_row, expected_row):
                    if not _compare_strings_as_floats(precision, actual_field, expected_field) \
                            and actual_field != expected_field:
                        print("Difference found between expected and actual output", file=_sys.stderr)
                        print("Expected field text:", expected_field, file=_sys.stderr)
                        print("Actual field text:", actual_field, file=_sys.stderr)
                        print("Expected row:", expected_row, file=_sys.stderr)
                        print("Actual row:", actual_row, file=_sys.stderr)
                        return False
    except StopIteration:
        print("Actual output is shorted than expected output", file=_sys.stderr)
        return False

    return True
