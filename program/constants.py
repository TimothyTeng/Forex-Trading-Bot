from decouple import config

#Connect to the test network for OANDA
TEST_HOST = "api-fxpractice.oanda.com"
TEST_STREAM_HOST = "stream-fxpractice.oanda.com"

#Connect to the main network for OANDA
MAIN_HOST = "api-fxtrade.oanda.com"
MAIN_STREAM_HOST = "stream-fxtrade.oanda.com"

# MODE OF PRODUCTION
MODE = "DEVELOPMENT"

#Close all open postions and orders
ABORT_ALL_POSITIONS = False

#Find Cointegrated Pairs
FIND_COINTEGRATED = True

#Place trades
PLACE_TRADES = True

# Resolution
RESOLUTION = "1HOUR"

# Stats Window -- HOW MANY DAYS WE CHECK
WINDOW = 21

# Thresholds - Opening
MAX_HALF_LIFE = 24
ZSCORE_THRESH = 1.5
USD_PER_TRADE = 50
# Amount inside your account - To ensure bots do not go above amount in account
USD_MIN_COLLATERAL = 1000

# Thresholds - Closing
CLOSE_AT_ZSCORE_CROSS = True

#Keys to connect to OANDA test account
TEST_ACCESS_TOKEN = config("TEST_ACCESS_TOKEN")
TEST_ACCOUNT_ID = config("TEST_ACCOUNT_ID")

#Keys to connect to OANDA main account
MAIN_ACCESS_TOKEN = config("MAIN_ACCESS_TOKEN")
MAIN_ACCOUNT_ID = config("MAIN_ACCOUNT_ID")

#Keys - Export
ACCESS_TOKEN = MAIN_ACCESS_TOKEN if MODE == "PRODUCTION" else TEST_ACCESS_TOKEN
ACCOUNT_ID = MAIN_ACCOUNT_ID if MODE == "PRODUCTION" else TEST_ACCOUNT_ID

#Host - Export
HOST = MAIN_HOST if MODE == "PRODUCTION" else TEST_HOST
STREAM_HOST = MAIN_STREAM_HOST if MODE == "PRODUCTION" else TEST_STREAM_HOST