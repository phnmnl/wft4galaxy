#!/usr/bin/env python

import os
import sys
import unittest

TestDir = os.path.abspath(os.path.dirname(__file__))


class TestRoundedCsvComparator(unittest.TestCase):
    CorrelationFile = os.path.join(TestDir, 'correlation_table.csv')

    def test_identical_files(self):
        from wft4galaxy.comparators import rounded_comparison_csv
        self.assertTrue(rounded_comparison_csv(self.CorrelationFile, self.CorrelationFile))

    def test_diff_heading(self):
        from wft4galaxy.comparators import rounded_comparison_csv
        different_file = os.path.join(TestDir, 'diff_heading.csv')
        self.assertFalse(rounded_comparison_csv(different_file, self.CorrelationFile))

    def test_diff_field(self):
        from wft4galaxy.comparators import rounded_comparison_csv
        different_file = os.path.join(TestDir, 'diff_field.csv')
        self.assertFalse(rounded_comparison_csv(different_file, self.CorrelationFile))

    def test_diff_field_less_than_roundoff(self):
        from wft4galaxy.comparators import rounded_comparison_csv
        # A number in a field is different, but at a higher precision than required
        # by comparison function
        different_file = os.path.join(TestDir, 'diff_under_round.csv')
        self.assertTrue(rounded_comparison_csv(different_file, self.CorrelationFile))


def suite():
    return unittest.TestLoader().loadTestsFromTestCase(TestRoundedCsvComparator)


def main():
    result = unittest.TextTestRunner(verbosity=2).run(suite())
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
