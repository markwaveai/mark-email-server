from datetime import datetime, timedelta,timezone,time
import pytz
from enum import Enum

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

def get_date_time_ist(timeStamp, input_format='%d-%m-%Y %H:%M:%S', with_ist_timezone=True):
    # Define IST timezone
    IST = timezone(timedelta(hours=5, minutes=30))
    if with_ist_timezone:
        # Convert the timestamp to a datetime object in IST
        date_obj = datetime.fromtimestamp(timeStamp / 1000, IST)
    else:
        # Convert the timestamp to a naive datetime object (without timezone)
        date_obj = datetime.fromtimestamp(timeStamp / 1000)
    # Return the formatted date and time string
    return date_obj.strftime(input_format)
def get_epoch_time():
    return int(datetime.now().timestamp() * 1000)
def get_epoch_time_7pm():
    # Get today's date
    today = datetime.today()
    # Create a datetime object for 7 PM today
    seven_pm_today = datetime.combine(today, time(19, 0))
    # Convert to epoch time in milliseconds
    epoch_time_7pm = int(seven_pm_today.timestamp() * 1000)
    
    return epoch_time_7pm
    
                 
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
