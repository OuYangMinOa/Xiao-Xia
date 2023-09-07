import discord
from discord.ext import commands

class Greetings(discord.ext.commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @discord.ext.commands.Cog.listener()
    async def on_member_join(self, member):
        channel = member.guild.system_channel
        if channel is not None:
            await channel.send(f'歡迎 {member.mention}!!')



def setup(bot):
    bot.add_cog(Greetings(bot))