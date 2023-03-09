import os

from ah.defs import SECONDS_IN
from ah.fs import get_temp_path

BN_CLIENT_ID = os.environ.get("BN_CLIENT_ID")
BN_CLIENT_SECRET = os.environ.get("BN_CLIENT_SECRET")
TEMP_PATH = get_temp_path()
DEFAULT_DB_PATH = os.path.join(TEMP_PATH, "ah_db")
DEFAULT_EXPORT_PATH = os.path.join(TEMP_PATH, "ah_export.lua")
APP_NAME = "ah"
MARKET_VALUE_RECORD_EXPIRES = 60 * SECONDS_IN.DAY
REGIONS = ["us", "eu", "kr", "tw"]
LOGGING_LEVEL = os.environ.get("LOGGING_LEVEL", "INFO")
