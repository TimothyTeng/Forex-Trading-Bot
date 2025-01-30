import pandas as pd
import time
from func_cointegration import calculate_cointegration
from func_utils import get_ISO_times
import numpy as np
import matplotlib.pyplot as plt
import v20
import json
from constants import HOST, ACCESS_TOKEN, ACCOUNT_ID, RESOLUTION


# Parameters
WINDOW = 21
ZSCORE_ENTRY_THRESHOLD = 1
ZSCORE_EXIT_THRESHOLD = 0
INITIAL_CAPITAL = 2000
POSITION_SIZE = 100
TRANSACTION_COST = 0.01
COINTEGRATED_RESET = 72

def calculate_zscore(spread):
  spread_series = pd.Series(spread)
  mean = spread_series.rolling(center=False, window=WINDOW).mean()
  std = spread_series.rolling(center=False, window=WINDOW).std()
  x = spread_series.rolling(center=False, window=1).mean()
  zscore = (x - mean) / std
  return zscore

def get_candlestick_data():
    client = v20.Context(hostname=HOST, token=ACCESS_TOKEN, port=443)
    ISO_TIMES = get_ISO_times(3000)
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
          count=3000,
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
      
      return df
    return construct_market_prices(client)
    
pivot_data = None
try:
    pivot_data = pd.read_csv('backtestingCandlestick.csv')
    pivot_data.set_index("datetime", inplace=True)
except:
    print("No data found")
    pivot_data = get_candlestick_data()
    pivot_data.to_csv('backtestingCandlestick.csv')
    

def find_cointegrated_pairs(data):
    pairs = []
    instruments = data.columns
    for i, base_instrument in enumerate(instruments[:-1]):
        for j, quote_instrument in enumerate(instruments[i + 1:]):
            series_1 = data[base_instrument]
            series_2 = data[quote_instrument]
            coint_flag, hedge_ratio, half_life = calculate_cointegration(series_1, series_2)

            if coint_flag and half_life > 0:
                pairs.append({
                    "base_instrument": base_instrument,
                    "quote_instrument": quote_instrument,
                    "hedge_ratio": hedge_ratio,
                    "half_life": half_life
                })
    return pairs

# Perform backtesting
def backtest(data):
    capital = INITIAL_CAPITAL
    equity_curve = []
    positions = []
    day_prices = {}
    hour_counter = 0
    pairs = []
    opened_instrument = set()
    buyCount = 0
    sellCount = 0

    # Goes through each date in the dataframe
    for date in data.index:
        # Extracts the prices at that specific date and time
        prices = data.loc[date]
        instrument_names = prices.index
        unrealized_pnl = 0

        # Collecting the sufficient data for the zscore with 500 hours
        if hour_counter < 500:
            for i, name in enumerate(instrument_names):
                if name in day_prices.keys():
                    day_prices[name].append(prices.iloc[i])
                else:
                    day_prices[name] = [prices.iloc[i]]
            hour_counter += 1
        else:
            # Keep the number of data to 500
            for i, name in enumerate(instrument_names):
                day_prices[name].append(prices.iloc[i])
                day_prices[name].pop(0)
            # Check for new pairs
            end_window = data.index[hour_counter - 1]
            start_window = data.index[hour_counter - 500]
            temp_df = data.loc[start_window:end_window]
            if (hour_counter % COINTEGRATED_RESET) == 0 or hour_counter == 500:
                pairs = find_cointegrated_pairs(temp_df)
            

            # Check for exit positions
            for position in positions[:]:  # Iterate over a copy to allow modification
                base, quote = position["pair"]
                series_1 = np.array(day_prices[base]).astype(float)
                series_2 = np.array(day_prices[quote]).astype(float)
                # Calculate z-score
                if len(series_1) > 0 and len(series_1) == len(series_2):
                    spread = series_1 - (hedge_ratio * series_2)
                    z_score = calculate_zscore(spread).values.tolist()[-1]

                z_score_level_check = abs(z_score) >= abs(position["entry_z_score"])
                z_score_cross_check = (z_score < 0 and position["entry_z_score"] > 0) or (z_score > 0 and position["entry_z_score"] < 0)
                
                if z_score_level_check and z_score_cross_check:
                    # Close position
                    exit_base_price = day_prices[base][-1]
                    exit_quote_price = day_prices[quote][-1]
                    exit_base_quantity = position["base_quantity"]
                    exit_quote_quantity = position["quote_quantity"]
                    entry_base_price = position["base_price"]
                    entry_quote_price = position["quote_price"]
                    entry_base_quantity = position["base_quantity"]
                    entry_quote_quantity = position["quote_quantity"]
                    if exit_base_quantity != 0 and exit_quote_quantity != 0:
                        base_pnl = exit_base_price * exit_base_quantity - entry_base_price * entry_base_quantity
                        quote_pnl = exit_quote_price * exit_quote_quantity - entry_quote_price * entry_quote_quantity
                        pnl = (base_pnl - quote_pnl) if position["type"] == "long" else (quote_pnl - base_pnl)
                        pnl -= 0.01  # Subtract transaction costs
                        sellCount += 1
                        print(f"SOLD: {base} & {quote} half-life of {position["half_life"]}")

                        capital += pnl
                        opened_instrument.remove(base)
                        opened_instrument.remove(quote)
                        positions.remove(position)
                
                else:
                    exit_base_price = day_prices[base][-1]
                    exit_quote_price = day_prices[quote][-1]
                    exit_base_quantity = position["base_quantity"]
                    exit_quote_quantity = position["quote_quantity"]
                    entry_base_price = position["base_price"]
                    entry_quote_price = position["quote_price"]
                    entry_base_quantity = position["base_quantity"]
                    entry_quote_quantity = position["quote_quantity"]
                    if exit_base_quantity != 0 and exit_quote_quantity != 0:
                        base_pnl = exit_base_price * exit_base_quantity - entry_base_price * entry_base_quantity
                        quote_pnl = exit_quote_price * exit_quote_quantity - entry_quote_price * entry_quote_quantity
                        pnl = (base_pnl - quote_pnl) if position["type"] == "long" else (quote_pnl - base_pnl)
                        pnl -= 0.01  # Subtract transaction costs
                        unrealized_pnl += pnl


            # Check for pairs and z_score
            for pair in pairs:
                base = pair["base_instrument"]
                quote = pair["quote_instrument"]
                hedge_ratio = pair["hedge_ratio"]
                half_life = pair["half_life"]
                # Get the 2 float series
                series_1 = np.array(day_prices[base]).astype(float)
                series_2 = np.array(day_prices[quote]).astype(float)
                # Calculate z-score
                if len(series_1) > 0 and len(series_1) == len(series_2):
                    spread = series_1 - (hedge_ratio * series_2)
                    z_score = calculate_zscore(spread).values.tolist()[-1]

                    if base not in opened_instrument and quote not in opened_instrument:
                        base_price = day_prices[base][-1]
                        quote_price = day_prices[quote][-1]
                        base_quantity = int(1 / base_price * POSITION_SIZE)
                        quote_quantity = int(1 / quote_price * POSITION_SIZE)
                        if z_score > ZSCORE_ENTRY_THRESHOLD:
                            positions.append({
                                "pair": (base, quote),
                                "type": "short",
                                "entry_date": date,
                                "entry_spread": spread[-1],
                                "entry_z_score": z_score,
                                "base_price":base_price,
                                "quote_price": quote_price,
                                "base_quantity": base_quantity,
                                "quote_quantity": quote_quantity,
                                "half_life": half_life
                            })
                            opened_instrument.add(base)
                            opened_instrument.add(quote)

                        elif z_score < -ZSCORE_ENTRY_THRESHOLD:
                            # Enter long spread
                            positions.append({
                                "pair": (base, quote),
                                "type": "long",
                                "entry_date": date,
                                "entry_spread": spread[-1],
                                "entry_z_score": z_score,
                                "base_price":base_price,
                                "quote_price": quote_price,
                                "base_quantity": base_quantity,
                                "quote_quantity": quote_quantity,
                                "half_life": half_life
                            })
                            opened_instrument.add(base)
                            opened_instrument.add(quote)
                        buyCount += 1
                        print(f"BOUGHT: {base} & {quote}")
                            

            capital += unrealized_pnl
            equity_curve.append({"date": date, "capital": capital})
            print(f"Hour {hour_counter}, NAV of {capital}")
            capital -= unrealized_pnl
            # Move to the next hour
            hour_counter += 1
    print(f"Sold: {sellCount}, Bought: {buyCount}, Sell percentage: {sellCount/buyCount}")
    return pd.DataFrame(equity_curve), sellCount, buyCount



results, sellCount, buyCount = backtest(pivot_data)
WINDOW = 28
result2, sellCount2, buyCount2 = backtest(pivot_data)
WINDOW = 21
ZSCORE_ENTRY_THRESHOLD = 1.5
result3, sellCount3, buyCount3 = backtest(pivot_data)
ZSCORE_ENTRY_THRESHOLD = 2
result4, sellCount4, buyCount4 = backtest(pivot_data)
ZSCORE_ENTRY_THRESHOLD = 2.5
result5, sellCount5, buyCount5 = backtest(pivot_data)
ZSCORE_ENTRY_THRESHOLD = 1
POSITION_SIZE = 200
result6, sellCount6, buyCount6 = backtest(pivot_data)
ZSCORE_ENTRY_THRESHOLD = 1
POSITION_SIZE = 400
result7, sellCount7, buyCount7 = backtest(pivot_data)



results.set_index("date").plot(y="capital", title="Equity Curve", xlabel="Date", ylabel="Capital")
plt.show()
result2.set_index("date").plot(y="capital", title="Equity Curve", xlabel="Date", ylabel="Capital")
plt.show()
result3.set_index("date").plot(y="capital", title="Equity Curve", xlabel="Date", ylabel="Capital")
plt.show()
result4.set_index("date").plot(y="capital", title="Equity Curve", xlabel="Date", ylabel="Capital")
plt.show()
result5.set_index("date").plot(y="capital", title="Equity Curve", xlabel="Date", ylabel="Capital")
plt.show()
result6.set_index("date").plot(y="capital", title="Equity Curve", xlabel="Date", ylabel="Capital")
plt.show()
result7.set_index("date").plot(y="capital", title="Equity Curve", xlabel="Date", ylabel="Capital")
plt.show()

print(sellCount, buyCount)
print(sellCount2, buyCount2)
print(sellCount3, buyCount3)
print(sellCount4, buyCount4)
print(sellCount5, buyCount5)
print(sellCount6, buyCount6)
print(sellCount7, buyCount7)