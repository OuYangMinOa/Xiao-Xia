from discord.commands import slash_command, Option
from utils.info       import Download_folder, logger
from pytube           import YouTube


import threading
import discord
import uuid
import os

class Download(discord.ext.commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="download_yt",description="從yt上下載音樂或影片 (低於20分鐘的音樂/2分鐘的音樂 )")
    async def download_yt(self,ctx, url: Option(str, "url", required = True),video=Option(str, "video",choices=['True','False'], required = False,default='False')):
        await ctx.respond(f"download_yt - {ctx.author.mention}\n{url}")
        ThisYt = YouTube(url)
        video = eval(eval)
        if (video):filename = f"{ThisYt.title}.mp4"
        else:      filename = f"{ThisYt.title}.mp3"

        def download(url,ThisYt):
            logger.info("[*] Downloading "+url)
            if (video):
                ThisYt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first().download(output_path=Download_folder,filename=filename)
            else:
                ThisYt.streams.filter(only_audio=True).first().download(output_path=Download_folder,filename=filename)
            logger.info("[*] successfully downloaded")
            

        thisThread = threading.Thread(target=download,args=(url,ThisYt,))
        thisThread.start()
        thisThread.join()

        thisFilename = os.path.join(Download_folder,filename)
        filesize     = len(open(thisFilename,'rb').read())
        logger.info(f"[*] {filename} filesize : {filesize/1024/1024} MB")

        if ( filesize<8*1024*1024 ):
            await ctx.send(file=discord.File(filename=filename, fp = thisFilename ))
            # os.remove(thisFilename)
        else:
            await ctx.send("File size too big !!")




def setup(bot):
    bot.add_cog(Download(bot))