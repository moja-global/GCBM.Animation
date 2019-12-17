import os
import sqlite3
from collections import OrderedDict
from gcbmanimation.provider.gcbmresultsprovider import GcbmResultsProvider

class SqliteGcbmResultsProvider(GcbmResultsProvider):
    '''
    Retrieves non-spatial annual results from a SQLite GCBM results database.

    Arguments:
    'path' -- path to SQLite GCBM results database.
    '''

    results_tables = {
        "v_flux_indicator_aggregates": "flux_tc",
        "v_flux_indicators"          : "flux_tc",
        "v_pool_indicators"          : "pool_tc",
        "v_stock_change_indicators"  : "flux_tc",
    }

    def __init__(self, path):
        if not os.path.exists(path):
            raise IOError(f"{path} not found.")

        self._path = path

    @property
    def simulation_years(self):
        '''See GcbmResultsProvider.simulation_years.'''
        conn = sqlite3.connect(self._path)
        years = conn.execute("SELECT MIN(year), MAX(year) from v_age_indicators").fetchone()

        return years

    def get_annual_result(self, indicator, units=1, **kwargs):
        '''See GcbmResultsProvider.get_annual_result.'''
        conn = sqlite3.connect(self._path)
        table, value_col = self._find_indicator_table(indicator)
        db_result = conn.execute(
            f"""
            SELECT years.year, COALESCE(SUM(i.{value_col}), 0) / {units} AS value
            FROM (SELECT DISTINCT year FROM v_age_indicators ORDER BY year) AS years
            LEFT JOIN {table} i
                ON years.year = i.year
            WHERE i.indicator = '{indicator}'
            GROUP BY years.year
            ORDER BY years.year
            """).fetchall()

        data = OrderedDict()
        for year, value in db_result:
            data[year] = value

        return data

    def _find_indicator_table(self, indicator):
        conn = sqlite3.connect(self._path)
        for table, value_col in SqliteGcbmResultsProvider.results_tables.items():
            if conn.execute(f"SELECT 1 FROM {table} WHERE indicator = ?", [indicator]).fetchone():
                return table, value_col

        return None, None
