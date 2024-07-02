__all__ = ['SOURCE_URL', 'NP', 'PJM', 'BE', 'FR', 'DE', 'EPFInfo', 'EPF']

import os
if not os.path.exists('./results/'):
    os.makedirs('./results/')

from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from pandas.tseries.frequencies import to_offset

from .utils import download_file, Info, TimeSeriesDataclass

# Cell
SOURCE_URL = 'https://sandbox.zenodo.org/api/files/da5b2c6f-8418-4550-a7d0-7f2497b40f1b/'

# Cell


@dataclass
class NP:
    test_date: str = '2016-12-27'
    name: str = 'NP'


@dataclass
class PJM:
    test_date: str = '2016-12-27'
    name: str = 'PJM'


@dataclass
class BE:
    test_date: str = '2015-01-04'
    name: str = 'BE'


@dataclass
class FR:
    test_date: str = '2015-01-04'
    name: str = 'FR'


@dataclass
class DE:
    test_date: str = '2016-01-04'
    name: str = 'DE'


@dataclass
class data_nbeatsx:
    test_date: str = '01/06/2019  00:00:00'
    name: str = 'data_nbeatsx'


@dataclass
class data_nbeatsx_inpg:
    test_date: str = '01/06/2019  00:00:00'
    name: str = 'data_nbeatsx_inpg'


# Cell
EPFInfo = Info(groups=('NP', 'PJM', 'BE', 'FR', 'DE', 'data_nbeatsx', 'data_nbeatsx_inpg'),
               class_groups=(NP, PJM, BE, FR, DE, data_nbeatsx, data_nbeatsx_inpg))

# Cell


class EPF:

    @staticmethod
    def load(directory: str,
             group: str) -> Tuple[pd.DataFrame,
                                  Optional[pd.DataFrame],
                                  Optional[pd.DataFrame]]:
        """
        Downloads and loads EPF data.

        Parameters
        ----------
        directory: str
            Directory where data will be downloaded.
        group: str
            Group name.
            Allowed groups: 'NP', 'PJM', 'BE', 'FR', 'DE' ,'data_nbeatsx','data_nbeatsx_inpg'.
        """
        path = Path(directory) / 'epf' / 'datasets'

        EPF.download(directory)

        class_group = EPFInfo.get_group(group)

        file = path / f'{group}.csv'

        df = pd.read_csv(file)
        print(df.columns)

        if 'Unnamed: 0' in df.columns:
            df = df.drop(columns=['Unnamed: 0'])

        # Identify exogenous columns
        exogenous_columns = [
            col for col in df.columns if col not in ['ds', 'y']]

        # Define the desired column order
        desired_columns = ['ds', 'y'] + exogenous_columns

        # Reindex the DataFrame with the desired column order
        df = df.reindex(columns=desired_columns)

        print(df.columns)

        print(df.head())

        print(df.columns, df['ds'].iloc[-1])

        df['unique_id'] = group

        print('\n', '3rd head', df.head())
        print(df['ds'].iloc[-1])
        df['ds'] = pd.to_datetime(df['ds'],format='mixed')
        print(df['ds'].iloc[-1])
        df['week_day'] = df['ds'].dt.dayofweek

        dummies = pd.get_dummies(df['week_day'], prefix='day')
        df = pd.concat([df, dummies], axis=1)

        dummies_cols = [col for col in df if col.startswith('day')]

        Y = df.filter(items=['unique_id', 'ds', 'y'])
        X = df.filter(items=['unique_id', 'ds', 'attention', 'topattn' ,'dayofweek', 'month', 'day', 'season', 'is_weekend',
                    'is_month_start', 'days_since_start_of_year','is_month_end', 'is_quarter_start',
                    'temperature_2m', 'relative_humidity_2m',
                    'precipitation','snow_depth', 'surface_pressure', 'cloud_cover', 'wind_speed_10m'] +
                      dummies_cols)

        return Y, X, None

    @staticmethod
    def load_groups(directory: str,
                    groups: List[str]) -> Tuple[pd.DataFrame,
                                                Optional[pd.DataFrame],
                                                Optional[pd.DataFrame]]:
        """
        Downloads and loads panel of EPF data
        according of groups.

        Parameters
        ----------
        directory: str
            Directory where data will be downloaded.
        groups: List[str]
            Group names.
            Allowed groups: 'NP', 'PJM', 'BE', 'FR', 'DE'.
        """
        Y = []
        X = []
        for group in groups:
            Y_df, X_df, S_df = EPF.load(directory=directory, group=group)
            Y.append(Y_df)
            X.append(X_df)

        Y = pd.concat(Y).sort_values(
            ['unique_id', 'ds']).reset_index(drop=True)
        X = pd.concat(X).sort_values(
            ['unique_id', 'ds']).reset_index(drop=True)

        S = Y[['unique_id']].drop_duplicates().reset_index(drop=True)
        dummies = pd.get_dummies(S['unique_id'], prefix='static')
        S = pd.concat([S, dummies], axis=1)

        return Y, X, S

    @staticmethod
    def download(directory: str) -> None:
        """Downloads EPF Dataset."""
        path = Path(directory) / 'epf' / 'datasets'
        if not path.exists():
            for group in EPFInfo.groups:
                download_file(path, SOURCE_URL + f'{group}.csv')
