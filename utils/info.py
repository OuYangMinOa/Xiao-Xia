from datetime import datetime
from utils.MyLog     import create_logger


music_user  = {}
User_dict   = {}  ##   {userid : userclass }k
PASS_MSG    = []
MASSAGE_DATA = "data/message_collect.txt"
silinece_channel = []

dir_path = 'logs'
logger = create_logger(dir_path)	
