from discord.commands import slash_command, Option
from discord.ext      import commands
from utils.file_os import *
import discord

from requests_html import AsyncHTMLSession
import requests
from utils.info import logger, alert_channel_id, ALERT_CHANNEL



class EarthQuakeAlert(discord.ext.commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @slash_command(name="eew_alert",description="地震預報系統(Earthquake Early Warning)")
    async def eew_alert(self,ctx):
        channel_id = ctx.channel.id
        if (channel_id not in alert_channel_id):
            alert_channel_id.append(channel_id)
            addtxt(ALERT_CHANNEL,channel_id)
        # print(alert_channel_id)
        await ctx.respond(f"Alert start ...")


    @slash_command(name="eew_alert_stop",description="停止地震預報系統(stop Earthquake Early Warning)")
    async def eew_alert(self,ctx):
        channel_id = ctx.channel.id
        if (channel_id in alert_channel_id):
            alert_channel_id.remove(channel_id)
            newtxt(ALERT_CHANNEL,alert_channel_id)
        await ctx.respond(f"Alert stop ...")


def setup(bot):
    bot.add_cog(EarthQuakeAlert(bot))
