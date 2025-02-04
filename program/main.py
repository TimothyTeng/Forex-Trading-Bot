from constants import ABORT_ALL_POSITIONS_EVENT, FIND_COINTEGRATED_EVENT, MANAGE_EXITS_EVENT, PLACE_TRADES_EVENT
from func_connections import connect_v20
from func_private import abort_all_positions
from func_public import construct_market_prices
from func_cointegration import store_cointegration_results
from func_entry_pairs import open_positions
from func_exit_pairs import manage_trade_exits
from func_messaging import send_message, start_telegram_bot, BOT_ACTIVE_EVENT
import threading
import time

def run_trading_logic():
  while True:
    BOT_ACTIVE_EVENT.wait()
    # Message on start
    send_message("Bot launch successful!")

    try:
      client = connect_v20()
    except Exception as e:
      print("Error connecting to client:", e)
      send_message(f"Failed to connect to client {e}")
      #exit(1)

    if ABORT_ALL_POSITIONS_EVENT.is_set():
      try:
        print("Aborting all positions...")
        send_message("Beginning aborting positions")
        close_orders = abort_all_positions(client)
      except Exception as e:
        print("Error aborting all positions:", e)
        send_message(f"Error closing all positions {e}")
        #exit(1)
      ABORT_ALL_POSITIONS_EVENT.clear()

    #Find Cointegrated pairs
    if FIND_COINTEGRATED_EVENT.is_set():
      #Construct market prices
      try:
        print("Fetching market prices. Please allow for 3-5 mins...")
        df_market_prices = construct_market_prices(client)

      except Exception as e:
        print("Error constructing market prices:", e)
        send_message(f"Error constructing market prices {e}")
        #exit(1)

      # Store cointegrated pairs
      try:
        print("Storing cointegrated pairs...")
        stores_result = store_cointegration_results(df_market_prices)
        if stores_result != "saved":
          print("Error saving cointegrated pairs")
          #exit(1)
      except Exception as e:
        print("Error saving cointegrated pairs:", e)
        send_message(f"Error saving cointegrated pairs {e}")
        #exit(1)
      
      FIND_COINTEGRATED_EVENT.clear()


    # Run as always on
    while BOT_ACTIVE_EVENT.is_set():

      # Place trades for opening positions
      if MANAGE_EXITS_EVENT.is_set():
        try:
          print("Managing exits...")
          manage_trade_exits(client)
          time.sleep(2)
        except Exception as e:
          print("Error managing exiting positions", e)
          send_message(f"Error managing exiting positions: {e}")
          #exit(1)

      # Place trades for opening positions
      if PLACE_TRADES_EVENT.is_set():
        try:
          print("Finding trading opportunities...")
          open_positions(client)
          time.sleep(2)
        except Exception as e:
          print("Error finding trading opportunities", e)
          send_message(f"Error open trades: {e}")
          #exit(1)

      #Find Cointegrated pairs
      if FIND_COINTEGRATED_EVENT.is_set():
        #Construct market prices
        try:
          print("Fetching market prices. Please allow for 3-5 mins...")
          df_market_prices = construct_market_prices(client)

        except Exception as e:
          print("Error constructing market prices:", e)
          send_message(f"Error constructing market prices {e}")
          #exit(1)

        # Store cointegrated pairs
        try:
          print("Storing cointegrated pairs...")
          stores_result = store_cointegration_results(df_market_prices)
          if stores_result != "saved":
            print("Error saving cointegrated pairs")
            #exit(1)
        except Exception as e:
          print("Error saving cointegrated pairs:", e)
          send_message(f"Error saving cointegrated pairs {e}")
          #exit(1)
        FIND_COINTEGRATED_EVENT.clear()
      
      if ABORT_ALL_POSITIONS_EVENT.is_set():
        try:
          print("Aborting all positions...")
          send_message("Beginning aborting positions")
          close_orders = abort_all_positions(client)
        except Exception as e:
          print("Error aborting all positions:", e)
          send_message(f"Error closing all positions {e}")
          #exit(1)
        ABORT_ALL_POSITIONS_EVENT.clear()

if __name__ == "__main__":
  # Start the trading logic in a separate thread
  trading_thread = threading.Thread(target=run_trading_logic, daemon=True)
  trading_thread.start()

  # Start the Telegram bot in the main thread
  try:
      start_telegram_bot()  # Ensure this runs in the main thread for asyncio compatibility
  except KeyboardInterrupt:
      print("Shutting down...")
      BOT_ACTIVE = False
      trading_thread.join()
    