import datetime
import sys

# Get the current time in UTC
utc_now = datetime.datetime.now(datetime.timezone.utc)

# Format in ISO 8601
iso_format_time = utc_now.isoformat()

# Print to standard output
print(iso_format_time)
sys.exit(0) 