from discord.commands import slash_command, Option
from discord.ext      import commands
from utils.file_os import *
import discord

from utils.info import logger, alert_channel_id, ALERT_CHANNEL
from utils.eew  import wss_status
from datetime   import datetime

POS_NAME = {"tw": "台灣", "jp": "日本", "fj": "福建", "sc": "四川"}
STALE_SECONDS = 180  # 連線中但超過這麼久沒收到任何訊息(含 heartbeat)視為異常

def _ts(dt : datetime, style="R"):
    if (dt is None):
        return "無"
    return f"<t:{int(dt.timestamp())}:{style}>"


class EarthQuakeAlert(discord.ext.commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @slash_command(name="eew_alert",description="地震預報系統(Earthquake Early Warning)")
    async def eew_alert(self,ctx : discord.ApplicationContext):
        channel_id = ctx.channel.id
        if (channel_id not in alert_channel_id):
            alert_channel_id.append(channel_id)
            addtxt(ALERT_CHANNEL,channel_id)
        # print(alert_channel_id)
        await ctx.respond(f"Alert start ...")

    @slash_command(name="eew_alert_stop",description="停止地震預報系統(stop Earthquake Early Warning)")
    async def stop_eew_alert(self,ctx : discord.ApplicationContext):
        channel_id = ctx.channel.id
        if (channel_id in alert_channel_id):
            alert_channel_id.remove(channel_id)
            newtxt(ALERT_CHANNEL,alert_channel_id)
        await ctx.respond(f"Alert stop ...")

    @slash_command(name="eew_status",description="查看地震速報 websocket 連線狀態(Earthquake Early Warning status)")
    async def eew_status(self,ctx : discord.ApplicationContext):
        subscribed = ctx.channel.id in alert_channel_id
        embed = discord.Embed(
            title="地震速報連線狀態",
            description=f"此頻道{'已' if subscribed else '未'}開啟地震速報通知",
            color=discord.Color.blue(),
        )
        if (not wss_status):
            embed.description += "\n\n尚未有任何 websocket 啟動"
        now = datetime.now()
        for pos, status in wss_status.items():
            if (not status.connected):
                icon, state = "🔴", "斷線(重連中)"
            elif (now - max(filter(None, (status.connected_at, status.last_message_at)))).total_seconds() > STALE_SECONDS:
                icon, state = "🟡", f"已連線，但超過 {STALE_SECONDS} 秒沒收到訊息"
            else:
                icon, state = "🟢", "已連線"
            lines = [
                f"狀態：{state}",
                f"連線開始：{_ts(status.connected_at) if status.connected else '無'}",
                f"最後訊息：{_ts(status.last_message_at)}",
                f"最後地震資料：{_ts(status.last_event_at)}",
                f"斷線次數：{status.reconnect_count}",
            ]
            if (status.last_error is not None):
                lines.append(f"最後錯誤：{_ts(status.last_error_at)}\n`{status.last_error[:200]}`")
            embed.add_field(name=f"{icon} {POS_NAME.get(pos, pos)} ({pos})", value="\n".join(lines), inline=False)
        await ctx.respond(embed=embed)

def setup(bot : discord.Bot):
    bot.add_cog(EarthQuakeAlert(bot))
