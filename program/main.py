from constants import ABORT_ALL_POSITIONS, FIND_COINTEGRATED
from func_connections import connect_v20
from func_private import abort_all_positions
from func_public import construct_market_prices

if __name__ == "__main__":
  try:
    client = connect_v20()
  except Exception as e:
    print(e)
    print("Error connecting to client:", e)
    exit(1)

  if ABORT_ALL_POSITIONS:
    try:
      print("Aborting all positions...")
      close_orders = abort_all_positions(client)
    except Exception as e:
      print(e)
      print("Error aborting all positions:", e)
      exit(1)

  #Find Cointegrated pairs
  if FIND_COINTEGRATED:
    #Construct market prices
    try:
      print("Fetching market prices. Please allow for 3-5 mins...")
      df_market_prices = construct_market_prices(client)

    except Exception as e:
      print(e)
      print("Error aborting all positions:", e)
      exit(1)