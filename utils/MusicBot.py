## music.py
from utils.GrabYtList import *
from utils.yt_music_grabber import YouTubeDownloader
from utils.info     import logger, music_user, sound_user, MUSIC_folder
from pytube import YouTube

import utils.loudness as loudness
import utils.music_ui as music_ui



import threading
import unicodedata
import hashlib
import discord
import asyncio
import random
import html
import time
import re
# import youtube_dl
import yt_dlp as youtube_dl
import os

# yt-dlp calls this with keyword args (e.g. before=...); a bare `lambda: ''`
# raises TypeError there and hides the real download error
youtube_dl.utils.bug_reports_message = lambda *args, **kwargs: ''


# Characters that are illegal in a Windows filename (\ / : * ? " < > |) plus '#',
# which breaks the download / playback chain even though the filesystem accepts it.
ILLEGAL_FILENAME_CHARS = '\\/:*?"<>|#'

# Linux caps a single filename at 255 bytes and Windows caps the whole path at 260
# characters, so a long title has to be trimmed before it ever touches the disk.
MAX_FILENAME_BYTES = 150


def safe_song_filename(title, fallback="unknown"):
    """Turn a video title into a filename that works on both Windows and Linux.

    Args:
        title (str): the raw video title
        fallback (str, optional): name to use when nothing is left after cleaning

    Returns:
        str: a sanitized, length limited filename
    """
    # The YouTube Data API hands back HTML escaped titles (&amp; , &#39; ...)
    name = html.unescape(str(title or ''))
    name = ''.join(
        ch for ch in name
        if ch not in ILLEGAL_FILENAME_CHARS and unicodedata.category(ch)[0] != 'C'
    )
    name = ' '.join(name.split())
    name = name.strip('. ')          # Windows rejects trailing dots and spaces
    if (not name):
        name = fallback

    encoded = name.encode('utf-8')
    if (len(encoded) > MAX_FILENAME_BYTES):
        # keep two different long titles from collapsing onto the same file
        suffix  = '-' + hashlib.md5(encoded).hexdigest()[:8]
        cut     = encoded[:MAX_FILENAME_BYTES - len(suffix)]
        name    = cut.decode('utf-8', 'ignore').rstrip() + suffix

    return name


async def probe_duration(path):
    """Length of an audio file in seconds (read from ffmpeg's header dump), or None."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-nostdin", "-hide_banner", "-i", path,
            stdout = asyncio.subprocess.DEVNULL,
            stderr = asyncio.subprocess.PIPE,
        )
        _, stderr = await asyncio.wait_for(proc.communicate(), 10)
    except Exception as e:
        logger.error(f"[*] probing the duration of {path} failed : {e}")
        return None
    match = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", stderr.decode("utf-8", "ignore"))
    if (not match):
        return None
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)



async def resolve_songs(url, limit=10):
    """Turn a url / search keyword into songs without blocking the event loop.

    Args:
        url (str): YouTube video / playlist url, Spotify url, or words to search
        limit (int): at most this many songs of a playlist

    Returns:
        (list[(str,str)], bool, str): (title, url) pairs, whether the playlist may have
        more than `limit` songs, and "single" or "playlist"
    """
    if ("http" not in url):
        found = await asyncio.to_thread(youtubeSearch, url, False)
        return ([found] if found else []), False, "single"

    if ("spotify" in url):
        songs = await asyncio.to_thread(GrabSongListFromSpotify, url, 0, limit)
        songs = [each for each in songs or [] if each]
        if ("track" in url):
            return songs, False, "single"
        return songs, len(songs) >= limit, "playlist"

    if ("list=" in url):
        songs = await asyncio.to_thread(grab_playlist, url, limit)
        if (songs):
            return songs, len(songs) >= limit, "playlist"
        logger.info("[*] Can't grab list, adding single music.")

    title = await asyncio.to_thread(get_title, url)
    return [(title or url, url)], False, "single"



class MusicBot:
    SHOW_PANEL = True   # post the now playing panel (the soundboard subclass turns it off)

    def __init__(self,channel, voice , ctx, client):
        self.panel     = None       # the now playing message
        self.view      = None       # the buttons attached to self.panel
        self.ui_status = "idle"     # idle / downloading / playing / paused (what the panel shows)
        self.last_action = ""       # footer of the panel, e.g. "⏭️ someone skipped ..."
        self.requesters  = {}       # song url -> mention of who asked for it
        self.duration  = None       # length of the current song in seconds
        self.is_stream = False      # current song is a live stream
        self.this_song = None
        self._panel_lock    = asyncio.Lock()
        self._progress_task = None
        self.loop      = False      # Enable loop or not
        self.volume    = 1
        self.live      = True       # Kill this Musicbot if self.live = False
        self.channel   = channel    # Voice channel
        self.channelid = channel.id # This Music serves channel Id
        self.floder    = MUSIC_folder    # Folder to store music
        self.ctxResArr = []
        self.ctx       = ctx        # ctx
        self.voice     = voice      # voice client
        self.client    = client     # bot
        self.queqed    = []         # music queqed for play
        self.passed    = []         # Played music
        self.state     = 0          # 0:not playing , 1:playing , 2:pause, 3:need to use next_() to continue
        self.rejoin_c  = 0          # rejoin every 20 songs
        self.dont_stop = 0          # will play untill dont_stop = 3 to check again
        self.StartCount = False     # True while a track is playing (/say and sounds wait on it)
        self.resume_at  = 0         # seconds into the next track to start from (-ss)
        self._pos_base  = 0         # playback position when the clock below was started
        self._play_t0   = None      # time.monotonic() when playback (re)started, None while paused

        # create the music floder if not exist
        os.makedirs(str(self.floder),exist_ok=True)

    # ------------------------------------------------------------ position

    def position(self):
        """Seconds into the current track."""
        if (self._play_t0 is None):
            return self._pos_base
        return self._pos_base + time.monotonic() - self._play_t0

    # /say and the soundboard read the position before interrupting a song and
    # write it back so the song resumes from there
    @property
    def startTime(self):
        return int(self.position())

    @startTime.setter
    def startTime(self, seconds):
        self.resume_at = seconds
        if (self._play_t0 is None):
            self._pos_base = seconds

    def _freeze_position(self):
        self._pos_base = self.position()
        self._play_t0  = None

    def _resume_position(self):
        if (self._play_t0 is None):
            self._play_t0 = time.monotonic()

    # ------------------------------------------------------------ panel

    def note(self, text):
        """Set the line shown at the bottom of the panel."""
        self.last_action = text

    def _show_panel_for(self, song):
        if (not self.SHOW_PANEL or not song):
            return False
        # /say plays its tts clip with an empty url, autosound plays empty.wav
        return song[1] != "" and song[0] != "empty.wav"

    async def update_panel(self, move=False):
        """Redraw the now playing panel.

        Args:
            move (bool): re-post the panel at the bottom of the channel when other
                messages were sent after it; otherwise it is edited where it is.
        """
        if (not self.SHOW_PANEL or not self.live):
            return
        try:
            await self._update_panel(move)
        except Exception as e:
            # the panel is only a view of the player; never let it stop the music
            logger.error(f"[*] {self.channelid} updating the panel failed : {e!r}")

    async def _update_panel(self, move):
        async with self._panel_lock:
            channel = self.ctx.channel
            embed   = music_ui.player_embed(self)
            idle    = self.ui_status not in ("downloading", "playing", "paused")

            if (self.panel is not None):
                at_bottom = getattr(channel, "last_message_id", None) == self.panel.id
                if (at_bottom or not move):
                    try:
                        if (idle):
                            self._drop_view()
                        elif (self.view is not None):
                            self.view.sync_buttons()
                        await self.panel.edit(embed=embed, view=self.view)
                        return
                    except discord.NotFound:
                        self.panel = None
                    except discord.HTTPException as e:
                        logger.error(f"[*] {self.channelid} editing the panel failed : {e}")
                        return
                else:
                    await self._delete_panel()

            if (idle and self.panel is None):
                return
            self._drop_view()
            self.view = None if idle else music_ui.PlayerView(self)
            try:
                self.panel = await channel.send(embed=embed, view=self.view)
            except discord.HTTPException as e:
                logger.error(f"[*] {self.channelid} sending the panel failed : {e}")
                return

        if (self._progress_task is None or self._progress_task.done()):
            self._progress_task = asyncio.create_task(self._progress_loop())

    def _drop_view(self):
        if (self.view is not None):
            self.view.stop()
            self.view = None

    async def _delete_panel(self):
        self._drop_view()
        if (self.panel is not None):
            try:
                await self.panel.delete()
            except discord.HTTPException:
                pass
            self.panel = None

    async def _progress_loop(self):
        while self.live and self.panel is not None:
            await asyncio.sleep(music_ui.PROGRESS_REFRESH)
            if (self.ui_status == "playing" and self.state == 1 and self._show_panel_for(self.this_song)):
                await self.update_panel()

    async def _notice(self, text, seconds=8):
        """A short message that removes itself."""
        try:
            await self.ctx.channel.send(embed=music_ui.info_embed(text, music_ui.COLOR_ERROR), delete_after=seconds)
        except discord.HTTPException as e:
            logger.error(f"[*] {self.channelid} notice failed : {e}")

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
        for eachRes in self.ctxResArr:
            try:
                if (isinstance(eachRes,discord.WebhookMessage) or isinstance(eachRes,discord.Message)):
                    await eachRes.delete()
                else:
                    await eachRes.delete_original_response()
                self.ctxResArr.remove(eachRes)
            except Exception as e:
                logger.error(f"[*] Delete original response : {e}")

        await self.clear(refresh_panel=False)
        self.live   = False
        await self._delete_panel()
        if (self._progress_task is not None):
            self._progress_task.cancel()

    async def leave(self):
        """Stop everything, disconnect and forget this bot."""
        await self.kill()
        try:
            await self.voice.disconnect()
        except Exception as e:
            logger.error(f"[*] {self.channelid} disconnect failed : {e}")
        key = self.ctx.channel.id
        if (music_user.get(key) is self):
            del music_user[key]
        # the soundboard of this channel shares the voice client that just disconnected
        if (key in sound_user and sound_user[key] is not self):
            await sound_user[key].kill()
            del sound_user[key]
        if (sound_user.get(key) is self):
            del sound_user[key]
        logger.info(f"[*] leaving {self.channelid}")

    # play next music
    async def _next2(self):
        threading.Thread(target=self.thread_next,daemon=True).start()

    def thread_next(self):
        self.client.loop.create_task(self._next())

    def countSec(self, offset=0):
        ## start the clock of the track that just started playing
        self.StartCount = True
        self._pos_base  = offset
        self._play_t0   = time.monotonic()

    async def _next(self):

        self.StartCount = False  ##
        self._freeze_position()

        if (len(self.queqed) == 0):
            logger.info("[*] Queqed song is finish")
            if (self.loop and len(self.passed) > 0): # refill the music queqed for play with Played music
                self.queqed = self.passed
                self.passed = []
            else:
                self.state = 0
                if (self.ui_status != "idle" and self._show_panel_for(self.this_song)):
                    self.ui_status = "idle"
                    await self.update_panel()
                return

        self.state = 1
        self.this_song  = self.queqed.pop(0) # get the song
        self.passed.append(self.this_song)
        self.duration   = None
        self.is_stream  = False
        show_panel      = self._show_panel_for(self.this_song)


        logger.info(f"[*] playing  : {self.this_song[0]} in + {self.channelid}")
        this_song_url   = self.this_song[1]
        display_name    = str(self.this_song[0])          # shown in discord
        this_song_name  = safe_song_filename(display_name) # written to the disk

        # songs cached before the sanitizer existed still live under their raw name
        if (('/' not in display_name) and (os.sep not in display_name)
                and os.path.isfile(os.path.join(self.floder, display_name))):
            this_song_name = display_name

        song_path  = os.path.join(self.floder , this_song_name)
        is_stream  = False   # True when we play a live url instead of a local file
        if ( not os.path.isfile(song_path)):
            # download with yt_download
            if (show_panel):
                self.ui_status = "downloading"
                await self.update_panel(move=True)
            is_yt_downloader_succeed = True
            try:
                async with YouTubeDownloader() as downloader:
                    await downloader.download_mp3(
                        yt_url = this_song_url,
                        download_folder = self.floder,
                        filename = this_song_name,                    
                    )
            except Exception as e:
                is_yt_downloader_succeed = False
                logger.error(f"[*] YouTubeDownloader failed : {e}")

            if not is_yt_downloader_succeed:
                logger.info("[*] Youtube Downloader failed, try to use youtube_dl")
                # download with youtube_dl
                self.ytl  = {
                    'format': 'bestaudio/best',
                    "outtmpl" : f"{song_path}",
                    'noplaylist': False, 
                } 
                
                try:
                    print("[*] downloading ->", this_song_name,"\n")
                    is_live = False   # unknown until extract_info succeeds; still let pytube try
                    with youtube_dl.YoutubeDL(self.ytl) as ydl:
                        ydl.cache.remove()
                        # ydl.download([this_song_url])
                        info = ydl.extract_info(this_song_url, download=False)
                        if (not info.get('is_live')):
                            logger.info(f"[*] Downloading {this_song_url} due to it not a live")
                            ## download with blocking ...
                            # ydl.download([this_song_url])
                            ## download without blocking ...
                            loop = asyncio.get_event_loop()
                            await loop.run_in_executor(None, lambda url:ydl.download(url), [this_song_url] )
                        else:
                            is_live = True
                            logger.info(f"[*] {this_song_url} is a live stream")
                            song_path = info['formats'][0]['url']
                            is_stream = True
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
                            # YouTube(this_song_url).streams.filter(only_audio=True).first().download(output_path=self.floder,filename=this_song_name)
                            loop = asyncio.get_event_loop()
                            await loop.run_in_executor(None, 
                                                    lambda x:YouTube(this_song_url
                                                                        ).streams.filter(only_audio=True
                                                                                        ).first().download(
                                                                                            output_path=self.floder,filename=this_song_name) ,
                                                    None )
                            logger.info("\n[*] ------------ download successful ------------")
                        else:
                            await self._next()
                            return
                        # try:
                        #     sound = AudioSegment.from_file(song_path)
                        #     normalized_sound = match_target_amplitude(sound, -20.0)
                        #     normalized_sound.export(song_path)
                        # except:
                        #     pass

                    except Exception as e:
                        logger.info("[*] error heppened again")
                        logger.info("[*] play next song")
                        logger.error(e)
                        await self._notice(f"😩 下載失敗，跳過 {music_ui.shorten(display_name, 80)}")
                        await self._next()
                        return
        else:
            print("[*] Audio exist " )

        if (self.live == False):
            return

        if self.ctx.guild.voice_client not in self.client.voice_clients:
            print("[*] get kicked from",self.channelid)
            return

        if (not is_stream) and (not os.path.isfile(song_path)):
            logger.error(f"[*] {song_path} is missing after downloading, skip this song")
            await self._notice(f"😩 下載失敗，跳過 {music_ui.shorten(display_name, 80)}")
            await self._next()
            return

        start_at       = self.resume_at
        self.resume_at = 0
        FFMPEG_OPTS = {
        # 'before_options': '-reconnect_streamed 1 -reconnect_delay_max 5',
        'before_options':f"-ss {start_at}",
        'options': '-vn'
        }
        if (not is_stream):
            # bring every song / sound clip to the same perceived loudness
            loudness_filter = await loudness.get_filter(song_path)
            if (loudness_filter):
                FFMPEG_OPTS['options'] += f' -af {loudness_filter}'

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

        self.countSec(start_at)

        self.voice.play(
            this_source,
            after = lambda e: asyncio.run_coroutine_threadsafe(self._endsong(e), self.client.loop)
            )

        self.is_stream = is_stream
        if (show_panel):
            if (not is_stream):
                self.duration = await probe_duration(song_path)
            self.ui_status = "playing"
            await self.update_panel(move=True)

    async def check(self):
        # define the voice channel
        if (self.live == False):
            return True
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
                        if (isinstance(eachRes,discord.WebhookMessage) or isinstance(eachRes,discord.Message)):
                            await eachRes.delete()
                        else:
                            await eachRes.delete_original_response()
                        
                    except Exception as e:
                        logger.error(f"[*] Delete original response : {e}")
            if (self.ctx.channel.id in sound_user): del sound_user[self.ctx.channel.id]
            return True
        

        ## if left the channel
        if (self.ctx.guild.voice_client not in self.client.voice_clients):
            logger.info("[*] bot not in voice client")
            await self.kill()
            if (self.ctx.channel.id in music_user): del music_user[self.ctx.channel.id]
            if (self.ctx.channel.id in sound_user):
                for eachRes in self.ctxResArr:
                    try:
                        if (isinstance(eachRes,discord.WebhookMessage) or isinstance(eachRes,discord.Message)):
                            await eachRes.delete()
                        else:
                            await eachRes.delete_original_response()
                    except Exception as e:
                        logger.error(f"[*] Delete original response : {e}")
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
        self.state = 0

        await self._next()

    async def _safe_next(self):
        try:
            await self._next()
        except Exception as e:
            logger.error(f"[*] {self.channelid} playing the next song failed : {e!r}")
            if (not self.voice.is_playing()):
                self.state = 0

    async def shuffle(self):
        random.shuffle(self.queqed)
        await self.update_panel()

    async def set_loop(self, enabled, who=None):
        self.loop = enabled
        if (who):
            self.note(f"🔁 {who} 開啟了循環播放" if enabled else f"➡️ {who} 關閉了循環播放")
        if (enabled and self.state == 0 and len(self.passed) > 0):
            await self.skip()     # the queue already ran out; start it over
        else:
            await self.update_panel()

    async def toggle_pause(self):
        if (self.state == 0 and len(self.queqed) > 0):
            await self.skip()
        else:
            await self.pause()

    async def pause(self,msg=""):
        self.dont_stop = 0
        self.StartCount = False
        if (msg):
            self.note(msg)
        if (self.state == 0):
            pass
        elif (self.state == 1): # is playing
            if self.ctx.guild.voice_client not in self.client.voice_clients:
                logger.info(f"[*] get kicked from {self.channelid}")
                await self.clear()
            else:
                logger.info(f"[*] ===  pause ===   {self.channelid}")
                self.state = 2
                self.voice.pause()
                self._freeze_position()
                if (self._show_panel_for(self.this_song)):
                    self.ui_status = "paused"
                    await self.update_panel()
        elif (self.state==2) :
            logger.info(f"[*] ===  continue ===   {self.channelid}")
            logger.info(f"[*] plaing {self.this_song[0]} in  {self.channelid}")
            self.state = 1
            self.StartCount = True
            self.voice.resume()
            self._resume_position()
            if (self._show_panel_for(self.this_song)):
                self.ui_status = "playing"
                await self.update_panel()


        elif (self.state==3) :
            logger.info(f"[*] ===  continue ===   {self.channelid}")
            logger.info(f"[*] plaing {self.this_song[0]} in  {self.channelid}")
            if( len(self.passed) >0):
                self.this_song  = self.passed.pop()
                self.queqed.insert(0,self.this_song)

                self.state = 1
                await self._next()

    async def skipnums(self,num):
        self.StartCount = False


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
        self.voice.pause()
        self.state = 0
        await self._next()

    async def skip(self):
        self.dont_stop = 0
        self.StartCount = False

        if (self.voice.is_playing()):
            self.voice.pause()
        self.state = 0
        logger.info(f"[*] {self.channelid} Skipped ")
        await self._next()

    async def previous(self):
        """Play the song before the current one again."""
        if (len(self.passed) < 2):
            return
        current  = self.passed.pop()
        previous = self.passed.pop()
        self.queqed.insert(0, current)
        self.queqed.insert(0, previous)
        await self.skip()

    def _remember_requester(self, songs, requester):
        if (requester):
            for each in songs:
                self.requesters[each[1]] = requester

    def add_thread(self,url,requester=None):
        logger.info("[*] Youtube : Adding rest in this thread ... ")
        try:
            output = grab_playlist(url,512)
        except:
            logger.info(f"[*] {self.channelid} somthing goes wrong while grabing the song")
            return
        self._remember_requester(output[10:512], requester)
        for each in output[10:512]:
            self.queqed.append(each)
        logger.info(f"[*] {self.channelid} Adding Thread done.")
        logger.info(f"[*] Qeuqed {len(self.queqed)} songs -> {self.channelid}")

    def addThreadSpotify(self,url,requester=None):
        logger.info("[*] SPotify : Adding rest in this thread ... ")
        try:
            output = [each for each in GrabSongListFromSpotify(url,start=5) or [] if each]
        except Exception as e:
            logger.error(e)
            logger.info(f"[*] {self.channelid} somthing goes wrong while grabing the song")
            return
        self._remember_requester(output, requester)
        for each in output:
            self.queqed.append(each)
        logger.info(f"[*] {self.channelid} Adding Thread done.")
        logger.info(f"[*] Qeuqed {len(self.queqed)} songs -> {self.channelid}")

    async def _resolve(self, url):
        """Turn what the user typed into songs.

        Returns:
            (list[(str,str)], callable|None, str): the songs to queue now, a function that
            queues the rest in a background thread, and "single" or "playlist"
        """
        spotify = "spotify" in url
        songs, more, kind = await resolve_songs(url, limit = 5 if spotify else 10)
        if (not more):
            return songs, None, kind
        return songs, (self.addThreadSpotify if spotify else self.add_thread), kind

    async def add(self, url, next=False, requester=None):
        """Queue a url / search keyword and start playing if nothing is playing.

        Returns:
            dict: {"ok": False, "error": str} or a summary for music_ui.added_embed
        """
        self.dont_stop = 0
        logger.info(f"[*] {url}")
        if (self.live == False):
            logger.info("[*] I'm dead")
            return {"ok": False, "error": "播放器已經關閉了，再 `/play` 一次試試"}

        try:
            songs, background, kind = await self._resolve(url)
        except Exception as e:
            logger.error(f"[*] {self.channelid} resolving {url} failed : {e}")
            songs, background, kind = [], None, "single"
        if (not songs):
            return {"ok": False, "error": "找不到這首歌，換個連結或關鍵字試試"}

        self._remember_requester(songs, requester)
        if (next):
            self.queqed[0:0] = songs
        else:
            self.queqed.extend(songs)

        if (background):
            threading.Thread(target=background, args=(url, requester), daemon=True).start()
        logger.info(f"[*] {self.channelid} -> Enqueued : {len(self.queqed)}")

        starting = (self.state == 0)
        position = 0 if starting else (1 if next else len(self.queqed))
        if (starting):
            # mark busy now so a second /play right after this doesn't start another song
            self.state = 1
            asyncio.create_task(self._safe_next())
        else:
            await self.update_panel()

        first = songs[0]
        if (kind == "playlist"):
            return {"ok": True, "kind": "playlist", "count": len(songs), "more": background is not None, "first": first}
        return {"ok": True, "kind": "single", "title": first[0], "url": first[1], "position": position}

    async def clear(self, refresh_panel=True):
        self.state = 0
        self.voice.pause()
        self._freeze_position()
        self.queqed = []
        self.passed = []
        if (refresh_panel and self.ui_status != "idle" and self.panel is not None):
            self.ui_status = "idle"
            await self.update_panel()
