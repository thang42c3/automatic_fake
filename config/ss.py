from datetime import datetime
import pytz
def convert_datetime_timezone(dt, tz1, tz2):
    tz1 = pytz.timezone(tz1)
    tz2 = pytz.timezone(tz2)

    dt = datetime.strptime(dt,"%Y:%m:%d %H:%M:%S")
    dt = tz1.localize(dt)
    dt = dt.astimezone(tz2)
    dt = dt.strftime("%Y:%m:%d %H:%M:%S")

    return dt

def run_schedule(hour, minute):
    time_now = datetime.today().strftime('%Y:%m:%d')+ " " + str(hour) + ":" + str(minute) + ":" + "00"
    time_now = convert_datetime_timezone(time_now, 'Asia/Jakarta', "UTC")
    print(time_now[11:16])

run_schedule(1,0)


