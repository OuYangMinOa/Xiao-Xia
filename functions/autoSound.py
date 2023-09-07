from utils.info       import Record_folder, recording, music_user, sound_user, logger
from discord.commands import slash_command, Option
from pydub.silence    import split_on_silence, detect_nonsilent
from discord.ext      import commands
from pydub            import AudioSegment
from .sounds          import SoundBot
from datetime         import datetime
from glob             import glob


import speech_recognition as sr
import discord
import asyncio
import time
import os


class Record(discord.ext.commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="autosound",description="自動偵測語音播放音效版")
    async def autosound(self, ctx):
        await ctx.respond(f"autosound -{ctx.author.mention}")
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

                sound_user[ctx.channel.id] = SoundBot(channel, voice , ctx, self.bot)

            elif (ctx.guild.id in music_user_guild):  # in sound_user
                music_channel_id = music_user[list(music_user)[music_user_guild.index(ctx.guild.id)]].ctx.channel.id
                voice = music_user[music_channel_id].voice
                await music_user[music_channel_id].pause()
                sound_user[ctx.channel.id] = SoundBot(channel, voice , ctx, self.bot)
            else:
                voice = await channel.connect()
                sound_user[ctx.channel.id] = SoundBot(channel, voice , ctx, self.bot)


        except Exception as e:
            logger.error(e)


    
        SRS = SoundAssist( os.path.join(Record_folder,str(ctx.guild.id)),voice, ctx,self.bot,sound_user[ctx.channel.id])

        recording.update({ctx.guild.id: SRS})
        
        await SRS.threadRecord()
        # vc.start_recording(
        #     discord.sinks.WaveSink(),  # The sink type to use.
        #     # discord.Sink(encoding='wav', filters={'time': 0}),
        #     SRS.once_done,  # What to do once done.
        #     ctx.channel  # The channel to disconnect from.
        # )


    @slash_command(name="stop_autosound",description="結束 - 自動偵測語音播放音效版")
    async def stopAutoSounding(self,ctx):
        await ctx.respond(f"stop_autosound -{ctx.author.mention}",delete_after=10)
        recording[ctx.guild.id].kill()


def setup(bot):
    bot.add_cog(Record(bot))

def speech_to_text(path):
    r = sr.Recognizer() 
    sound = AudioSegment.from_wav(path)
    chunks = split_on_silence(sound,
        min_silence_len = 300,
        silence_thresh = sound.dBFS-20,
        keep_silence=100,
    )
    # normalized_sound = match_target_amplitude(sound, -20.0)
    nonsilent_data = detect_nonsilent(sound, min_silence_len=500, silence_thresh=-50, seek_step=50)
    folder_name = "audio-chunks"
    if not os.path.isdir(folder_name):
        os.mkdir(folder_name)
    whole_text = []
    time_text  = []

    for i, chunk in enumerate(nonsilent_data, start=1):
        this_time = [chunk_ for chunk_ in chunk]
        time_text.append(this_time)
        audio_chunk  = sound[this_time[0]:this_time[1]]

        chunk_filename = os.path.join(folder_name, f"chunk{i}.wav")
        audio_chunk.export(chunk_filename, format="wav")

        with sr.AudioFile(chunk_filename) as source:
            try:
                audio_listened = r.record(source)
                try:
                    text = r.recognize_google(audio_listened, language = 'zh-tw', show_all=True)
                    if text['alternative'][0]['confidence'] < 0.7:
                        text['alternative'][0]['transcript'] = "*inaudible*"
                    text = text['alternative'][0]['transcript']
                except sr.UnknownValueError as e:
                    text = "*inaudible*"
                else:                
                    whole_text.append(text)
            except:
                whole_text.append('')
                continue
    return whole_text, time_text


class SoundAssist:
    def __init__(self,saveFolder,voice, ctx,bot,soundClass):
        self.ctx         = ctx
        self.bot         = bot
        self.voice       = voice
        self.alive       = True
        self.soundClass  = soundClass
        self.saveFolder  = saveFolder
        self.waitProcess = False
        self.start_time  = datetime.now().strftime('%y-%m-%d-%H-%M-%S')
        self.getsounds(ctx.guild.id)
        os.makedirs(saveFolder,exist_ok=True)

    def getsounds(self,channel_id):
        save_folder = os.path.join("data/attachments", str(channel_id))
        label, file = [], []
        for path in glob(f'{save_folder}/*.*'):
            if (path.endswith('mp3') or path.endswith('wav') ):
                label.append(os.path.basename(path[:-4]))
                file.append( os.path.basename(path) )
        label = sorted(label, key=lambda x: len(x))
        file  = sorted(file , key=lambda x: len(label[file.index(x)] ))

        self.label, self.file =  label, file


    async def StartKeepListening(self):
        self.bot.loop.create_task(self.threadRecord())

    def kill(self):
        self.alive = False
        del recording[self.ctx.guild.id]

    async def threadRecord(self):
        print("Start Keep recording")
        
        while self.alive :
            while self.soundClass.state == 1 or self.waitProcess:
                await asyncio.sleep(1)
            self.voice.start_recording(
            discord.sinks.WaveSink(),  # The sink type to use.
            # discord.Sink(encoding='wav', filters={'time': 0}),
            self.once_done,  # What to do once done.
            self.ctx.channel)
            await asyncio.sleep(5)
            self.voice.stop_recording()
            await asyncio.sleep(1)
            
            if self.ctx.guild.voice_client not in self.bot.voice_clients:
                self.kill()

    async def once_done(self, sink: discord.sinks, channel: discord.TextChannel, *args):
        self.waitProcess = True
        if not self.alive:
            return
        # recorded_users = [  # A list of recorded users
        #     (await self.bot.fetch_user(user_id)).name
        #     for user_id, audio in sink.audio_data.items()
        # ]

        end_time = datetime.now().strftime('%y-%m-%d-%H-%M-%S')
        day_folder =  os.path.join(self.saveFolder, f'{self.start_time}~{end_time}')
        os.makedirs(day_folder,exist_ok=True)
        
        all_result = []  # save recognize words
        all_time   = []  # save recognize words time
        for user_id, audio in sink.audio_data.items():
            this_file = os.path.join(day_folder,f'{user_id}.wav')
            audio = AudioSegment.from_raw(audio.file, format="wav", sample_width=2,frame_rate=48000,channels=2)
            audio.export(this_file, format='wav')
            result, timeline = speech_to_text(this_file)
            print(user_id,":",result)
            all_result.append(result)
            all_time.append(timeline)
        
        choseLen, choseFile = 0, None

        for eachSound,eachFile in zip(self.label, self.file):
            for eachTextArr in all_result:
                for eachText in eachTextArr:
                    # print(eachText, eachSound, list(set(eachText)&set(eachSound)))
                    thisLen = len(list(set(eachText)&set(eachSound)))
                    if ( thisLen>=2 ):
                        if (thisLen > choseLen):
                            choseFile = eachFile
                        # await self.soundClass.playSound(eachFile)
                        # self.waitProcess = False
                        # return
        if (choseFile):
            await self.soundClass.playSound(choseFile)


        self.waitProcess = False
        