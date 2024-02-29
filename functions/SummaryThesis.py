from discord.commands import slash_command, Option
from discord.ext      import commands
from utils            import wesAi
from utils.info       import logger
from PyPDF2           import PdfReader 
from tqdm.auto        import tqdm

import discord
import os

class SummaryThesis(discord.ext.commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    @slash_command( name="summary_thesis",description="upload pdf")
    async def summary_thesis(self,ctx, file: discord.Attachment):
        logger.info(f"summary_thesis {ctx.author.name} upload a pdf for thesis summarization")
        await ctx.respond(f"/summary_thesis - {ctx.author.mention}",ephemeral=True)
        thisMess = await ctx.respond(f"Analyzing the PDF ... (It's might take a while)",ephemeral=True)

        if file:
            attachment = file

            if ( not attachment.filename.endswith('txt') and not attachment.filename.endswith('pdf')):
                await ctx.respond(f"Only allow pdf and txt files")
                return
            
            save_folder = f"data/pdf/{ctx.guild.id}"
            os.makedirs(save_folder,exist_ok=True)

            await attachment.save(f"{save_folder}/{attachment.filename}") 
            # await ctx.respond(f"{attachment.filename} received.")

            reader = PdfReader(f"{save_folder}/{attachment.filename}") 


            totalText = ""
            print("[*] Summarizing the PDF...")
            for num,each in tqdm(enumerate(reader.pages)):
                # totalText = totalText + each.extract_text()
                thisSum =  await wesAi.prompt_wes_com(f"幫我以條列式總結以下文字,以中文回復:\n{each.extract_text()}")
                thisOutput = f"## Page{num +1}\n{thisSum}"

                while thisOutput!="":
                    if (len(thisOutput) > 1900):
                        await ctx.respond(thisOutput[:1900],ephemeral=True)
                        thisOutput = thisOutput[1900:]

                    else:
                        await ctx.respond(thisOutput,ephemeral=True)
                        thisOutput = ""
                        break

            # summaryText = await wesAi.prompt_wes_com(f"幫我以條列式總結以下文字:\n{totalText}")

            
            # await ctx.respond(f"{summaryText}",ephemeral=True)
        await thisMess.delete()



def setup(bot):
    bot.add_cog(SummaryThesis(bot))
            
