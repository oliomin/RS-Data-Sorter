import csv
from io import StringIO

import numpy as np
import pandas as pd

from climatexl import build_climate_sheet


def csv_yield(filename, /, *cols, first_row_is_headers=True, col_indices=None):
    with open(filename, newline="") as file:
        reader = csv.reader(file)
        for _, row in enumerate(reader):
            if (not _) and first_row_is_headers:
                _headers = [*row]
                continue
            if cols:
                yield [row[_headers.index(_)] for _ in cols]
            elif col_indices:
                yield [row[__] for __ in col_indices]
            else:
                yield row


def open_file(filename):
    data_store = dict()
    with open(filename) as file:
        for line in file:
            if line.startswith("["):
                data_store[line.strip("[]\n")] = ""
                key = line.strip("[]\n")
            else:
                data_store[key] += line
    return data_store


def preprocess(FILENAME):
    data_store = open_file(FILENAME)
    #########################################
    #  REMOVE TAB CHARACTERS
    #########################################
    for key, val in data_store.items():
        data_store[key] = data_store[key].replace("\t", "")

    #########################################
    #  REMOVE SPACE CHARACTERS FROM TABLES
    #########################################
    for key in "Standard Isobaric Surfaces", "Regional Wind Levels":
        data_store[key] = data_store[key].replace(" ", "")

    _df = pd.read_csv(StringIO(data_store["Standard Isobaric Surfaces"]))
    _levels = [30, 50, 100, 150, 200, 300, 500, 700, 850, 925, 1000]

    _df = _df.set_index("P(hPa)")
    _levels = [_ for _ in _levels if _ >= min(_df.index)]

    _df = _df.loc[_levels, (_df.columns[_] for _ in (0, 2, 3, 6, 7))].sort_index(
        ascending=False
    )

    def selectively_round_off(ds):
        def _r(x):
            try:
                return np.round(x)
            except:
                return x

        _gpm = _r(ds.loc["Geo(gpm)"])
        _dir = _r(ds.loc["Wdir(D)"])
        return pd.Series(
            data=[_gpm, ds.loc["T(C)"], ds.loc["Dew(C)"], _dir, ds.loc["Wspd(m/s)"]],
            index=ds.index,
        )

    _df = _df.apply(selectively_round_off, axis=1)

    _df = _df.transpose()

    _df.to_csv("levels.csv")

    return [_levels, _df]


def dump_prints(file):
    _ = open_file(file)
    with open(f"{file.name}_print.txt", "w") as file:
        # page 1
        for key in (
            "Station Information",
            "Flight Start Time",
            "Highest Point",
            "Maximum Wind",
            "Tropopauses1",
            "Tropopauses2",
            "Freezing Level",
            "Cloud Data",
        ):
            file.write(f"[{key}]\n")
            file.write(_[key])
        else:
            file.write("\n" * 3)

        # page 3
        file.write("[Standard Isobaric Surfaces]\n")
        file.write(_["Standard Isobaric Surfaces"])
        file.write("\n" * 3)

        # page 2
        file.write("[WMO Message]\n")
        file.write(_["WMO Message"])
        file.write("\n" * 3)

        # page 4
        file.write("[Regional Wind Levels]\n")
        file.write(_["Regional Wind Levels"])
        file.write("\n" * 3)


def postprocess(file, excel_file, datetime, ground_data=None):
    dump_prints(file)
    _levels, _df = preprocess(file)
    if not ground_data:
        build_climate_sheet(excel_file, _levels, _df, datetime, backup=False)
    else:
        build_climate_sheet(
            excel_file, _levels, _df, datetime, ground_data, backup=False
        )
