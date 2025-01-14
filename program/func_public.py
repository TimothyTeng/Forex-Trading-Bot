import numpy as np
import pandas as pd
from constants import RESOLUTION,ACCOUNT_ID
from func_utils import get_ISO_times
from pprint import pprint
import time
import json

ISO_TIMES = get_ISO_times()


# Get candles recent
def get_candles_recent(client, market):

  # Define output
  close_prices = []

  # Protect API
  time.sleep(0.2)

  # Get data
  candles = client.instrument.candles(
      instrument=market,
      granularity=RESOLUTION
    )
  
  # Structure data
  for candle in candles.body["candles"]:
    c = json.loads(candle.json())
    close_prices.append(c["mid"]["c"])
  
  # Construct and return close price series
  prices_result = np.array(close_prices).astype(float)
  return prices_result

# Get candles historical
def get_candles_historical(client, market):
  close_prices = []

  # Extract historical price data for each timeframe
  for timeframe in ISO_TIMES.keys():

    # Confirm times needed
    tf_obj = ISO_TIMES[timeframe]
    from_iso = tf_obj["from_iso"]
    to_iso = tf_obj["to_iso"]
    
    #protect API
    time.sleep(0.2)
    
    #Get data
    candles = client.instrument.candles(
      instrument=market,
      from_time=from_iso,
      to_time=to_iso,
      granularity=RESOLUTION
    )

    for candle in candles.body["candles"]:
      c = json.loads(candle.json())
      close_prices.append({"datetime": c["time"], market:c["mid"]["c"]})

  # Construct and return dataframe
  return close_prices



def construct_market_prices(client):
  
  # Declare variables
  tradable_markets = []
  markets = client.account.instruments(accountID=ACCOUNT_ID)

  # Find tradable pairs
  for market in markets.body['instruments']:
    market_info = json.loads(market.json())
    if market_info["type"] == "CURRENCY":
      tradable_markets.append(market_info["name"])

  # Set initial DataFame
  close_prices = get_candles_historical(client, tradable_markets[0])
  df = pd.DataFrame(close_prices)
  df.set_index("datetime", inplace=True)

  # Append other prices to Dataframe
  # You can limit the amount to loop through here to save time in development
  for market in tradable_markets[1:]:
    close_prices_add = get_candles_historical(client, market)
    df_add = pd.DataFrame(close_prices_add)
    df_add.set_index("datetime", inplace=True)
    df = pd.merge(df, df_add, how="outer", on="datetime", copy=False)
    del df_add

  df.dropna(inplace=True)
  
  # Check any columns with NaNs
  # nans = df.columns[df.isna().any()].tolist()
  # if len(nans) > 0:
  #  print("Dropping columns: ")
  #  print(nans)
  #  df.drop(columns=nans, inplace=True)
  
  # Return result
  return df
