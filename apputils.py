from datetime import datetime, timedelta,timezone,time
import pytz
from enum import Enum
def validate_date_format(date_string, required_format='%d-%m-%Y'):
    try:
        # Attempt to parse the date string using the required format
        datetime.strptime(date_string, required_format)
        return True  # If successful, the date string is valid and correctly formatted
    except ValueError:
        # If parsing fails, the date string is either incorrectly formatted or invalid
        return False
def get_formatted_date(input_date_string,input_format = '%d-%m-%Y',output_format = '%B %d, %Y'):    
    # Parse the input date string to a datetime object
    date_obj = datetime.strptime(input_date_string, input_format)
    # Format the datetime object to the desired output format
    return date_obj.strftime(output_format)

def get_yesterday_date_string_in_ist(input_format='%d-%m-%Y'):
    timezone = pytz.timezone('Asia/Kolkata')
    yesterday = datetime.now(timezone) - timedelta(days=1)
    return yesterday.strftime(input_format)

def get_today_date_string_in_ist(out_put_format='%d-%m-%Y'):
    timezone = pytz.timezone('Asia/Kolkata')
    today = datetime.now(timezone)
    return today.strftime(out_put_format)

def get_today_date_string(out_put_format='%d-%m-%Y'):
    today = datetime.now()
    return today.strftime(out_put_format)

def get_today_date_time_in_ist(out_put_format='%d-%m-%Y %H:%M:%S'):
    timezone = pytz.timezone('Asia/Kolkata')
    today = datetime.now(timezone)
    return today.strftime(out_put_format)

def get_day_start_end_epoch_in_ist(date_str, date_format="%d-%m-%Y"):
    IST = timezone(timedelta(hours=5, minutes=30))
    start_date = datetime.strptime(date_str, date_format).replace(tzinfo=IST)
    start_epoch = int(start_date.timestamp() * 1000)
    end_date = start_date + timedelta(days=1) - timedelta(seconds=1)
    end_epoch = int(end_date.timestamp() * 1000)
    return start_epoch, end_epoch

def get_day_start_end_epoch(date_str, date_format="%d-%m-%Y",is13digit=True):
    # Parse the input date
    start_date = datetime.strptime(date_str, date_format)
    # Calculate the start of the day at 00:00:00 AM
    start_epoch = int(start_date.timestamp() * 1000)
    if is13digit==False:
       start_epoch = int(start_date.timestamp()) 
    # Calculate the end of the day at 23:59:59 PM
    end_date = start_date + timedelta(days=1) - timedelta(seconds=1)
    end_epoch = int(end_date.timestamp() * 1000)
    if is13digit==False:
       end_epoch = int(end_date.timestamp())

    return start_epoch, end_epoch

def get_date_time_ist(timeStamp, output_format='%d-%m-%Y %H:%M:%S', with_ist_timezone=True):
    # Define IST timezone
    IST = timezone(timedelta(hours=5, minutes=30))
    if with_ist_timezone:
        # Convert the timestamp to a datetime object in IST
        date_obj = datetime.fromtimestamp(timeStamp / 1000, IST)
    else:
        # Convert the timestamp to a naive datetime object (without timezone)
        date_obj = datetime.fromtimestamp(timeStamp / 1000)
    # Return the formatted date and time string
    return date_obj.strftime(output_format)
def get_epoch_time():
    return int(datetime.now().timestamp() * 1000)
# def get_epoch_time():
#     return int(datetime.now().timestamp() * 1000)

def get_epoch_time_pm(date, pmtime=19,date_format='%d-%m-%Y'):
    # Parse the given date string into a datetime object
    given_date = datetime.strptime(date, date_format)
    # Create a datetime object for 7 PM on the given date
    seven_pm_given_date = datetime.combine(given_date, time(pmtime, 0))
    # Convert to epoch time in milliseconds
    epoch_time_pm = int(seven_pm_given_date.timestamp() * 1000)
    return epoch_time_pm

def get_epoch_time_for_date_with_current_time(date, date_format='%d-%m-%Y'):
    # Parse the given date string into a datetime object
    given_date = datetime.strptime(date, date_format).date()
    # Get the current time
    current_time = datetime.now().time()
    # Combine the given date with the current time
    combined_datetime = datetime.combine(given_date, current_time)
    # Convert to epoch time in milliseconds
    epoch_time = int(combined_datetime.timestamp() * 1000)
    return epoch_time

def check_epoch_isToday(epoch):
    # Convert the epoch to a datetime object and extract the date
    date_time = datetime.fromtimestamp(epoch).date()
    # Get today's date
    today = datetime.today().date()
    # Check if the date of the epoch matches today's date
    return date_time == today

def check_epoch_is_given_date(epoch, date, date_format='%d-%m-%Y'):
    # Convert the epoch to a datetime object and extract the date
    date_time = datetime.fromtimestamp(epoch).date()
    # Parse the given date string into a datetime object and extract the date
    given_date = datetime.strptime(date, date_format).date()
    # Compare the date components of both dates
    return date_time == given_date

def check_date_isToday(date, date_format='%d-%m-%Y'):
    # Convert the input date string to a datetime object
    date_time = datetime.strptime(date, date_format).date()
    # Get today's date
    today = datetime.today().date()
    # Check if the given date matches today's date
    return date_time == today


                 
class TableTypes(Enum):
    CROP_TABLE = "cropTable"
    STOCKING_TABLE = "stockingTable"
    SHIFTING_TABLE = "shiftingTable"
    FEED_TABLE = "feedtable"
    CHECK_TRAY = "checkTray"
    NETTING_TABLE = "nettingTable"
    HARVEST_TABLE = "harvestTable"
    WATER_REMAINDER = "WaterRemainder"
    FEED_REMAINDER = "FeedRemainder"
    MEAL_TABLE = "mealTable"
    PRO_BREW_TABLE = "proBrewTable"
    WEIGHING_MACHINE_TABLE = "weighingMachineTable"
    IMAGE = "Image"
    VIDEO = "Video"
    DOCUMENT = "Document"
    SCHEDULE = "Schedule"
    FEED_SCHEDULE = "feed_schedule"
    MEAL_TIMING_TABLE = "mealTimingTable"
    CHECKTRAY_TIMING_TABLE = "checktrayTimingTable"
    REPORT_COMMENT = "reportComment"
    NEXT_MEAL_ALERT = "nextMealAlert"
    INSTRUCTIONS = "Instructions"
    PH_TABLE = "phtable"
    DO_TABLE = "dotable"
    CHECKTRAY_CHANGE = "checkTray_change"
    VERIFIED_FEED = "verified_feed"
    CHECKTRAY_REPLY = "checktray_reply"
    FEED_VERIFICATION = "feed_verification"
    SMART_SCALE_WEIGHING_TABLE = "smartScaleWeighingTable"
    AQUABOT = "aquabotTable"
    WATER_PARAMETER = "WaterParameter"
    DAY_FEED_TABLE = "dayfeedtable"
