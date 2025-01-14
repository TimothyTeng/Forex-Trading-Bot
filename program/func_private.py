# Handling opening and closing positions
from constants import ACCOUNT_ID
import time
import json
from func_utils import format_number

# check order status
def check_order_status(client, order_id):
  order = json.loads(client.order.get(accountID=ACCOUNT_ID, ids=[order_id]).body.json())
  if order["order"]:
    return order.data["order"]["state"]

# Place market order
def place_market_order(client, market, side, size, price, reduce_only):
  amt = ("-" + size) if side == "SELL" else size[1:]
  print(amt, market, side, size, price, reduce_only)
  response = client.order.create(
    accountID=ACCOUNT_ID,
    order = {
      "units": amt,
      "instrument": market,
      "timeInForce": "FOK",
      "type": "MARKET",
      "priceBound": price,
      "positionFill": reduce_only
      }
    )
  return response



# Abort all open positions
def abort_all_positions(client):
  # Cancel all orders
  lst = client.order.list_pending(accountID=ACCOUNT_ID).body['orders']
  for order in lst:
    orderID = order['id']
    client.order.cancel(accountID=ACCOUNT_ID, orderSpecifier=orderID)
  
  # Protect the API
  time.sleep(0.5)

  all_positions = client.position.list_open(ACCOUNT_ID).body["positions"]

  # Handle open positions
  close_orders = []
  if len(all_positions) > 0:
    # Loop through each position
    for position in all_positions:
      positionData = json.loads(position.json())
      # Determine Market
      market = positionData["instrument"]

      # Determine Side
      side = "BUY"
      size = 0
      if float(positionData["long"]["units"]) > 0:
        side = "SELL"
        price = float(positionData["long"]["averagePrice"])
        size = positionData["long"]["units"]
      else:
        price = float(positionData["short"]["averagePrice"])
        size = positionData["short"]["units"]
      
      # Get Price
      accept_price = price * 1.7 if side == "BUY" else price * 0.3
      markets = json.loads(client.account.instruments(accountID=ACCOUNT_ID, instruments=market).body["instruments"][0].json())
      tickSize = markets["pipLocation"]
      accept_price = format_number(accept_price, tickSize)

      # Place order to close
      order = place_market_order(client, market, side, size, accept_price, "REDUCE_ONLY")

      # Append result to close orders
      close_orders.append(order)

      # Protect API
      time.sleep(0.1)
  
  # Return closed orders
  return close_orders

      
