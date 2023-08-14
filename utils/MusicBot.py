## music.py
from utils.GrabYtList import *
from utils.info     import logger, music_user, sound_user, MUSIC_folder
from pytube import YouTube

import threading
import discord
import asyncio
import time
from pydub import AudioSegment
# import youtube_dl
import yt_dlp as youtube_dl
import os

youtube_dl.utils.bug_reports_message = lambda: ''




def match_target_amplitude(sound, target_dBFS):
    change_in_dBFS = target_dBFS - sound.dBFS
    return sound.apply_gain(change_in_dBFS)

class MusicBot:   
    def __init__(self,channel, voice , ctx, client):
        self.music_msg = None       # The message for current music
        self.wait_msg  = None # The message for
        self.loop      = False      # Enable loop or not
        self.volume    = 1
        self.live      = True       # Kill this Musicbot if self.live = False
        self.channel   = channel    # Voice channel
        self.channelid = channel.id # This Music serves channel Id
        self.floder    = MUSIC_folder    # Folder to store music
        self.ctxResArr = []
        self.ctx       = ctx        # ctx
        self.voice     = voice      # voice client
        self.client    = client
        self.queqed    = []         # music queqed for play
        self.passed    = []         # Played music
        self.state     = 0          # 0:not playing , 1:playing , 2:pause, 3:need to skip to continue
        self.rejoin_c  = 0          # rejoin every 20 songs
        self.dont_stop = 0          # will play untill dont_stop = 3 to check again

        # create the music floder if not exist
        os.makedirs(str(self.floder),exist_ok=True)

    # async def lyrics(self):
    #     print(f"[*] Search lyrics now playing music {self.this_song[0]}")
    #     search_word = await self.ctx.send(f"Searching {self.this_song[0]} lyrics ...")
    #     try:
    #         status, get_ly = await grab_Lyrics_spotify(self.this_song[0])
    #     except Exception as e:
    #         print(e)
    #     await search_word.delete()
    #     print(f"[*] {status}")
    #     if (status):
    #         for i in range(len(Get_ly)//1500):
    #             await self.ctx.send(Get_ly[1500*i:1500*(i+1)])
    #     else:
    #         await self.ctx.send(f"I cannot found the lyrics of {self.this_song[0]}")
    #         await self.ctx.send("Try to type !lyrics {simplified song name}")
    #         await self.ctx.send("Example : !lyrics 数码宝贝大冒险进化插曲 brave heart -> !lyrics brave heart")
    # kill this class
    async def kill(self):
        await self.clear()
        self.live   = False

    # play next music
    async def _next(self):
        if (len(self.queqed) == 0):
            logger.info("[*] Queqed song is finish")
            if (self.loop): # refill the music queqed for play with Played music
                self.queqed = self.passed
                self.passed = []
            else:
                self.state = 0
                return

        self.state = 1
        self.this_song  = self.queqed.pop(0) # get the song
        self.passed.append(self.this_song)
        

        logger.info(f"[*] playing  : {self.this_song[0]} in + {self.channelid}")
        this_song_url   = self.this_song[1]
        this_song_name  = self.this_song[0]

        for each_char in ["\\", "/", '"', "'", ":", "|"]:
            if (each_char in this_song_name):
                this_song_name = this_song_name.replace(each_char,"")
        if ("\\" in this_song_name):
            this_song_name = this_song_name.replace("\\","")
        if ("/" in this_song_name):
            this_song_name = this_song_name.replace("/","")
        if ('"' in this_song_name):
            this_song_name = this_song_name.replace('"',"#")
        if ("'" in this_song_name):
            this_song_name = this_song_name.replace("'","#")
        if (":" in this_song_name):
            this_song_name = this_song_name.replace(":","#")
        if ("|" in this_song_name):
            this_song_name = this_song_name.replace("|","#")

        song_path  = os.path.join(self.floder , this_song_name)
        if ( not os.path.isfile(song_path)):            
            self.ytl  = {
                'format': 'bestaudio/best',
                "outtmpl" : f"{song_path}",
                'noplaylist': False, 
            } 
            self.dowloading = await self.ctx.send(f'... Downloading {this_song_name}')
            try:
                print("[*] downloading ->", this_song_name,"\n")
                is_live = True
                with youtube_dl.YoutubeDL(self.ytl) as ydl:
                    ydl.cache.remove()
                    # ydl.download([this_song_url])
                    info = ydl.extract_info(this_song_url, download=False)
                    if (not info['is_live']):
                        is_live = False
                        logger.info(f"[*] Downloading {this_song_url} due to it not a live")
                        ydl.download([this_song_url])
                    else:
                        logger.info(f"[*] {this_song_url} is a live stream")
                        song_path = info['formats'][0]['url']
                # try:
                #     sound = AudioSegment.from_file(song_path)
                #     normalized_sound = match_target_amplitude(sound, -20.0)
                #     normalized_sound.export(song_path)
                # except:
                #     pass
                
                logger.info("\n[*] ------------ download successful ------------")
            except Exception as e:
                logger.error(e)
                logger.error("[*] ----- error ----- try to use pytube.")
                print("[*] redownloaded in 5 second")
                try:
                    print("[*] redownloading ->", this_song_name)
                    if (not is_live):
                        # song_path = song_path + ".mp3"
                        logger.info(f"[*] Download to {song_path}")
                        YouTube(this_song_url).streams.filter(only_audio=True).first().download(output_path=self.floder,filename=this_song_name)
                        logger.info("\n[*] ------------ download successful ------------")
                    else:
                        await self._next()
                        await self.dowloading.delete()
                        return
                    # try:
                    #     sound = AudioSegment.from_file(song_path)
                    #     normalized_sound = match_target_amplitude(sound, -20.0)
                    #     normalized_sound.export(song_path)
                    # except:
                    #     pass

                except Exception as e:
                    error_     = await self.ctx.channel.send(f':weary:  Error occurred again')
                    redownload = await self.ctx.channel.send(f':weary:  Skipping this song ... {this_song_name}')
                    logger.info("[*] error heppened again")
                    logger.info("[*] play next song")
                    logger.error(e)
                    time.sleep(1)
                    await redownload.delete()
                    await error_.delete()
                    await self.dowloading.delete()
                    await self._next()
                    return 
            await self.dowloading.delete()
        else:
            print("[*] Audio exist " )

        if (self.live == False):
            return

        if self.ctx.guild.voice_client not in self.client.voice_clients:
            print("[*] get kicked from",self.channelid)
            return

        self.music_msg = await self.ctx.channel.send(f':musical_note:  Now playing ({len(self.passed)}/{len(self.queqed)+len(self.passed)}) : {this_song_name} :musical_note:')

        FFMPEG_OPTS = {
        # 'before_options': '-reconnect_streamed 1 -reconnect_delay_max 5', 
        'options': '-vn'
        }

        # self.rejoin_c += 1
        # if (self.rejoin_c == 10):
        #     # this_source = discord.FFmpegPCMAudio(song_path, **FFMPEG_OPTS)
        #     this_source = discord.FFmpegPCMAudio(song_path, **FFMPEG_OPTS)
        #     self.voice.play(    
        #         this_source, 
        #         after=lambda e: print("[*] reconnecting the ffmpeg , error : ",e)
        #         )
        #     self.rejoin_c = 0
        #     # self.recon_msg = await self.ctx.channel.send(f':weary:   please waiting for 5 second')
        #     # await asyncio.sleep(5)
        #     await self.recon_msg.delete()

        print("[*] music start ...")
        # FFmpegPCMAudio  FFmpegOpusAudio

        this_source = discord.FFmpegPCMAudio(song_path, **FFMPEG_OPTS)
        this_source.volume = self.volume

        self.voice.play(
            this_source, 
            after = lambda e: asyncio.run_coroutine_threadsafe(self._endsong(e), self.client.loop)
            )

        self.dont_stop +=1
        if (self.dont_stop > 3):
            self.client.loop.create_task(self.check())
            
    async def check(self):
        # define the voice channel
        if (self.live == False):
            return False
        # print(self.channel.voice_states)
        member_count = len(self.channel.voice_states)
        print(f"[*] {self.channelid}, left member : {member_count}")
        if (member_count == 1):
            logger.info(f"[*] {self.channelid}, left member : {member_count}")
            logger.info(f"[*] {self.channelid}, Music stop cause no one listening")
            # await self.pause()
            await self.kill()
            await self.voice.disconnect()
            if (self.ctx.channel.id in music_user): del music_user[self.ctx.channel.id]
            if (self.ctx.channel.id in sound_user):
                for eachRes in self.ctxResArr:
                    try:
                        # sound_user[ctx.channel.id].crmView.stop()
                        await eachRes.delete_original_response()
                    except Exception as e:
                        print(e)
            if (self.ctx.channel.id in sound_user): del sound_user[self.ctx.channel.id]
            return True
        return False
    

    def StartChecking(self):
        async def WhileChecking():
            while True:
                res = await self.check()
                await asyncio.sleep(600)
                if (res):
                    break
        def LoopChecking():
            self.client.loop.create_task(WhileChecking())
        
        threading.Thread(target=LoopChecking,daemon=True).start()


    async def play_downloaded_music(self):
        musics = os.listdir(self.floder)
        for each in musics:
            self.queqed.append((each,"no url"))

        print("\n[*]",self.channelid,"-> Enqueued :",len(self.queqed), "the remaining songs will continue add in the background")
        if (self.state ==0):
            await self._next()

    async def _endsong(self,e):
        if (self.live == False):
            return
        if (self.music_msg):
            await self.music_msg.delete()
        self.state = 0

        await self._next()

    async def list(self):
        self.dont_stop = 0
        if (self.state == 0):
            await self.ctx.channel.send('No music right now,type : !play {music url}')
            return 
        output = f"{len(self.passed)}. {self.this_song[0]}     :point_left: you are here\n"
        for i in range(0,len(self.queqed)):
            output = output + f"{i+len(self.passed)+ 1}. {self.queqed[i][0]}\n"
            if (i==23):
                output = output + f"{len(self.queqed) - 24} more ... "
                break
        await self.ctx.send(output)

    async def shuffle(self):
        temp_arr = np.array(self.queqed)
        np.random.shuffle(temp_arr)
        self.queqed = [tuple(i) for i in temp_arr]
        print(self.queqed)
        await self.ctx.channel.send('Shuffled') 

    async def pause(self,msg=""):
        self.dont_stop = 0
        if (self.state == 0):
            await self.ctx.channel.send(f':poop: No music playing, type /`play url`') 
        elif (self.state == 1):
            if self.ctx.guild.voice_client not in self.client.voice_clients:
                logger.info(f"[*] get kicked from {self.channelid}")
                await self.clear()
            else:
                logger.info(f"[*] ===  pause ===   {self.channelid}")
                self.wait_msg = await self.ctx.channel.send(f':poop: Music stop, type `/pause` or `/play` to continue the music {msg}')
                self.state = 2
                self.voice.pause()
        elif (self.state==2) :
            logger.info(f"[*] ===  continue ===   {self.channelid}")
            logger.info(f"[*] plaing {self.this_song[0]} in  {self.channelid}")
            if (self.wait_msg):
                await self.wait_msg.delete()
                self.wait_msg = None
            self.state = 1
            self.voice.resume()


        elif (self.state==3) :
            logger.info(f"[*] ===  continue ===   {self.channelid}")
            logger.info(f"[*] plaing {self.this_song[0]} in  {self.channelid}")

            if (self.wait_msg):
                await self.wait_msg.delete()
                self.wait_msg = None
            self.state = 1

            self.this_song  = self.passed.pop(0)
            self.queqed.insert(0,self.this_song)

            
            await self.skip()

    async def skipnums(self,num):
        num = int(num)
        logger.info(f"[*] {self.channelid} skipping {num} of songs")
        try:
            logger.info(f"[*] skipping 1 : {self.this_song[0]}")
        except:
            pass

        for i in range(num-1):
            if (len(self.queqed)>0):
                this_song  = self.queqed.pop(0) # get the song
                logger.info(f"[*] skipping {i+2} : {this_song[0]}")
                self.passed.append(this_song)

        self.dont_stop = 0
        if (self.music_msg):
            await self.music_msg.delete()
            self.music_msg = None

        self.voice.pause()
        self.state = 0
        await self._next()

    async def skip(self):
        self.dont_stop = 0
        try:
            if (self.music_msg):
                await self.music_msg.delete()
                self.music_msg = None
        except:
            pass
        if (self.voice.is_playing()):
            self.voice.pause()
        self.state = 0
        logger.info(f"[*] {self.channelid} Skipped ")
        await self._next()

    def add_thread(self,url):
        logger.info("[*] Youtube : Adding rest in this thread ... ")
        try:
            output = grab_playlist(url,512)
        except:
            logger.info(f"[*] {self.channelid} somthing goes wrong while grabing the song")
            return
        for each in output[10:512]:
            self.queqed.append(each)
        logger.info(f"[*] {self.channelid} Adding Thread done.")
        logger.info(f"[*] Qeuqed {len(self.queqed)} songs -> {self.channelid}")

    def addThreadSpotify(self,url):
        logger.info("[*] SPotify : Adding rest in this thread ... ")
        try:
            output = GrabSongListFromSpotify(url,start=5)
        except Exception as e:
            logger.error(e)
            logger.info(f"[*] {self.channelid} somthing goes wrong while grabing the song")
            return
        for each in output:
            self.queqed.append(each)
        logger.info(f"[*] {self.channelid} Adding Thread done.")
        logger.info(f"[*] Qeuqed {len(self.queqed)} songs -> {self.channelid}")

    async def add(self,url):
        self.dont_stop = 0
        try:
            logger.info(f"[*] {url}")
            
            if (self.live == False):
                logger.info("[*] I'm dead")
                return
            
            if ("http" not in url):
                tempWord = await self.ctx.send(f'Searching for {url} ... ')
                self.queqed.append(youtubeSearch(url,useKeyword=False))
                await tempWord.delete()


            elif ("spotify" in url):  
                self.queqed.extend( GrabSongListFromSpotify(url,start=0,end=5) )

                threading.Thread(target = self.addThreadSpotify, args=(url,),daemon=True).start()
                logger.info(f"[*] Queqed : {self.queqed}")
            elif ("list" in url):
                logger.info(f"[*] Adding a play list in {self.channelid}")
                try:
                    output = grab_playlist(url,10)
                    logger.info("[*] grab_playlist successful")

                except Exception as e:
                    logger.info(f"[*] somthing goes wrong while grabing the song")
                    logger.error(e)
                    await self.ctx.send(f'oops... somthing goes wrong, I cannot this music')
                    await self.ctx.send('Try "!play music" to play local music')
                    return
                for each in output[0:10]:
                    self.queqed.append(each)

                threading.Thread(target = self.add_thread, args=(url,),daemon=True).start()
                logger.info(f"[*] Queqed : {self.queqed}")

            else:
                this_title = get_title(url)
                logger.info(f"[*] Adding a single video {this_title} in {self.channelid}")
                self.queqed.append((this_title,url))

            logger.info(f"\n[*] {self.channelid} -> Enqueued : {len(self.queqed)} the remaining songs will continue add in the background")

            if (self.state ==0):
                await self._next()
        except Exception as e:
            logger.error(e)
            #await self.ctx.send(f'oops... somthing goes wrong, I cannot play all the music')
        
    async def clear(self):
        try:
            if (self.music_msg):
                await self.music_msg.delete()
                self.music_msg = None
            if (self.wait_msg):
                await self.wait_msg.delete()
                self.wait_msg = None
        except Exception as e:
            logger.error(e)

        self.state = 0
        self.voice.pause()
        self.queqed = []
        self.passed = []

