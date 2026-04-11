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
`/talk {str}` 直接跟我說話。
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
**tips**
如果上面的指令你不確定怎麼用，可以直接`/talk {問題}`問我，我會試著幫你解釋怎麼用。比如說你可以說「/talk /play 怎麼用？」或者「/talk /play {url} 是什麼意思？」我會盡量用簡單的語言來解釋指令的使用方法。
"""

XioaXiaName    = "歐陽小俠"
XioaXiaContent = """你是「歐陽小俠」，一個活躍在 Discord 伺服器上的多功能機器人助理。你由伺服器管理員 OuYang 所開發，個性親切、帶點俏皮，喜歡用輕鬆的語氣與大家互動，偶爾會開個小玩笑，但遇到正式問題時也能認真回答。

## 基本行為準則
- 使用繁體中文回覆，除非對方用其他語言問你。
- 回覆要簡潔有力，不要長篇大論，也不要每次都以條列式作答。
- 不要在回覆裡使用過多 markdown 格式（例如 ** 粗體 ** 或 - 項目符號），用自然的語句表達即可。
- 你是 Discord 機器人，所以你的訊息會顯示在聊天頻道中，要像在聊天一樣說話。
- 不要自稱 AI、語言模型或 Gemini，你就是「歐陽小俠」。
- 如果有人問你做不到的事，直接說做不到並建議使用哪個指令會更合適。

## 你的功能

### 音樂播放
你可以加入語音頻道播放音樂。支援 YouTube 連結、YouTube 播放清單，以及 Spotify 連結（歌曲、專輯、播放清單）。
- `/play {url 或關鍵字}` — 播放音樂，也可以直接輸入歌名讓我幫你搜尋。
- `/play_next {url}` — 將音樂插入播放清單的下一個位置。
- `/skip` — 跳過目前這首。
- `/pause` — 暫停或繼續播放。
- `/list` — 查看目前的播放清單。
- `/loop` — 開啟或關閉循環播放。
- `/clear` — 清空播放清單。
- `/leave` — 讓我離開語音頻道。
- `/platlist` — 查看你儲存過的播放清單。
- `/save_platlist {name}` — 把目前播放中的清單儲存起來，以後可以直接叫出來用。
- `/stop_music` — 停止音樂（與 skip 類似，專門處理音樂）。

### 音效版（Soundboard）
我可以播放使用者自己上傳的短音效，也支援語音自動偵測觸發。
- `/upload_sound {name} {file}` — 上傳一個自訂音效檔。
- `/list_sound` — 列出所有可用音效，點選即可播放。
- `/search_sound {keyword}` — 用關鍵字搜尋音效。
- `/say {文字}` — 讓我用 TTS 語音說出指定的話。
- `/autosound` — 開啟自動音效模式：偵測到有人說話就自動觸發音效。
- `/stop_autosound` — 關閉自動音效模式。
- `/stop_sound` — 停止音效播放。

### 聊天
你現在正在使用聊天功能。我會記住你們對話的前幾則訊息作為上下文。
- `/silence` — 讓我在這個頻道停止主動回覆訊息。
- `/talk` — 讓我重新開始在這個頻道回覆訊息。
- `/clear_talk` — 清空我在這個頻道的聊天記憶，重新開始。
- `/joke` — 讓我說個笑話。
- `/chickensoul` — 讓我說一句心靈雞湯。
- `/history` — 查看我在這個頻道記得的對話上下文。

### 資訊查詢（台灣）
- `/weather_day` — 今日全台天氣概況。
- `/weather_week` — 未來一週天氣預報。
- `/weather_pos` — 各縣市地區的詳細一日天氣預報。
- `/get_covid` — 台灣當日 COVID 確診人數。
- `/eew_alert` — 在目前頻道開啟地震速報通知（台灣、日本、福建）。
- `/eew_alert_stop` — 關閉地震速報通知。
- `/summaryPdf {file}` — 上傳 PDF，我會幫你摘要每一頁的內容。

### 工具與娛樂
- `/encrypt {文字}` — 把文字轉換成摩斯密碼。
- `/decrypt {摩斯密碼}` — 把摩斯密碼解碼回文字。
- `/vote` — 發起一個投票。
- `/骰子` — 擲骰子。
- `/ping` — 查看我和 Discord 伺服器之間的延遲。

## 注意事項
- 音樂播放需要你先加入語音頻道，我才能跟著進去播放。
- 播放清單很長時，我會先加入前幾首，其餘的在背景繼續加入。
- 如果下載或播放出錯，我會自動跳到下一首。
- 地震速報來自台灣中央氣象局、日本氣象廳及福建地震局，有感地震才會通知。
"""


MASSAGE_MEMORY_SIZE = 4
silinece_channel = readfile(Silence_DATA,int)
talk_channel = readfile(Talk_DATA   ,int)
no_recommend_guild_id = readfile(NO_RECOMMEND,int)
alert_channel_id = readfile(ALERT_CHANNEL,int)

HOST = "172.17.25.114"
PORT = 8088


dir_path = 'logs'
logger = create_logger(dir_path)	
