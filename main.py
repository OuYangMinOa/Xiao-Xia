# main.py
from utils.OnMessage import prompt_openai, handle_message
from utils.info      import logger
from traceback       import format_exception

from functions.PlayMusic       import StartChecking

import asyncio
import discord
import dotenv
import time
import os




dotenv.load_dotenv()

token = str(os.getenv("DISCORD_TOKEN"))

intents = discord.Intents.default()


bot = discord.Bot(intents=intents,)


@bot.event
async def on_ready():
    # print(f'We have logged in as {bot.user}')
    logger.info(f'We have logged in as {bot.user}')


@bot.before_invoke
async def before_invoke(ctx):
    await asyncio.sleep(1.2)
    await ctx.response.defer( ephemeral=True)
    await asyncio.sleep(1)



@bot.event
async def on_message(message):
    if message.author == bot.user:
        return  
    await handle_message(message)



if __name__ == '__main__': 
    # import cogs from cogs folder
    for filename in os.listdir("functions"):
        if filename.endswith(".py"):
            extension = f"functions.{filename[:-3]}"
            bot.load_extension(extension)
    # from utils.wesAi import prompt_wes_com
    # print(prompt_wes_com("用戶:請自我介紹\n小俠:"))
print("[*] Wait for `bot.run` to complete")
StartChecking(bot)
bot.run(token)










