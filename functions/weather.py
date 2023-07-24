from discord.commands import slash_command, Option
from discord.ext      import commands
from utils.file_os import *
import discord

from requests_html import AsyncHTMLSession
import requests
from utils.info import logger

class Weather(discord.ext.commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @slash_command(name="weather_day",description="Today's Weather Overview")
    async def weather_day(self,ctx):
        await ctx.respond(f"/weather_day - {ctx.author.mention}")
        try:
            url = "https://www.cwb.gov.tw/V8/C/W/index.html"
            session = AsyncHTMLSession()
            r = await  session.get(url)
            await r.html.arender()

            image_links = ""
            for i in r.html.xpath("/html/body/div[3]/main/div/div[3]/a"):
                image_links = 'https://www.cwb.gov.tw'+list(i.links)[0]

            text = r.html.xpath("/html/body/div[3]/main/div/div[1]/div/div/div[1]/div")[0].text
            ####################  handle text ####################
            text = "\n".join(text.split("\n")[1:])
            text = "# "+ text
            ch_num = ['一','二','三','四','五','六','七','八','九']
            for num,each_ch_num in enumerate(ch_num):
                if (each_ch_num in text):
                    text = text.replace(each_ch_num+'、',f"## {each_ch_num}\n - ")
            
            await ctx.send(text)
            
            await ctx.send(image_links)
            #################### warning message #################

            next_text = "\n# :warning:  天氣特報  :warning: \n"
            url = "https://www.cwb.gov.tw/V8/C/"
            r = await session.get(url)

            await r.html.arender()
            for each_link in r.html.xpath("/html/body/header/div[2]/div/div/div[1]/div/div/ol")[0].links:
                print(each_link)
                next_text = next_text + f" * https://www.cwb.gov.tw{each_link}\n"
            next_text = next_text + "\n資料來源:中央氣象局"
            await session.close()
            await ctx.send(next_text)
        except Exception as e:
            logger.error(e)

        


    @slash_command(name="weather_week",description="Weather overview for the week ahead")
    async def weather_week(self,ctx):
        await ctx.respond(f"/weather_week - {ctx.author.mention}")

        try:
            url = "https://www.cwb.gov.tw/V8/C/W/index.html"
            session = AsyncHTMLSession()
            r = await  session.get(url)

            await r.html.arender()

            text = r.html.xpath("/html/body/div[3]/main/div/div[1]/div/div/div[2]")[0].text
            await session.close()
            text = "\n".join(text.split("\n")[1:])
            text = "# "+ text
            text = text + "\n資料來源:中央氣象局"
            await ctx.send(text)
        except Exception as e:
            logger.error(e)

    @slash_command(name="weather_pos",description="Weather overview for the certain position.")
    async def weather_pos(self,ctx):
        towns = ["基隆市",
                "臺北市",
                "新北市",
                "桃園市",
                "新竹市",
                "新竹縣",
                "苗栗縣",
                "臺中市",
                "彰化縣",
                "南投縣",
                "雲林縣",
                "嘉義市",
                "嘉義縣",
                "臺南市",
                "高雄市",
                "屏東縣",
                "宜蘭縣",
                "花蓮縣",
                "臺東縣",
                "澎湖縣",
                "金門縣",
                "連江縣"]
        values = ["10017",
                "63",
                "65",
                "68",
                "10018",
                "10004",
                "10005",
                "66",
                "10007",
                "10008",
                "10009",
                "10020",
                "10010",
                "67",
                "64",
                "10013",
                "10002",
                "10015",
                "10014",
                "10016",
                "09020",
                "09007",]
        MWS = MyWeatherSelection(ctx,towns,values)
        await ctx.respond(f"weather_pos {ctx.author.mention}", view=MWS.view, ephemeral=True)

def SvgToPng(url):
    # print(url)
    numbers = url.split("/")[-1][0:2]
    
    ouput_filename = f"data/cwbgov_pic/cwbgov{numbers}.png"
    return "cwbgov{numbers}.png", ouput_filename
    # https://www.cwb.gov.tw/V8/assets/img/weather_icons/weathers/svg_icon/night/.svg


class MyWeatherSelection:
    def __init__(self,ctx, towns,values):
        self.ctx, self.towns, self.values,  = ctx,towns,values
        options = [ discord.SelectOption(label=towns[i])for i in range(len(towns))]

        self.select = discord.ui.Select(
                placeholder = "選擇縣市",
                min_values  = 1, 
                max_values  = 1,
                options = options
            )
        self.view = discord.ui.View(timeout=24*60*60*7)
        self.view.add_item(self.select)
        self.select.callback = self.callback
    async def callback(self, interaction):
        which_chosen = self.towns.index(self.select.values[0])
        if (which_chosen==0):
            url = "https://www.cwb.gov.tw/V8/C/W/County/index.html"
        else:
            url = f"https://www.cwb.gov.tw/V8/C/W/County/County.html?CID={self.values[which_chosen]}"

        await interaction.response.send_message(self.select.values[0])


        await self.grabWeatherPositionInformation(url)

    async def grabWeatherPositionInformation(self,url):
        session = AsyncHTMLSession()
        r = await  session.get(url)
        await r.html.arender() 
        
        await self.ctx.send("# " + r.html.xpath("/html/body/div[2]/main/div/div[1]/div[1]/div/h2")[0].text)
        await self.ctx.send("* " + r.html.xpath("/html/body/div[2]/main/div/div[2]/a")[0].text)

        filename, filepath1 = SvgToPng(f"https://www.cwb.gov.tw{r.html.xpath('/html/body/div[2]/main/div/div[1]/div[3]/div[2]/ul/li[1]/img')[0].attrs['src']}")
        file1 = discord.File(filepath1,filename="output1.png")
        embed1=discord.Embed(title="今晚明晨")
        embed1.set_thumbnail(url = f"attachment://output1.png")
        embed1.add_field(name="溫度",value=r.html.xpath("/html/body/div[2]/main/div/div[1]/div[3]/div[2]/ul/li[1]/span[2]/span[1]")[0].text,inline=False)
        embed1.add_field(name=":umbrella: 降雨機率",value=r.html.xpath("/html/body/div[2]/main/div/div[1]/div[3]/div[2]/ul/li[1]/span[3]")[0].text.replace("降雨機率",'\t'),inline=False)
        embed1.add_field(value="\u200B",name=r.html.xpath("/html/body/div[2]/main/div/div[1]/div[3]/div[2]/ul/li[1]/span[4]")[0].text,inline=False)
        await self.ctx.send(file=file1,embed=embed1)



        filename,filepath2 = SvgToPng(f"https://www.cwb.gov.tw{r.html.xpath('/html/body/div[2]/main/div/div[1]/div[3]/div[2]/ul/li[2]/img')[0].attrs['src']}")
        file2 = discord.File(filepath2,filename="output2.png")
        embed2=discord.Embed(title="明日白天")
        embed2.set_thumbnail(url = f"attachment://output2.png")
        embed2.add_field(name="溫度",value=r.html.xpath("/html/body/div[2]/main/div/div[1]/div[3]/div[2]/ul/li[2]/span[2]/span[1]")[0].text,inline=False)
        embed2.add_field(name=":umbrella: 降雨機率",value=r.html.xpath("/html/body/div[2]/main/div/div[1]/div[3]/div[2]/ul/li[2]/span[3]")[0].text.replace("降雨機率",'\t'),inline=False)
        embed2.add_field(value="\u200B",name=r.html.xpath("/html/body/div[2]/main/div/div[1]/div[3]/div[2]/ul/li[2]/span[4]")[0].text,inline=False)
        await self.ctx.send(file=file2,embed=embed2)


        filename,filepath3 = SvgToPng(f"https://www.cwb.gov.tw{r.html.xpath('/html/body/div[2]/main/div/div[1]/div[3]/div[2]/ul/li[3]/img')[0].attrs['src']}")
        file3 = discord.File(filepath3,filename="output3.png")
        embed3=discord.Embed(title="明日晚上")
        embed3.set_thumbnail(url = f"attachment://output3.png")
        embed3.add_field(name="溫度",value=r.html.xpath("/html/body/div[2]/main/div/div[1]/div[3]/div[2]/ul/li[3]/span[2]/span[1]")[0].text,inline=False)
        embed3.add_field(name=":umbrella: 降雨機率",value=r.html.xpath("/html/body/div[2]/main/div/div[1]/div[3]/div[2]/ul/li[3]/span[3]")[0].text.replace("降雨機率",'\t'),inline=False)
        embed3.add_field(name=r.html.xpath("/html/body/div[2]/main/div/div[1]/div[3]/div[2]/ul/li[3]/span[4]")[0].text,value="\u200B",inline=False)
        await self.ctx.send(file=file3,embed=embed3)


        await self.ctx.send(f"https://www.cwb.gov.tw{r.html.xpath('/html/body/div[2]/main/div/div[5]/div[1]/div/img')[0].attrs['src']}")
        

def setup(bot):
    bot.add_cog(Weather(bot))