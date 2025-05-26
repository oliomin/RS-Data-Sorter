import sys
from argparse import ArgumentParser
from glob import glob
from io import StringIO

import numpy as np
import pandas as pd

from climatexl import build_climate_sheet

parser = ArgumentParser()
parser.add_argument("filename", help="path of the integration file.")
parser.add_argument("-xl", help="path of the excel file.")
parser.add_argument("-datetime", help="datetime in YYYYMMDDHHmm format.")
parser.add_argument(
    "--ignore-ground-data", action="store_true", help="Ignore surface data"
)
parser.add_argument(
    "--feed-ground-one-by-one", action="store_true", help="Feed surface data one by one"
)

FILENAME = parser.parse_args().filename
EXCEL = parser.parse_args().xl
DATETIME = parser.parse_args().datetime
IGNORE_GROUND_DATA = parser.parse_args().ignore_ground_data
FEDDING_GROUND_ONE_BY_ONE = parser.parse_args().feed_ground_one_by_one


def open_file(filename: str) -> dict[str, str]:
    data_store = dict()
    with open(filename) as file:
        for line in file:
            if line.startswith("["):
                data_store[line.strip("[]\n")] = ""
                key = line.strip("[]\n")
            else:
                data_store[key] += line
    return data_store


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


def selectively_round_off(ds: pd.Series) -> pd.Series:
    def _r(x):
        try:
            return np.round(x)
        except TypeError:
            return x

    _gpm = _r(ds.loc["Geo(gpm)"])
    _dir = _r(ds.loc["Wdir(D)"])
    return pd.Series(
        data=[_gpm, ds.loc["T(C)"], ds.loc["Dew(C)"], _dir, ds.loc["Wspd(m/s)"]],
        index=ds.index,
    )


_df = _df.apply(selectively_round_off, axis=1)

_df = _df.transpose()

print(_df)
_df.to_csv("levels.csv")
print("\nHighest Point:\n", data_store["Highest Point"])
print("Max Wind:\n", data_store["Maximum Wind"])
print("Tropopause 1:\n", data_store["Tropopauses1"])
print("Tropopause 2:\n", data_store["Tropopauses2"])
print("Freezing Level:\n", data_store["Freezing Level"])


def dump_prints():
    _ = open_file(FILENAME)
    with open("print.txt", "w") as file:
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


dump_prints()

if not EXCEL:
    EXCEL = glob("*.xlsx")[0]
    print(f"Using excel file: {EXCEL}. Continue? (default: Y)")
    if input().upper() != "N":
        EXCEL = glob("*.xlsx")[0]
    else:
        sys.exit()

if not IGNORE_GROUND_DATA:
    print("Continue with inserting surface data? (default: Y)")
    if not input().upper() == "N":
        if not FEDDING_GROUND_ONE_BY_ONE:
            while True:
                print("Enter space separated values. example: 1013.2 25.5 24.5 180 2.2")
                ground_data = input().split()
                if not len(ground_data) == 5:
                    print("Entered data is not 5 values. Try again!")
                    continue
                else:
                    break
        else:
            ground_data = []
            while True:
                print("Enter surface pressure:")
                ground_data.append(input())
                print("Temperature:")
                ground_data.append(input())
                print("Dew Point:")
                ground_data.append(input())
                print("Wind Direction:")
                ground_data.append(input())
                print("Wind Speed:")
                ground_data.append(input())
                print(f"Continue with {ground_data}? (default: Y)")
                if input().upper() == "N":
                    ground_data.clear()
                    continue
                else:
                    break

        build_climate_sheet(EXCEL, _levels, _df, DATETIME, ground_data)
else:
    build_climate_sheet(EXCEL, _levels, _df, DATETIME)
