import numpy as np
import pandas as pd
from constants import RESOLUTION
from func_utils import get_ISO_times
from pprint import pprint
import time

ISO_TIMES = get_ISO_times()

print(ISO_TIMES)

def construct_market_prices(client):
  pass