import datetime as dt
import os

import pandas as pd
from dotenv import find_dotenv, load_dotenv
from tiingo import TiingoClient

from finmas.cache_config import cache
from finmas.logger import get_logger
from finmas.utils.common import date_to_str

load_dotenv(find_dotenv())

logger = get_logger(__name__)


@cache.memoize(expire=dt.timedelta(days=1).total_seconds())
def get_price_data(ticker: str, start: dt.date | str, end: dt.date | str) -> pd.DataFrame:
    """
    Get historical price data for a given stock ticker.

    Args:
        ticker: The stock ticker symbol.
        start: The start date for the historical data.
        end: The end date for the historical data.
    """
    if os.getenv("TIINGO_API_KEY") is None:
        logger.error("TIINGO_API_KEY environment variable not set.")
        return pd.DataFrame()

    start, end = date_to_str(start), date_to_str(end)

    client = TiingoClient({"session": True, "api_key": os.getenv("TIINGO_API_KEY")})

    df = client.get_dataframe(
        ticker,
        startDate=start,
        endDate=end,
    )

    df.columns = df.columns.str.lower()
    assert isinstance(df.index, pd.DatetimeIndex)
    df.index = df.index.tz_localize(None)
    return df
