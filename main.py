# main.py
from utils.OnMessage import prompt_openai, handle_message
from utils.info     import logger

from traceback       import format_exception

import discord
import dotenv
import os




dotenv.load_dotenv()

token = str(os.getenv("DISCORD_TOKEN"))
bot = discord.Bot(intents=discord.Intents.all(),)


@bot.event
async def on_ready():
    # print(f'We have logged in as {bot.user}')
    logger.info(f'We have logged in as {bot.user}')

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

    from utils.wesAi import prompt_wes_com
    print(prompt_wes_com("用戶:請自我介紹\n小俠:"))


bot.run(token)










