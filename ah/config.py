import os

from ah.defs import SECONDS_IN
from ah.fs import get_temp_path

BN_CLIENT_ID = os.environ("BN_CLIENT_ID")
BN_CLIENT_SECRET = os.environ("BN_CLIENT_SECRET")
DATA_BASE_PATH = get_temp_path()
APP_NAME = "ah"
MARKET_VALUE_RECORD_EXPIRES = 60 * SECONDS_IN.DAY
USE_COMPRESSION_FOR_STORAGE = True
