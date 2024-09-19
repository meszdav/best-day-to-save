import datetime
from typing import Tuple, Union
import polars as pl
import calendar

import logging
from pathlib import Path


logger = logging.getLogger(__name__)


class SavingPlan:
    """Class to calculate the total worth of a saving plan.

    Parameters
    ----------
    df : pl.DataFrame
        The DataFrame containing the stock data.
    invest_amount : int
        The amount of money to invest each month.
    day_to_invest : int
        The day of the month to invest the money.
    period : Union[str, Tuple[datetime.datetime, datetime.datetime]]
        The period to consider for the calculations. If a string is passed, the only available value is 'max'.
        If a tuple is passed, it should contain two datetime objects.

    Attributes
    ----------
    total_worth : float
        The total worth of the saving plan.
    result_df : pl.DataFrame
        The DataFrame containing the results of the calculations.

    Examples
    --------
    >>> import polars as pl
    >>> from datetime import datetime
    >>> from saving_plan import SavingPlan
    >>> df = pl.DataFrame(
    ...     {
    ...         "Date": ["2021-01-01", "2021-01-02", "2021-01-03", "2021-01-04", "2021-01-05"],
    ...         "Close": [10, 20, 30, 40, 50]
    ...     }
    ... ).lazy()
    >>> df = df.with_column(pl.col("Date").cast(pl.Date))
    >>> invest_amount = 100
    >>> day_to_invest = 1
    >>> period = (datetime(2021, 1, 1), datetime(2021, 1, 5))
    >>> saving_plan = SavingPlan(df, invest_amount, day_to_invest, period)
    >>> saving_plan.total_worth
    100.0
    >>> saving_plan.result_df.collect()
    shape: (1, 4)
    ╭───────┬────────────┬─────────────┬─────────────╮
    │ Date  ┆ bought_st… ┆ all_stocks  ┆ total_worth │
    │ ---   ┆ ---        ┆ ---         ┆ ---         │
    │ date  ┆ f64        ┆ f64         ┆ f64         │
    ╞═══════╪════════════╪═════════════╪═════════════╡
    │ 2021… ┆ 10         ┆ 10          ┆ 100         │
    ╰───────┴────────────┴─────────────┴─────────────╯
    """

    def __init__(
        self,
        df: pl.DataFrame,
        invest_amount: int,
        day_to_invest: int,
        period: Union[str, Tuple[datetime.datetime, datetime.datetime]],
    ):
        self.df = df

        self.invest_amount = invest_amount
        self.day_to_invest = day_to_invest
        self.period = period

        if isinstance(self.period, str):

            assert (
                self.period == "max"
            ), "If using string the only available value is 'max'"
        else:
            self.df = df.pipe(self.replace_timezone).filter(
                pl.col("Date").is_between(
                    pl.lit(self.period[0]), pl.lit(self.period[1])
                )
            )

        self._total_worth = None
        self._result_df = None

    @property
    def total_worth(self):
        if self._total_worth is None:
            self._total_worth = self.get_total_worth()
        return self._total_worth

    @property
    def result_df(self):
        if self._result_df is None:
            self._result_df = self.get_result_df()
        return self.get_result_df()

    def replace_timezone(self, df: pl.DataFrame) -> pl.DataFrame:
        """Get rid of the timezone information"""
        return df.with_columns(pl.col("Date").dt.replace_time_zone(None))

    def extract_year(self, col="Date"):
        return pl.col(col).dt.year().alias("year")

    def extract_month(self, col="Date"):
        return pl.col(col).dt.month().alias("month").cast(pl.Int32)

    def extract_day(self, col="Date"):
        return pl.col(col).dt.day().alias("day")

    def extract_dates(self, df: pl.DataFrame):
        return df.with_columns(
            self.extract_year(), self.extract_month(), self.extract_day()
        )

    def drop_first_month_if_needed(self, df: pl.DataFrame) -> pl.DataFrame:
        """Drop the first month if the day to invest is before the first day of the **first** month"""
        return df.with_columns(
            pl.when(
                pl.lit(self.day_to_invest)
                .lt(pl.col("Date").min().dt.day())
                .and_(pl.lit(self.period[0]).dt.month().eq(pl.col("month")))
                .and_(pl.lit(self.period[0]).dt.year().eq(pl.col("year")))
            )
            .then(1)
            .otherwise(0)
            .alias("to_drop")
        ).filter(pl.col("to_drop") == 0)

    def drop_last_month_if_needed(self, df: pl.DataFrame) -> pl.DataFrame:
        """Drop the last month if the day to invest is after the last day of the **last** month"""
        return df.with_columns(
            pl.when(
                pl.lit(self.day_to_invest)
                .gt(pl.col("Date").max().dt.day())
                .and_(pl.lit(self.period[1]).dt.month().eq(pl.col("month")))
                .and_(pl.lit(self.period[1]).dt.year().eq(pl.col("year")))
            )
            .then(1)
            .otherwise(0)
            .alias("to_drop")
        ).filter(pl.col("to_drop") == 0)

    def get_prepared_df(self) -> pl.DataFrame:
        """Prepare the DataFrame for the calculations. Adding year, month, day to the dataframe.
        The prepared DataFrame will have only the
        the range of dates that are needed for the calculations.
        """
        prepared_df = (
            self.df.pipe(self.extract_dates)
            # .pipe(self.drop_first_month_if_needed)
            .pipe(self.drop_last_month_if_needed)
        )

        return prepared_df

    def get_filtered_df(self, df: pl.DataFrame) -> pl.DataFrame:
        """Filter the DataFrame to get the days where the investment should be made"""

        # check whether the day to invest is before the last day of the month
        condition_1 = pl.lit(self.day_to_invest).lt(
            pl.col("day").max().over("year", "month")
        )
        # get rid of the duplicates
        condition_2 = (
            pl.col("diff").abs().eq(pl.col("diff").abs().min().over("year", "month"))
        )
        return df.filter(
            pl.when(condition_1)
            .then(pl.col("diff") >= 0)  # if so we keep the positive differences
            .otherwise(pl.col("diff") <= 0)  # if not we keep the negative differences
        ).filter(condition_2)

    def get_diff(self, df: pl.DataFrame) -> pl.DataFrame:
        """Get the difference between the day to invest and the current day"""
        return df.with_columns(
            (pl.col("day") - pl.lit(self.day_to_invest)).alias("diff")
        )

    def add_bought_stocks(self, df: pl.DataFrame) -> pl.DataFrame:
        return df.with_columns(
            (self.invest_amount / pl.col("Close")).alias("bought_stocks")
        )

    def add_all_stocks(self, df: pl.DataFrame) -> pl.DataFrame:
        return df.with_columns(pl.cum_sum("bought_stocks").alias("all_stocks"))

    def add_total_worth(self, df: pl.DataFrame) -> pl.DataFrame:
        return df.with_columns(
            (pl.col("all_stocks") * pl.col("Close")).alias("total_worth")
        )

    def add_day_to_invest(self, df: pl.DataFrame) -> pl.DataFrame:
        return df.with_columns(pl.lit(self.day_to_invest).alias("day_to_invest"))

    def add_pct_chg(self, df: pl.DataFrame) -> pl.DataFrame:
        return df.with_columns(
            pct_chg=pl.col("Close").pct_change().mul(100)
        ).with_columns(abs_pct_chg=pl.col("pct_chg").abs())

    def get_result_df(self) -> pl.DataFrame:
        prepared_df = self.get_prepared_df()
        return (
            prepared_df.pipe(self.get_diff)
            .pipe(self.get_filtered_df)
            .drop("year", "month", "day", "diff", "to_drop")
            .pipe(self.add_bought_stocks)
            .pipe(self.add_all_stocks)
            .pipe(self.add_total_worth)
            .pipe(self.add_day_to_invest)
            .pipe(self.add_pct_chg)
        )

    def get_total_worth(self):
        return self.result_df.sort("Date").select("total_worth").collect()[-1].item()


#  function to get saving plans for a period of a time for each day of the month
def get_saving_plans(
    df: pl.DataFrame,
    invest_amount: int,
    period: Tuple[datetime.datetime, datetime.datetime],
):
    """Get saving plans for a period of time for each day of the month.

    Parameters
    ----------
    df : pl.DataFrame
        The DataFrame containing the stock data.
    invest_amount : int
        The amount of money to invest each month.
    period : Tuple[datetime.datetime, datetime.datetime]
        The period to consider for the calculations. It should contain two datetime objects.

    Yields
    ------
    SavingPlan
        A saving plan for each day of the month.
    """

    for day_to_invest in range(1, 32):
        saving_plan = SavingPlan(df, invest_amount, day_to_invest, period)
        yield saving_plan


def get_time_periods(df: pl.DataFrame, period_years=15) -> pl.DataFrame:
    """Get time periods of a fixed number of years."""

    return (
        (
            df.filter(pl.col("Date").dt.date() < datetime.datetime(2009, 9, 4)).select(
                pl.col("Date").alias("start"),
                pl.col("Date").dt.offset_by(f"{period_years}y").alias("end"),
            )
        )
        .collect()
        .to_numpy()
    )


def simulate(df: pl.DataFrame, time_periods: tuple, invest_amount: int):
    """Simulate the saving plans for each time period

    Args:
        df (pl.DataFrame): polars DataFrame
        time_periods (tuple): _description_
        invest_amount (int): _description_

    Yields:
        _type_: _description_
    """
    for period in time_periods:
        for day in range(1, 32):
            saving_plan = SavingPlan(
                df=df, invest_amount=invest_amount, day_to_invest=day, period=period
            )
            yield saving_plan


def write_simulation_result(
    df: pl.DataFrame, time_periods: tuple, invest_amount: int, path: Path
):
    """Simulate the saving plans for each time period

    Args:
        df (pl.DataFrame): polars DataFrame
        time_periods (tuple): _description_
        invest_amount (int): _description_

    Yields:
        _type_: _description_
    """
    all_day_dfs = []
    cnt = 0
    for period in time_periods:

        for day in range(1, 32):
            saving_plan = SavingPlan(
                df=df, invest_amount=invest_amount, day_to_invest=day, period=period
            )
            all_day_dfs.append(saving_plan.result_df)

            if cnt % 5000 == 0:
                logger.warning(f"Writing to parquet file: {cnt}")
                pl.concat(all_day_dfs).collect().write_parquet(
                    path / f"{str(cnt).zfill(4)}.parquet"
                )
                all_day_dfs = []
            cnt += 1


def get_last_day_of_month(year, month):
    # monthrange returns a tuple (first_weekday, number_of_days)
    last_day = calendar.monthrange(year, month)[1]
    return last_day


def get_all_possible_time_periods(
    df: pl.DataFrame,
    min_length: int = 20,
    step: int = 3,
):
    """Get all possible time periods from the given data frame. Where the time periods
    is a dynamic time window defined by the `min_length` and `step` parameters. The time
    window is moved by the `step` parameter.

    Args:
        df (pl.DataFrame): The data frame.
        min_length (int, optional): Minimum length of the time period. Defaults to 20.
        step (int, optional): The step in months to move the time window. Defaults to 3.
    """

    p_df = df.collect()

    min_date = p_df["Date"].dt.min()
    min_year = min_date.year
    min_month = min_date.month

    max_date = p_df["Date"].dt.max()
    max_year = max_date.year
    max_month = max_date.month

    all_year_month = []
    for y in range(min_year, max_year + 1):
        for m in range(1, 13):
            if y == min_year and m < min_month:
                continue
            elif y == max_year and m > max_month:
                continue
            else:
                all_year_month.append((y, m))

    time_periods = []
    for start in all_year_month[::step]:
        for end in all_year_month[::step]:
            length = (end[0] - start[0]) * 12 + end[1] - start[1]
            length_in_years = length / 12

            if length_in_years < min_length:
                continue
            else:
                start_ = datetime.datetime(start[0], start[1], 1)

                last_day = get_last_day_of_month(end[0], end[1])
                end_ = datetime.datetime(end[0], end[1], last_day)

                time_periods.append((start_, end_))

    return time_periods
