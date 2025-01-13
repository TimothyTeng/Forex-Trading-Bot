from datetime import datetime, timedelta

# Format number
def format_number(curr_num, match_decimals):
  """
    Give current number an example with decimals desired
    Function will return correctly formatted string
  """

  if match_decimals < 0:
    decimal_places = abs(match_decimals)  # Convert -4 to 4
    formatted_num = f"{curr_num:.{decimal_places}f}"
    return formatted_num
  else:
    # If match_decimals is not negative, return integer representation
    return f"{int(curr_num)}"
  
def format_time(timestamp):
  return timestamp.replace(microsecond=0).isoformat()

def get_ISO_times():
  #Get time stamps
  date_start = datetime.now()
  date_end = date_start - timedelta(days=16)
  times_dict = {
    "range_1": {
      "from_iso": format_time(date_start),
      "to_iso": format_time(date_end)
    }
  }
  return times_dict