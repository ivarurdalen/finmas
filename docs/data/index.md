# Data Sources

This is a list of the data sources that have been integrated in this app.
Those data sources that require an API Key are marked in the table.
Then it is necessary to set those as a environment variable which can
be done by copying the `.env.template` file in the root folder and
creating a `.env` file with the API keys.

| API Key                         | Name          | Type             | Description                                                       |
| ------------------------------- | ------------- | ---------------- | ----------------------------------------------------------------- |
|                                 | SEC / Edgar   | Filings          | Accessed via [edgartools](https://github.com/dgunning/edgartools) |
| <i class="fa-solid fa-key"></i> | Tiingo        | Price data       | Limited to 1000 calls per day.                                    |
| <i class="fa-solid fa-key"></i> | Benzinga      | News             | Requires registration of Alpaca account                           |
| <i class="fa-solid fa-key"></i> | Alpha Vantage | Fundamental data | Limited to 25 calls per day.                                      |
