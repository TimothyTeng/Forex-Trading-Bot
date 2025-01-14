from decouple import config
import json
import v20
from constants import (
  HOST,
  STREAM_HOST,
  ACCESS_TOKEN,
  ACCOUNT_ID
)

# Connect to OANDA
def connect_v20():
  client = v20.Context(hostname=HOST, token=ACCESS_TOKEN, port=443)
  stream_client = v20.Context(hostname=STREAM_HOST, token=ACCESS_TOKEN, port=443)

  client.account.get(accountID=ACCOUNT_ID)
  response = client.account.get(accountID=ACCOUNT_ID)
  account = json.loads(response.body["account"].json())

  # Success message
  print("Connection Successful")
  print(f"Account ID: {account["id"]}")
  print(f"Account Balance: {account["balance"]}")

  return client