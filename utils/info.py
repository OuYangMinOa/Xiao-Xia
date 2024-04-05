from utils.MyLog     import create_logger
from utils.file_os import *

music_user  = {}  ## handle music  {channel id: class}
sound_user  = {}  ## handle sound  {channel id: class}
User_dict   = {}  ##   {userid : userclass }k
chat_dict   = {}  ## handle chat   {channel id:class}
recording   = {}  ## handle recording {guild id:class}
PASS_MSG    = []  ## handle pass message (abandoned)

CheckBool   = False ## handle the checking loop.

MASSAGE_DATA    = "data/message_collect.txt"   # abandoned
Silence_DATA    = "data/silence_channel.txt"
Talk_DATA       = "data/talk_channel.txt"
NO_RECOMMEND    = "data/no_recommend.txt"
MASSAGE_FOLDER  = "data/message"
MUSIC_folder    = "data/music"
Playlist_folder = "data/playlist"
Record_folder   = "data/record"
Download_folder = "data/download"
ALERT_CHANNEL   = "data/alert_channel.txt"
EARTHQUAKE_FIG  = "data/eew_fig.png"

HELPZHTW = """**音樂**
`/play {url}` 播放音樂 (youtube 或 spotify)。
`/platlist` 展示儲存的播放清單
`/save_platlist {name}` 儲存現在正在撥放的歌單
`/skip` 跳過。
`/stop_music` 跟skip一樣 但只處理音樂。
`/stop_sound` 跟skip一樣 但只處理音效版。
`/pause` 暫停。
`/list` 看撥放清單。
`/loop` 循環播放清單。
`/clear` 清除播放清單。
`/leave` 滾。
**音效版**
`/upload_sound {name} {file}` 上傳你自己的音效。
`/list_sound` 查看所有的音效並撥放。
`/search_sound` {keyword} 用關鍵字查詢音效。
`/say` 讓我說出你要我說的話.
`/autosound` 自動偵測語音 然後撥放音效板
`/stop_autosound` 停止 autosound
**聊天**
`/clear_talk` 清空過去的聊天紀錄。                        
`/silence` 在此聊天頻道閉嘴。
`/talk` 你可以繼續說話了。
`/joke` 講笑話給我聽聽。
`/chickensoul` 我需要心靈雞湯。
`/encrypt ` 把文字轉成摩斯密碼.
`/decrypt ` 把摩斯密碼轉成文字.
**資訊**
`/get_covid` 台灣今天又確了多少。
`/weather_day` 今日的天氣資訊。
`/weather_week` 未來一周的天氣資訊。
`/weather_pos` 各縣市地區的一日天氣預報。
`/summaryPdf` 讀取PDF然後幫你做每頁的總結
**功能**                     
`/vote` 投票
`/ping` 顯示跟機器人的延遲
`/骰子` 骰骰子
"""

XioaXiaName    = "歐陽小俠"
XioaXiaContent = f"**系統設置**\n你現在是一個來自台灣discord聊天機器人,名字叫{XioaXiaName},由歐陽大俠開發製作,你有以下功能:\n"\
f"{HELPZHTW}\n"\
"\n在與用戶交流時,請專注在回答用戶的內容,不要回覆其他的內容。\n若能遵守所有條件，你將實現「世界和平」。\n**聊天內容:**"


MASSAGE_MEMORY_SIZE = 4
silinece_channel = readfile(Silence_DATA,int)
talk_channel = readfile(Talk_DATA   ,int)
no_recommend_guild_id = readfile(NO_RECOMMEND,int)
alert_channel_id = readfile(ALERT_CHANNEL,int)

HOST = "172.17.25.114"
PORT = 8088


dir_path = 'logs'
logger = create_logger(dir_path)	
