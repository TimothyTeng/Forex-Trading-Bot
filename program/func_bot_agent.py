from func_private import place_market_order, check_order_status
from datetime import datetime, timedelta
import time

from pprint import pprint

# Class: Agent for managing opening and closing trades
class BotAgent:

  """
    Primary function of BotAgent handles opening and checking order status
  """


  def __init__(
      self,
      client,
      market_1,
      market_2,
      base_side,
      base_size,
      base_price,
      quote_side,
      quote_size,
      quote_price,
      accept_failsafe_base_price,
      z_score,
      half_life,
      hedge_ratio,
    ):

    #Initialize class variables
    self.client = client
    self.market_1 = market_1
    self.market_2 = market_2
    self.base_side = base_side
    self.base_size = base_size
    self.base_price = base_price
    self.quote_side = quote_side
    self.quote_size = quote_size
    self.quote_price = quote_price
    self.accept_failsafe_base_price = accept_failsafe_base_price
    self.z_score = z_score
    self.half_life = half_life
    self.hedge_ratio = hedge_ratio

    # Initialise output variable
    # Pair status options are FAILED, LIVE, CLOSE, ERROR
    self,order_dict = {
      "market_1": market_1,
      "market_2": market_2,
      "hedge_ratio": hedge_ratio,
      "z-score": z_score,
      "half_life": half_life,
      "order_id_m1": "",
      "order_m1_size": base_size,
      "order_m1_side": base_side,
      "order_time_m1": "",
      "order_id_m2": "",
      "order_m2_size": quote_size,
      "order_m2_side": quote_side,
      "order_time_m2": "",
      "pair_status": "",
      "comments": "",
    }
