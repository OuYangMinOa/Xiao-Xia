from utils.info       import silinece_channel, Silence_DATA, logger, chat_dict, talk_channel, Talk_DATA
from discord.commands import slash_command, Option
from discord.ext      import commands
from utils.file_os    import *
from utils.Chat       import Chat

import discord


class Silence(discord.ext.commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="silence",description="Shut me up in this channel")
    async def silence(self,ctx):
        try:
            if (ctx.channel.id in talk_channel):
                talk_channel.remove(ctx.channel.id)
                newtxt(Talk_DATA, talk_channel)
                await ctx.respond("Use `/talk` to let me talk again.")
                return
            await ctx.respond("I could have talked.")
        except Exception as e:
            logger.error(e)

        # try:
        #     if (ctx.channel.id not in silinece_channel):
        #         silinece_channel.append(ctx.channel.id)
        #         addtxt(Silence_DATA,ctx.channel.id)
        #     await ctx.respond("ok, I will shut up in this channel :smiling_face_with_tear: :mask:")
        # except Exception as e:
        #     logger.error(e)


    @slash_command(name="talk",description="If no message is provided, enable reply to all messages.")
    async def talk(self,ctx, msg:Option(str, "message",required=False,default=None)):
        if (msg):
            if (ctx.channel.id not in chat_dict):
                chat_dict[ctx.channel.id] = Chat(ctx.channel.id)

            chatgpt_result = await chat_dict[ctx.channel.id].Talk(ctx.author.name,msg)
            if chatgpt_result:
                await ctx.respond(chatgpt_result)
                return


        try:
            if (ctx.channel.id not in talk_channel):
                talk_channel.append(ctx.channel.id)
                addtxt(Talk_DATA,ctx.channel.id)
                await ctx.respond("Use `/silence` to shut me up, `/clear_talk` to clear chat history.")
                return
        except Exception as e:
            logger.error(e)

        # try:
        #     if (ctx.channel.id in silinece_channel):
        #         silinece_channel.remove(ctx.channel.id)
        #         newtxt(Silence_DATA, silinece_channel)
        #         await ctx.respond(":confetti_ball: Yeah! :confetti_ball:  ")
        #         return

        #     await ctx.respond("I could have talked.")
        # except Exception as e:
        #     logger.error(e)


    @slash_command(name="clear_talk",description="Clear past chat history")
    async def clear_talk(self,ctx):
        if (ctx.channel.id in chat_dict):
            chat_dict[ctx.channel.id].clear_message()
            await ctx.respond("Past chat history has been cleared")
    

def setup(bot):
    bot.add_cog(Silence(bot))