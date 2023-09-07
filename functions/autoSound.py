from discord.commands import slash_command, Option
from discord.ext import commands
from utils.info import Record_folder, recording, music_user, sound_user, logger
from datetime import datetime


import discord
import os


class Record(discord.ext.commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="public_record",description="Start a public record")
    async def public_record(self, ctx):
        try:
            if not ctx.author.voice:
                await ctx.respond('you are not connected to a voice channel')
                return
            else:
                channel = ctx.author.voice.channel

            music_user_guild = [music_user[x].ctx.guild.id for x in music_user]
            sound_user_guild = [sound_user[x].ctx.guild.id for x in sound_user]  #  use for check if bot is in the sound dict
            
            if (ctx.guild.id in sound_user_guild):  # in sound_user
                sound_channel_id = sound_user[list(sound_user)[sound_user_guild.index(ctx.guild.id)]].ctx.channel.id
                voice = sound_user[sound_channel_id].voice
                await sound_user[sound_channel_id].clear()

            elif (ctx.guild.id in music_user_guild):  # in sound_user
                music_channel_id = music_user[list(music_user)[music_user_guild.index(ctx.guild.id)]].ctx.channel.id
                voice = music_user[music_channel_id].voice
                await music_user[music_channel_id].pause()
            else:
                voice = await channel.connect()

        except Exception as e:
            logger.error(e)


    

        recording.update({ctx.guild.id: voice})

        SRS = SoundAssist( os.path.join(Record_folder,str(ctx.guild.id)),voice, self.bot)

        # vc.start_recording(
        #     discord.sinks.WaveSink(),  # The sink type to use.
        #     # discord.Sink(encoding='wav', filters={'time': 0}),
        #     SRS.once_done,  # What to do once done.
        #     ctx.channel  # The channel to disconnect from.
        # )




class SoundAssist:
    def __init__(self,saveFolder,voice, client=None):
        self.voice       = voice
        self.client      = client
        self.saveFolder  = saveFolder
        self.start_time  = datetime.now().strftime('%y-%m-%d-%H-%M-%S')
        os.makedirs(saveFolder,exist_ok=True)

    def StartKeepListening(self):
        pass