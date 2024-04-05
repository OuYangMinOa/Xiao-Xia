# help.py


from utils.info       import silinece_channel
from discord.commands import slash_command, Option
from discord.ext      import commands

import discord


class Help(discord.ext.commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="help_en",description="Show all commands")
    async def help_en(self,ctx):
        await  ctx.respond("""* :notes: **MUSIC**
 - `/play {url}` play music (youtube or spotify).
 - `/platlist` show all playlist
 - `/save_platlist {name}` save current playlist
 - `/skip` to skip the song.
 - `/stop_music` same as skip but only stop music。
 - `/stop_sound` same as skip but only stop sound。
 - `/pause` to pause the song.
 - `/list` to show the playlist.
 - `/loop` to loop current song.
 - `/clear` to clear the playlist.
 - `/leave` to leave the voice channel.
 
* :notes: **SOUND**
 - `/upload_sound {name} {file}` to upload your own sound.
 - `/list_sound` to list all available sound and play it.
 - `/search_sound` {keyword}to search sounds by keywords.
 - `/say` to say the word.
 - `/autosound` Automatically detect voice and play sound effects board
 - `/stop_autosound` Stop autosound
                           
* 😆 **CHAT**
 - `/clear_talk` Clear past chat history.
 - `/silence` to shut me up in this chat.
 - `/talk` so I can keep talking.
 - `/joke` say a joke.
 - `/chickensoul` Chicken Soup for the Soul.
 - `/encrypt ` Convert the message into Morse code.
 - `/decrypt ` Convert Morse code into messages.

* 📑 **INFORMATIONS**
 - `/get_covid` Get the number of confirmed cases in Taiwan.
 - `/weather_day` Get today's Weather Overview
 - `/weather_week` Get weather overview for the week ahead
 - `/weather_pos` One-day weather forecast for each county and city area
 - `/summaryPdf` Read the PDF and summrize each page
 - `/eew_alert` Earthquake early warning (Taiwan)

* 📑 **FUNCTIONS**                            
 - `/vote` vote
 - `/ping` Show latency
 - `/骰子` dice
""")

    # @slash_command(name="幫助",description="幫助訊息")
    @slash_command(name="help_zhtw",description="幫助訊息")
    async def help_zhtw(self,ctx):
        await  ctx.respond("""* :notes: **音樂**
 - `/play {url}` 播放音樂 (youtube 或 spotify)。
 - `/platlist` 展示儲存的播放清單
 - `/save_platlist {name}` 儲存現在正在撥放的歌單
 - `/skip` 跳過。
 - `/stop_music` 跟skip一樣 但只處理音樂。
 - `/stop_sound` 跟skip一樣 但只處理音效版。
 - `/pause` 暫停。
 - `/list` 看撥放清單。
 - `/loop` 循環播放清單。
 - `/clear` 清除播放清單。
 - `/leave` 滾。

* :notes: **音效版**
 - `/upload_sound {name} {file}` 上傳你自己的音效。
 - `/list_sound` 查看所有的音效並撥放。
 - `/search_sound` {keyword} 用關鍵字查詢音效。
 - `/say` 讓我說出你要我說的話.
 - `/autosound` 自動偵測語音 然後撥放音效板
 - `/stop_autosound` 停止 autosound

* 😆 **聊天**
 - `/clear_talk` 清空過去的聊天紀錄。                        
 - `/silence` 在此聊天頻道閉嘴。
 - `/talk` 你可以繼續說話了。
 - `/joke` 講笑話給我聽聽。
 - `/chickensoul` 我需要心靈雞湯。
 - `/encrypt ` 把文字轉成摩斯密碼.
 - `/decrypt ` 把摩斯密碼轉成文字.

* 📑 **資訊**
 - `/get_covid` 台灣今天又確了多少。
 - `/weather_day` 今日的天氣資訊。
 - `/weather_week` 未來一周的天氣資訊。
 - `/weather_pos` 各縣市地區的一日天氣預報。
 - `/summaryPdf` 讀取PDF然後幫你做每頁的總結
 - `/eew_alert` 地震預警 (Taiwan)

* 📑 **功能**                     
 - `/vote` 投票
 - `/ping` 顯示跟機器人的延遲
 - `/骰子` 骰骰子
""")


def setup(bot):
    bot.add_cog(Help(bot))