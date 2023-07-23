from discord.commands import slash_command, Option
from discord.ext      import commands
from utils.file_os import *
import discord

from requests_html import AsyncHTMLSession



class Weather(discord.ext.commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @slash_command(name="weather",description="Today's Weather Overview")
    async def weather(self,ctx):
        await ctx.respond(f"/weather - {ctx.author.mention}")


        url = "https://www.cwb.gov.tw/V8/C/W/index.html"
        session = AsyncHTMLSession()
        r = await  session.get(url)
        await r.html.arender()

        text = r.html.xpath("/html/body/div[3]/main/div/div[1]/div/div/div[1]/div")[0].text
        ####################  handle text ####################
        text = "\n".join(text.split("\n")[1:])
        text = "# "+ text
        ch_num = ['一','二','三','四','五','六','七','八','九']
        for num,each_ch_num in enumerate(ch_num):
            if (each_ch_num in text):
                text = text.replace(each_ch_num+'、',f"## {each_ch_num}\n - ")

        await ctx.send(text)

        #################### warning message #################

        next_text = "\n# 天氣特報 \n"
        url = "https://www.cwb.gov.tw/V8/C/"
        r = await session.get(url)

        await r.html.arender()
        for each_link in r.html.xpath("/html/body/header/div[2]/div/div/div[1]/div/div/ol")[0].links:
            print(each_link)
            next_text = next_text + f" * https://www.cwb.gov.tw{each_link}\n"
        next_text = next_text + "\n資料來源:https://www.cwb.gov.tw/V8/C/"
        await session.close()
        await ctx.send(next_text)

        


    @slash_command(name="week_weather",description="Weather overview for the week ahead")
    async def week_weather(self,ctx):
        await ctx.respond(f"/weather - {ctx.author.mention}")


        url = "https://www.cwb.gov.tw/V8/C/W/index.html"
        session = AsyncHTMLSession()
        r = await  session.get(url)

        await r.html.arender()

        text = r.html.xpath("/html/body/div[3]/main/div/div[1]/div/div/div[2]")[0].text
        await session.close()
        text = "\n".join(text.split("\n")[1:])
        text = "# "+ text
        text = text + "\n資料來源:https://www.cwb.gov.tw/V8/C/"
        await ctx.send(text)


def setup(bot):
    bot.add_cog(Weather(bot))