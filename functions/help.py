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
        await  ctx.respond(""":notes: **MUSIC**
\t - `/play {url}` to play music on youtube.
\t - `/skip` to skip the song.
\t - `/pause` to pause the song.
\t - `/list` to show the playlist
\t - `/loop` to loop current song.
\t - `/clear` to clear the playlist
\t - `/leave` to leave the voice channel.

:notes: **SOUND**
\t - `/upload_sound {name} {file}` to upload your own sound.
\t - `/list_sound` to list all available sound and play it.

😆 **CHAT**
\t - `/silence` to shut me up
\t - `/talk` so I can keep talking
\t - `/joke` say a joke
\t - `/chickensoul` Chicken Soup for the Soul

📑 **INFORMATIONS**
\t - `/get_covid` Get the number of confirmed cases in Taiwan.
""")


    @slash_command(name="help_zhtw",description="幫助訊息")
    async def help_zhtw(self,ctx):
        await  ctx.respond(""":notes: **音樂**
\t - `/play {url}` 播放油管上的音樂。
\t - `/skip` 跳過。
\t - `/pause` 暫停。
\t - `/list` 看撥放清單。
\t - `/loop` 循環播放清單。
\t - `/clear` 清除播放清單。
\t - `/leave` 滾。

:notes: **音效**
\t - `/upload_sound {name} {file}` 上傳你自己的音效.
\t - `/list_sound` 查看所有的音效並撥放.

😆 **聊天**
\t - `/silence` 閉嘴。
\t - `/talk` 你可以繼續說話了。
\t - `/joke` 講笑話給我聽聽
\t - `/chickensoul` 我需要心靈雞湯

📑 **資訊**
\t - `/get_covid` 台灣今天又確了多少.
""")


def setup(bot):
    bot.add_cog(Help(bot))