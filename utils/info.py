from utils.MyLog     import create_logger
from utils.file_os import *

music_user  = {}  ## handle music  {channel id: class}
sound_user  = {}  ## handle sound  {channel id: class}
User_dict   = {}  ##   {userid : userclass }k
PASS_MSG    = []  ## handle pass message (abandoned)
chat_dict   = {}  ## handle chat   {channel id:class}
recording   = {}  ## handle recording {guild id:class}

CheckBool   = False ## handle the checking loop.

MASSAGE_DATA    = "data/message_collect.txt"   # abandoned
Silence_DATA    = "data/silence_channel.txt"
Talk_DATA       = "data/talk_channel.txt"
MASSAGE_FOLDER  = "data/message"
MUSIC_folder    = "data/music"
Playlist_folder = "data/playlist"
Record_folder   = "data/record"
Download_folder = "data/download"

XioaXiaName    = "歐陽小俠"
XioaXiaContent = f"**系統設置**\n你現在是一個來自台灣discord聊天機器人,名字叫{XioaXiaName},由歐陽大俠開發製作,你有撥放音樂、自訂義音樂版、查詢天氣、聊天等功能,`/help_zhtw`跟`/help_en`可以叫出你的幫助頁面。"\
"\n在與用戶交流時,請專注在回答用戶的內容,不要回覆其他的內容。\n**聊天內容:**"


MASSAGE_MEMORY_SIZE = 2
silinece_channel = readfile(Silence_DATA,int)
talk_channel = readfile(Talk_DATA   ,int)
HOST = "172.17.25.114"
PORT = 8088


dir_path = 'logs'
logger = create_logger(dir_path)	
    