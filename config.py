import logging
from logging.handlers import RotatingFileHandler
import os

database = "wards_2006"
db_host = "localhost"
db_user = "wards"
db_password = "wards"
code_dir = "/var/www/wards.code4sa.org"
env_dir = "/home/adi/.virtualenvs/a2w"
python = "%s/bin/python" % env_dir
pip = "%s/bin/pip" % env_dir
google_key = "AIzaSyB70Y_kdJcaqKXPrRYXdkCGqWnNxC28LPE"


# load log level from config
LOG_LEVEL = logging.DEBUG
LOGGER_NAME = "address2ward"

# create logger for this application
logger = logging.getLogger(LOGGER_NAME)
logger.setLevel(LOG_LEVEL)

# declare format for logging to file
file_formatter = logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s '
    '[in %(pathname)s:%(lineno)d]'
)

log_path = os.path.dirname(os.path.realpath(__file__))
file_handler = RotatingFileHandler(os.path.join(log_path, 'debug.log'))
file_handler.setLevel(LOG_LEVEL)
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)
