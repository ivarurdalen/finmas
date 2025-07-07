import os
from pathlib import Path

import pandas as pd
from alpha_vantage.fundamentaldata import FundamentalData

from finmas.constants import defaults
from finmas.logger import get_logger, log_execution_time

logger = get_logger(__name__)


@log_execution_time(logger)
def get_fundamental_data(ticker: str, type: str, freq: str) -> pd.DataFrame:
    """
    Return fundamental data for a given ticker using Alpha Vantage as data source.

    The full historical data is returned.

    Args:
        ticker: The stock ticker
        type: The type of the data. Either "income", "balance", "cash_flow" or "earnings"
        freq: The frequency of the data. Either "Annual" or "Quarterly"
    """
    if type not in ["income", "balance", "cash_flow", "earnings"]:
        raise ValueError(f"Invalid type '{type}'")
    if freq not in ["Annual", "Quarterly"]:
        raise ValueError(f"Invalid frequency '{freq}'")

    fundamentals_dir = Path(defaults["data_dir"]) / "fundamentals" / ticker
    fundamentals_dir.mkdir(parents=True, exist_ok=True)
    file_path = fundamentals_dir / f"{type}_{freq.lower()}.csv"
    if file_path.exists():
        logger.info(f"Reading {type} data for '{ticker}' from '{str(file_path)}'")
        return pd.read_csv(file_path, index_col=0, parse_dates=True)

    if os.getenv("ALPHAVANTAGE_API_KEY") is None:
        logger.error("ALPHAVANTAGE_API_KEY environment variable not set.")
        return pd.DataFrame()
    fundamentals = FundamentalData(output_format="pandas")

    data_func_map = {
        "income": {
            "Annual": fundamentals.get_income_statement_annual,
            "Quarterly": fundamentals.get_income_statement_quarterly,
        },
        "balance": {
            "Annual": fundamentals.get_balance_sheet_annual,
            "Quarterly": fundamentals.get_balance_sheet_quarterly,
        },
        "cash_flow": {
            "Annual": fundamentals.get_cash_flow_annual,
            "Quarterly": fundamentals.get_cash_flow_quarterly,
        },
        "earnings": {
            "Annual": fundamentals.get_earnings_annual,
            "Quarterly": fundamentals.get_earnings_quarterly,
        },
    }

    data_func = data_func_map.get(type, {}).get(freq)
    if type not in data_func_map or data_func is None:
        raise ValueError(f"Invalid type '{type}' or frequency '{freq}'")

    try:
        df: pd.DataFrame = data_func(ticker)[0]
    except Exception as e:
        print(e)
        return pd.DataFrame()

    df.set_index("fiscalDateEnding", inplace=True)
    df.index = pd.to_datetime(df.index)
    df.sort_index(inplace=True)
    if "reportedCurrency" in df.columns:
        df.drop(columns=["reportedCurrency"], inplace=True)

    df = df.apply(pd.to_numeric, errors="coerce")

    df = df.dropna(axis=1, how="all")

    if defaults["save_fundamental_data"]:
        df.to_csv(file_path)
        logger.info(f"{type.title()} data for '{ticker}' stored in '{str(file_path)}'")

    return df


def get_income_statement_df(ticker: str, freq: str, cols: list[str] | None = None) -> pd.DataFrame:
    """
    Return the income statements as a DataFrame for a given ticker.

    The DataFrame is wrangled and adds the net profit margin as a new column.

    Args:
        ticker: The stock ticker
        freq: The frequency of the data. Either "Annual" or "Quarterly"
        cols: The columns to return. If None, all columns are returned
    """
    df = get_fundamental_data(ticker=ticker, type="income", freq=freq)

    if not isinstance(df, pd.DataFrame) or df.empty:
        return pd.DataFrame()
    if cols:
        df = df[cols]

    df["netProfitMargin"] = df["netIncome"] / df["totalRevenue"]
    return df
