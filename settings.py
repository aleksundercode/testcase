import os
from dotenv import load_dotenv

load_dotenv()
APP_NAME = 'ExnessTestApp'
DATA_PATH = 'data/'
LOGDRIVER = os.environ.get("LOGDRIVER", "FILE")
if LOGDRIVER not in ['FILE', 'SQLLITE']:
    LOGDRIVER = 'FILE'
LOGFILE_NAME = DATA_PATH + os.environ.get("LOGFILE_NAME", "log.txt")
SQLLITE_DBNAME = DATA_PATH + os.environ.get("SQLLITE_DBNAME", "ExnessTestApp.db")