

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

