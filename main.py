# main.py
from utils.OnMessage import prompt_openai, handle_message, ThreadHandleMessage 
from utils.check     import StartChecking, DeleteAllResponse, EarthQuakeWarning, EEWLoop
from utils.info      import logger, CheckBool
from traceback       import format_exception

import asyncio
import discord
import dotenv
import atexit
import time
import os




dotenv.load_dotenv()

token = str(os.getenv("DISCORD_TOKEN"))

intents = discord.Intents.all()

class MyBot(discord.Bot):
    async def close(self):
        CheckBool = False
        await DeleteAllResponse()
        await super().close()

bot = MyBot(intents=intents,)


@bot.event
async def on_ready():
    logger.info(f'We have logged in as {bot.user}')


@bot.before_invoke
async def before_invoke(ctx):
    logger.info(f"{ctx.command} - {ctx.author.name}")

    if (str(ctx.command) not in ['autosound','vote']):
        await ctx.defer()

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return  
    if message.author.bot:
        return
    # await handle_message(message)
    await ThreadHandleMessage(bot,message)
    return





if __name__ == '__main__': 



    # import cogs from cogs folder
    for filename in os.listdir("functions"):
        if filename.endswith(".py"):
            extension = f"functions.{filename[:-3]}"
            bot.load_extension(extension)

    # from utils.wesAi import prompt_wes_com_main
    # print(prompt_wes_com_main("用戶:請自我介紹\n小俠:"))


    print(f"[*] Process id : {os.getpid()}")
    StartChecking(bot)
    EEWLoop(bot).start_alert_tw()
    # .start_alert_fj()\
    # .start_alert_jp()\
    # .start_alert_sc()\
    

    print("[*] Wait for `bot.run` to complete")
    bot.run(token)







