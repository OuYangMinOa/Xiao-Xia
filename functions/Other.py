from discord.commands import slash_command
from discord.ext      import commands
from utils.file_os    import addtxt
from utils.info       import MASSAGE_DATA, PASS_MSG
from utils.info       import logger
from utils.wesAi      import prompt_wes_com
import utils.Covid as my_Cd
import discord

    

class Others(discord.ext.commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="joke",description="Talk a joke")
    async def joke(self, ctx):
        await ctx.respond("joke"+ f' - {ctx.author.mention}')

        logger.info("joke"+ f' - {ctx.author.name}')
        this_joke = await prompt_wes_com('Q:請你說個笑話\nA:')


        PASS_MSG.append(f"{ctx.author.name}:請你說個笑話")
        PASS_MSG.append("小俠:"+this_joke)
        logger.info("小俠:"+this_joke)


        addtxt( MASSAGE_DATA,f"{ctx.author.name}:請你說個笑話")
        addtxt( MASSAGE_DATA,"小俠:"+this_joke)


        await ctx.send( this_joke)


    @slash_command(name="chickensoul",description="Chicken Soup for the Soul")
    async def ChickenSoul(self, ctx):
        await ctx.respond("chickensoul"+ f' - {ctx.author.mention}')
        logger.info("chickensoul"+ f' - {ctx.author.name}')

        this_chicken = await prompt_wes_com('Q:請你說個一句心靈雞湯\nA:')

        PASS_MSG.append(f"{ctx.author.name}:請你說個一句心靈雞湯")
        PASS_MSG.append("小俠:"+this_chicken)
        logger.info("小俠:"+this_chicken)
        
        addtxt( MASSAGE_DATA,f"{ctx.author.name}:請你說個一句心靈雞湯")
        addtxt( MASSAGE_DATA,"小俠:"+this_chicken)

        await ctx.send(this_chicken)

    @slash_command(name="get_covid",description="Number of confirmed cases in Taiwan")
    async def get_covid(self, ctx):
        await ctx.respond(my_Cd.get_covid())
    


def setup(bot):
    bot.add_cog(Others(bot))