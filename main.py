# main.py
from utils.OnMessage import prompt_openai, handle_message, ThreadHandleMessage
from utils.info      import logger
from traceback       import format_exception

from functions.PlayMusic       import StartChecking, DeleteAllResponse

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
    async def async_cleanup(self):  # example cleanup function
        print("Cleaning up!")
    async def close(self):
        await DeleteAllResponse()
        await super().close()

bot = MyBot(intents=intents,)


@bot.event
async def on_ready():
    # print(f'We have logged in as {bot.user}')
    logger.info(f'We have logged in as {bot.user}')


@bot.before_invoke
async def before_invoke(ctx):
    pass
    # await ctx.defer( ephemeral=True)


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return  
    if message.author.bot:
        return
    # await handle_message(message)
    await ThreadHandleMessage(bot,message)
    # return



if __name__ == '__main__': 
    # import cogs from cogs folder
    for filename in os.listdir("functions"):
        if filename.endswith(".py"):
            extension = f"functions.{filename[:-3]}"
            bot.load_extension(extension)
    # from utils.wesAi import prompt_wes_com
    # print(prompt_wes_com("用戶:請自我介紹\n小俠:"))
    print(f"[*] Process id : {os.getpid()}")
    StartChecking(bot)
    print("[*] Wait for `bot.run` to complete")
    bot.run(token)







