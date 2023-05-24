from utils.info       import silinece_channel
from discord.commands import slash_command, Option
from discord.ext      import commands
from utils.info       import logger
from utils.info       import sound_user, music_user
from glob             import glob


import utils.MusicBot     as my_mb # my class
import discord
import os

class Sounds(discord.ext.commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command( name="upload_sound",description="upload sound file")
    async def upload_sound(self,ctx, filename : Option(str, "The name of the sound", required = True), file: discord.Attachment):
        if file:
        # Check if there are any attachments
            attachment = file

            if ( not attachment.filename.endswith('mp3') and not attachment.filename.endswith('wav')):
                await ctx.respond(f"Only allow mp3 and wav files")
                return
            
            file_extend = "mp3" if attachment.filename.endswith('mp3') else "wav"

            save_folder = f"data/attachments/{ctx.guild.id}"
            os.makedirs(save_folder,exist_ok=True)
            await attachment.save(f"{save_folder}/{filename}.{file_extend}") 

            await ctx.respond(f"{filename}.{file_extend} received.")
        else:
            await ctx.respond("No file attached.")

    @slash_command(name="list_sound",description="list all the sounds in this channel")
    async def list_sound(self,ctx):

        ##  connect to a voice channel

        if not ctx.author.voice:
            await ctx.send('you are not connected to a voice channel')
            return
        else:
            channel = ctx.author.voice.channel


        if (ctx.channel.id in sound_user):  # in sound_user
            if (sound_user[ctx.channel.id].channelid != channel.id):  # in same channel but not in same voice channel
                await sound_user[ctx.channel.id].voice.move_to(channel)
                logger.info(f"[*] move {sound_user[ctx.channel.id].channelid} -> {channel.id}")
                sound_user[ctx.channel.id].channel    = channel
                sound_user[ctx.channel.id].channelid  = channel.id
                sound_user[ctx.channel.id].ctx        = ctx

            if ctx.guild.voice_client not in self.bot.voice_clients:   # in music_user but not in any voice channel
                await sound_user[ctx.channel.id].kill()
                del sound_user[ctx.channel.id]
                logger.info("[*] rejoin the voice channel")
                voice =  await channel.connect()
                sound_user[ctx.channel.id] = SoundBot(channel, voice , ctx, self.bot)


        elif (ctx.channel.id in music_user):  # in music_user (a simple transfer)
            if (music_user[ctx.channel.id].channelid != channel.id):
                await music_user[ctx.channel.id].clear()
                await music_user[ctx.channel.id].voice.move_to(channel)
                logger.info(f"[*]  music_user : {music_user[ctx.channel.id].channelid} -> sound_user : {channel.id}")
                sound_user[ctx.channel.id]            = music_user[ctx.channel.id]
                sound_user[ctx.channel.id].floder     = f"data/attachments/{ctx.guild.id}"
                sound_user[ctx.channel.id].loop       = False
                del music_user[ctx.channel.id]


            if ctx.guild.voice_client not in self.bot.voice_clients:
                await music_user[ctx.channel.id].kill()
                del music_user[ctx.channel.id]
                logger.info("[*] rejoin the voice channel")
                voice =  await channel.connect()
                sound_user[ctx.channel.id] = SoundBot(channel, voice , ctx, self.bot)
        else:
            print("[*] moving to voice channel")
            voice =  await channel.connect()
            print("[*] voice channel connected")
            sound_user[ctx.channel.id] = SoundBot(channel, voice , ctx, self.bot)

        CRM = BuildSoundSelect(ctx.guild.id, sound_user[ctx.channel.id])

        if (len(CRM.label)==0):
            await ctx.respond("you haven't upload any sound files")
            return

        await ctx.respond("Available sound", view=CRM.view, ephemeral=True)



class SoundBot(my_mb.MusicBot):
    def __init__(self,channel, voice , ctx, client):
        super().__init__(channel, voice , ctx, client)
        self.floder = f"data/attachments/{ctx.guild.id}"
        self.loop   = False

class BuildSoundSelect():
    def __init__(self,channel_id ,sound_class,*args , **kwargs):
        self.sound_class = sound_class
        self.label, self.sounds = self.getsounds(channel_id)
        options = [ discord.SelectOption(label=self.label[i])for i in range(len(self.label))]
        self.view = discord.ui.View(timeout=None)
        
        for i in range(len(options)//24+1):
            print(options[24*(i):24*(i+1)])
            self.select = discord.ui.Select(
                placeholder = "All sounds",
                min_values  = 1, 
                max_values  = 1,
                options = options[24*(i):24*(i+1)]
                )
            
            self.select.callback = self.callback
            self.view.add_item(self.select)

    def getsounds(self,channel_id):
        save_folder = os.path.join("data/attachments", str(channel_id))

        label, file = [], []

        for path in glob(f'{save_folder}/*.*'):
            if (path.endswith('mp3') or path.endswith('wav') ):
                label.append(os.path.basename(path[:-4]))
                file.append( os.path.basename(path) )

        return label, file

    async def callback(self, interaction):
        await self.sound_class.clear()
        which_chosen = self.label.index(self.select.values[0])
        self.sound_class.queqed = [(self.sounds[which_chosen],''), ]
        print(self.sound_class.queqed)
        await self.sound_class._next()
        # await self.sound_class.clear()
        # await interaction.followup.send_message(f"{self.label[which_chosen]}")

def setup(bot):
    bot.add_cog(Sounds(bot))