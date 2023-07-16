from datetime import datetime
from utils.MyLog     import create_logger
from utils.file_os import *

music_user  = {}  ## handle music  {channel id: class}
sound_user  = {}  ## handle sound  {channel id: class}
User_dict   = {}  ##   {userid : userclass }k
PASS_MSG    = []
MASSAGE_DATA = "data/message_collect.txt"
Silence_DATA = "data/silence_channel.txt"
silinece_channel = readfile(Silence_DATA,int)

dir_path = 'logs'
logger = create_logger(dir_path)	
