from datetime import datetime
from utils.MyLog     import create_logger
from utils.file_os import *

music_user  = {}  ## handle music  {channel id: class}
sound_user  = {}  ## handle sound  {channel id: class}
User_dict   = {}  ##   {userid : userclass }k
PASS_MSG    = []
chat_dict   = {}  ## handle chat   {channel id:class}

MASSAGE_DATA   = "data/message_collect.txt"
Silence_DATA   = "data/silence_channel.txt"
MASSAGE_FOLDER = "data/message"
XioaXiaContent = "你現在是一個來自台灣discord機器人,名字叫歐陽小俠,你有撥放音樂、自訂義音樂版、查詢天氣、聊天等功能,`/help_zhtw`跟`/help_en`可以叫出你的幫助頁面。"
XioaXiaName    = "歐陽小俠"

MASSAGE_MEMORY_SIZE = 50
silinece_channel = readfile(Silence_DATA,int)

dir_path = 'logs'
logger = create_logger(dir_path)	
