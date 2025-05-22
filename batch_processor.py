import shutil
import sys
from argparse import ArgumentParser
from glob import glob
from pathlib import Path
from zipfile import ZipFile

from utils import csv_yield, postprocess

parser = ArgumentParser()
parser.add_argument("-dir", help="directory containing integration files.")
parser.add_argument("-xl", help="path of the excel file.")
parser.add_argument("--ground-data", help="path to ground data csv file.")
parser.add_argument(
    "--ignore-ground-data", action="store_true", help="Ignore surface data."
)
parser.add_argument(
    "--feed-ground-one-by-one",
    action="store_true",
    help="Feed surface data one by one.",
)
parser.add_argument(
    "--ground-data-csv-path",
    help="Feed surface data from the csv file. See --generate-template-csv-file for format.",
)
parser.add_argument(
    "--generate-template-csv-file",
    action="store_true",
    help="Create a template csv file for ground data. Use with --dir argument.",
)

DIR = parser.parse_args().dir
EXCEL = parser.parse_args().xl
IGNORE_GROUND_DATA = parser.parse_args().ignore_ground_data
FEDDING_GROUND_ONE_BY_ONE = parser.parse_args().feed_ground_one_by_one
GROUND_DATA_CSV = parser.parse_args().ground_data_csv_path
GENERATE_TEMPLATE_CSV_FILE = parser.parse_args().generate_template_csv_file


def sanitize_dir_input(dir: str):
    _ = None
    if dir.endswith(".zip"):
        _ = ZipFile(dir)
    else:
        try:
            _ = Path(dir)
        except:
            print("Invalid Path. Exiting.")
            sys.exit(1)
    return _


def iterate_files(path: Path | ZipFile):
    if isinstance(path, ZipFile):
        for file in path.namelist():
            if file.endswith(".txt"):
                yield Path(file)
    else:
        for file in path.iterdir():
            if file.is_file() and file.suffix == ".txt":
                yield file


def parse_datetime_from_filename(filename):
    _ = filename.split("-")
    return _[0] + _[1] + "00"


if __name__ == "__main__":
    if GENERATE_TEMPLATE_CSV_FILE:
        if not DIR:
            print(
                """No directory provided. Enter the path to the directory or the zip
                     file containing the integration files. (default: current directory)"""
            )
            if _ := input():
                DIR = _
            else:
                DIR = Path(".")
        datetimes = []
        for file in iterate_files(sanitize_dir_input(DIR)):
            datetimes.append(parse_datetime_from_filename(file.name))
        print(f"Creating template csv file for {len(datetimes)} files.")
        with open("ground_data_template.csv", "w") as file:
            file.write(
                "Datetime,Surface Pressure,Temperature,Dew Point,Wind Direction,Wind Speed\n"
            )
            for datetime in datetimes:
                file.write(f"{datetime},,,,,\n")
        print("Template csv file created.")
        sys.exit(0)

    if not DIR:
        print(
            """No directory provided. Enter the path to the directory or the zip
                 file containing the integration files. (default: current directory)"""
        )
        if _ := input():
            DIR = _
        else:
            DIR = Path(".")

    if not EXCEL:
        EXCEL = glob("*.xlsx")[0]
        print(f"Using excel file: {EXCEL}. Continue? (default: Y)")
        if input().upper() != "N":
            EXCEL = glob("*.xlsx")[0]
        else:
            sys.exit()
    shutil.copy(EXCEL, f"{EXCEL}.bkp")

    if GROUND_DATA_CSV:
        _ground_dict = {}
        for _ in csv_yield(GROUND_DATA_CSV):
            _ground_dict[_[0]] = [*_[1:]]

    for file in iterate_files(sanitize_dir_input(DIR)):
        print("Processing file....", file.name)
        ground_data: list[str] | None = []
        if GROUND_DATA_CSV:
            ground_data = _ground_dict.get(parse_datetime_from_filename(file.name))
        elif not IGNORE_GROUND_DATA:
            try:
                print(
                    f"Continue with inserting surface data for file: {file}? (default: Y)"
                )
                if not input().upper() == "N":
                    if not FEDDING_GROUND_ONE_BY_ONE:
                        while True:
                            print(
                                "Enter space separated values. example: 1013.2 25.5 24.5 180 2.2"
                            )
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
            except KeyboardInterrupt:
                print("Exitting...Bye! o(*￣▽￣*)ブ")
                sys.exit(1)

        postprocess(file, EXCEL, parse_datetime_from_filename(file.name), ground_data)
        if isinstance(ground_data, list):
            ground_data.clear()

    else:
        print("\nProcessing complete. Exitting...")
        print("(❁´◡`❁) Bye Bye.")
