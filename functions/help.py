# help.py


from utils.info       import silinece_channel

import utils.MusicBot     as my_mb # my class

from discord.commands import slash_command, Option
from discord.ext      import commands

import discord


class Help(discord.ext.commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="help_en",description="Show all commands")
    async def help_en(self,ctx):
        await  ctx.respond("""* :notes: **MUSIC**
 - `/play {url}` to play music on youtube.
 - `/skip` to skip the song.
 - `/pause` to pause the song.
 - `/list` to show the playlist.
 - `/loop` to loop current song.
 - `/clear` to clear the playlist.
 - `/leave` to leave the voice channel.
 
* :notes: **SOUND**
 - `/upload_sound {name} {file}` to upload your own sound.
 - `/list_sound` to list all available sound and play it.
 - `/search_sound` {keyword}to search sounds by keywords.

* 😆 **CHAT**
 - `/silence` to shut me up in this chat.
 - `/talk` so I can keep talking.
 - `/joke` say a joke.
 - `/chickensoul` Chicken Soup for the Soul.

* 📑 **INFORMATIONS**
 - `/get_covid` Get the number of confirmed cases in Taiwan.
 - `/weather_day` Get today's Weather Overview
 - `/weather_week` Get weather overview for the week ahead
 - `/weather_pos` One-day weather forecast for each county and city area
""")


    @slash_command(name="help_zhtw",description="幫助訊息")
    async def help_zhtw(self,ctx):
        await  ctx.respond("""* :notes: **音樂**
 - `/play {url}` 播放油管上的音樂。
 - `/skip` 跳過。
 - `/pause` 暫停。
 - `/list` 看撥放清單。
 - `/loop` 循環播放清單。
 - `/clear` 清除播放清單。
 - `/leave` 滾。

* :notes: **音效**
 - `/upload_sound {name} {file}` 上傳你自己的音效。
 - `/list_sound` 查看所有的音效並撥放。
 - `/search_sound` {keyword} 用關鍵字查詢音效。

* 😆 **聊天**
 - `/silence` 在此聊天頻道閉嘴。
 - `/talk` 你可以繼續說話了。
 - `/joke` 講笑話給我聽聽。
 - `/chickensoul` 我需要心靈雞湯。

* 📑 **資訊**
 - `/get_covid` 台灣今天又確了多少。
 - `/weather_day` 今日的天氣資訊。
 - `/weather_week` 未來一周的天氣資訊。
 - `/weather_pos` 各縣市地區的一日天氣預報
""")


def setup(bot):
    bot.add_cog(Help(bot))