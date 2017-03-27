import os as _os
import sys as _sys
from wft4galaxy import common as _common
from difflib import unified_diff as _unified_diff

_logger = _common.default_logger


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
            return cmp(colsActual, colsExpected) == 0
        return False
