from models.db import dbPgCloud
import pandas as pd
import numpy as np
from datetime import datetime
from fredapi import Fred

db = dbPgCloud()

class workdays():
    def __init__(self) -> None:
        self.holidays = np.array(db.get_feriados()['Data'].to_list(),dtype='datetime64')
        self.today = datetime.today()
        self.strtoday = self.today.strftime("%Y-%m-%d")
    def between(self,start_date,end_date) -> int:
        return np.busday_count(start_date,end_date,holidays=self.holidays)
    def offset(self,start_date,days) -> datetime:
        return np.busday_offset(start_date,days,roll='forward',holidays=self.holidays)
    def range(self,start:datetime,end:datetime) -> pd.DatetimeIndex:
        return pd.date_range(
            start = start,
            end = end,
            freq = pd.tseries.offsets.CustomBusinessDay(
                holidays = self.holidays
            )
        )

class sqlfunctions():
    def __init__(self) -> None:
        pass

fred = Fred(api_key="17510977a24f66e589677c4584090116")

def get_fred_series(series_id, start_date="2000-01-01"):
    """Download a FRED series as a pandas Series"""
    data = fred.get_series(series_id)
    data = data[data.index >= pd.to_datetime(start_date)]
    data = data.sort_index()
    return data

def get_rbusbis_series(start_date="2000-01-01"):
    """Download the RBUSBIS series without any deflation"""
    rbusb = get_fred_series("RBUSBIS", start_date)
    df = pd.DataFrame({"rbusbis": rbusb}).dropna()
    return df


if __name__ == '__main__':
    wd = workdays()
    print(np.datetime_as_string(np.datetime64(wd.today)))

    