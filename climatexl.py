from openpyxl import load_workbook
import pandas as pd
from datetime import datetime
import sys

def _ascentime(ascentime :str|None = None) -> datetime:
    if ascentime:
        return datetime.strptime(ascentime, '%Y%m%d%H%M')
    else:
        _ = datetime.now()
        if _.hour < 14 and _.hour > 0:
            return _.replace(hour = 0, minute = 0)
        else:
            return _.replace(hour = 12, minute = 0)


def build_climate_sheet(filename :str, levels :list[int], df :pd.DataFrame, ascentime :str|datetime|None = None):
    wb = load_workbook(filename)
    wb.save(filename + '.bkp')

    if ascentime is None:
        print(f"No default datetime set! Continue with {_ascentime().strftime('%Y%m%d%H%M')}? (default: Y)")
        if input().upper() != "N":
            ascentime = _ascentime()
        else:
            sys.exit()

    col_offsets :tuple[int, ...] = (0, 3, 6, 9, 10) 

    if isinstance(ascentime, str): ascentime = _ascentime(ascentime)

    if ascentime.hour == 12: col_offsets = (1, 4, 7, 11, 12)

    row_offset :int = ascentime.day - 1

    for sheet in (str(_) for _ in reversed(levels)):
        row = wb[sheet]['B5'].offset(row_offset)

        _ = df[float(sheet)].to_list()

        row.offset(column = col_offsets[0]).value = _[0]%1e4
        row.offset(column = col_offsets[1]).value = _[1]
        row.offset(column = col_offsets[2]).value = _[2]
        row.offset(column = col_offsets[3]).value = _[3]
        row.offset(column = col_offsets[4]).value = _[4]
    else:
        wb.active = wb['Surface']

    wb.save(filename)

