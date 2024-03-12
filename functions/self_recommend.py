import discord



from discord.commands import slash_command
from utils.info       import NO_RECOMMEND
from utils.file_os    import addtxt


class Recommend(discord.ext.commands.Cog):
    def __init__(self,bot) -> None:
        self.bot = bot

    @slash_command(name="stop_recommend",description="忌妒....")
    async def stop_recommend(self,ctx):
        ctx.response("好的，我就不再提醒了 :pleading_face: ")
        addtxt(NO_RECOMMEND,ctx.guild.id)

def setup(bot):
    bot.add_cog(Recommend(bot))