import googleapiclient.discovery
from utils.info     import logger, MUSIC_folder
import os
import re
import bs4
import time
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import requests


from pytube import YouTube, Playlist
from pip._vendor import requests

# grab the title of single video
def get_title(url):
    """Get  the title of a single video

    Args:
        url (str): The youtube url

    Returns:
        str: title of single video
    """
    ########## Pytube
    try:
        logger.info(f"[*] USing pytube ")
        return YouTube(url).title
    except Exception as e:
        logger.error(f"[*] Pytube faild to grab {url} title")


    ##########  googleapiclient
    for keynum in [1,2,3,4,5]:
        try:
            this_id = re.search('(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})', url, re.M|re.I).group(1)
            # print(f"[*] {this_id}")
            youtube = googleapiclient.discovery.build("youtube", "v3", developerKey = str(os.getenv(f'YOUTUBE_DEVELOPMENT_TOKEN{keynum}')))
            request = youtube.videos().list(
                part = "snippet",
                id = this_id)
            return request.execute()["items"][0]['snippet']['title']
        except Exception as e:
            logger.error(f"[*] keynum {keynum} failed")
    logger.info(f"[*] ALL keynum failed")




# grab the title and url of playlist
def grab_playlist(url,maxima_song = 25):
    """grab the title and url of playlist

    Args:
        url (str): the url of the playlist
        maxima_song (int, optional): the maxima song to grab. Defaults to 25.

    Returns:
        list[(str,str)]: A list of title and url
    """
    # logger.info(url)
    

    for keynum in [1,2,3,4,5]:
        try:
            playlist_id = re.search("list=(.*?)(?:&|$)", url, re.M|re.I).group(1)
            youtube = googleapiclient.discovery.build("youtube", "v3", developerKey = str(os.getenv(f'YOUTUBE_DEVELOPMENT_TOKEN{keynum}')))
            request = youtube.playlistItems().list(
                part = "snippet",
                playlistId = playlist_id,
                maxResults = maxima_song
            )
            response = request.execute()
            playlist_items = []
            Total_number   = 0
            while request is not None:
                response = request.execute()
                playlist_items += response["items"]
                request = youtube.playlistItems().list_next(request, response)
                Total_number += 1
                if (Total_number == maxima_song):
                    break
            playlist_set = []
            for i in playlist_items:
                this_set = (
                    i['snippet']['title'],
                    f"https://www.youtube.com/watch?v={i['snippet']['resourceId']['videoId']}"
                    )
                playlist_set.append(this_set)
            return playlist_set
        except Exception as e:
            logger.error(f"[*] keynum {keynum} failed")

    logger.info(f"[*] ALL keynum failed")

    try:
        logger.info("[*] Grabbing playlist with pytube")
        p = Playlist(url)
        count = 0
        playlist_set = []
        for item in p.videos:
            if (count>=maxima_song):
                break
            playlist_set.append(
                (item.title,item.watch_url)
                )
            time.sleep(0.01)
            count += 1
        return playlist_set
    except Exception as e:
        logger.error(f"[*] Pytube faild to grab {url} yt playlist")


async def grab_Lyrics_spotify(song_name):
    """Grab the Lyrics on the Spotify (abandoned)

    Args:
        song_name (str): song_name

    Returns:
        str: Lyrics
    """

    search_url = f"https://cse.google.com/cse?cx=partner-pub-9427451883938449%3Agd93bg-c1sx&q={song_name}#gsc.tab=0&gsc.q={song_name}&gsc.page=1"
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
    }

    logger.info("[*] Start Web grabing")
    session = AsyncHTMLSession()
    r =  await session.get(search_url)
    await r.html.arender(scrolldown = 4 , sleep = 0.1)
    logger.info("[*] Finish Web grabing")

    output = ""
    get_all_url = r.html.xpath("//a[@class='gs-title']")
    get_links = list(get_all_url)#[0]
    logger.info(f"[*] Found {len(get_links)} result")
    Found = False
    for each in get_links: 
        each_links = list(each.links)
        if (len(each_links) == 0): continue

        Lyrics_r  = requests.get(each_links[0],headers= headers).content
        soup      = bs4.BeautifulSoup(Lyrics_r,"lxml")

        find_ly   = soup.find_all("div",id="kanji")
        if (len(find_ly) !=0):
            Found = True
            output = output + "Song name : "+each.text + "\n"
            for i in find_ly:
                output = output + i.text.replace(" "," ").replace("Lyrics from Animelyrics.com","")
                output = output + "\n\n"
            break

        find_ly   = soup.find_all("td",class_="romaji")
        if (len(find_ly) !=0):
            Found = True
            output = output + "Song name : "+each.text + "\n\n\n"
            for i in find_ly:
                output = output + i.text.replace(" "," ").replace("Lyrics from Animelyrics.com","")
                output = output + "\n\n"
            break

    output = output + "Lyrics from Animelyrics.com\n"
    return Found, output

def youtubeSearch(keyword,useKeyword=True):

    for keynum in [1,2,3,4,5]:
        try:
            if (useKeyword):
                if (  os.path.isfile(os.path.join(MUSIC_folder,keyword))):
                    return (keyword,"")

            youtube = googleapiclient.discovery.build("youtube", "v3", developerKey = str(os.getenv(f'YOUTUBE_DEVELOPMENT_TOKEN{keynum}')))
            response = youtube.search().list(q=keyword,
                                            part="id,snippet",
                                            maxResults=1
                                            ).execute().get("items", [])
            # print(response)
            for record in response:
                if record["id"]["kind"] == "youtube#video":
                    title = record["snippet"]["title"]
                    youtube_id = record["id"]["videoId"]
                    youtube_url = f"https://www.youtube.com/watch?v={youtube_id}"
                    break
            if (useKeyword):
                return (keyword,youtube_url)
            else:
                return (title,youtube_url)
        except Exception as e:
            logger.error(f"[*] keynum {keynum} failed")
    logger.info(f"[*] ALL keynum failed")
    return None

def GrabSongListFromSpotify(url,start=0,end=100):
    auth_manager = SpotifyClientCredentials()
    sp = spotipy.Spotify(auth_manager=auth_manager)
    
    spId = url.split('/')[-1]
    logger.info(f"Id: {spId}")

    if ("track" in url):
        results = sp.track(spId)
        # print(results['name'],results['artists'][0]['name'])
        return [youtubeSearch(results['name']+'-'+results['artists'][0]['name']),]

    if ("artist" in url):
        results = sp.artist_top_tracks(spId)
        output = []
        for eachItem in results['tracks'][start:end]:
            thisResult = youtubeSearch(eachItem['name']+'-'+eachItem['artists'][0]['name'])
            if (thisResult):
                output.append(thisResult)
            time.sleep(0.1)
        return output
    

    if ("playlist" in url):
        results = sp.playlist_tracks(spId)
        output = []
        for eachItem in results['items'][start:end]:
            thisResult = youtubeSearch(eachItem['track']['name']+'-'+eachItem['track']['artists'][0]['name'])
            if (thisResult):
                output.append(thisResult)
            time.sleep(0.1)
        return output

if __name__ == "__main__":
    pass

    # print(get_title('http://youtu.be/NLqAF9hrVbY'))
    # import asyncio
    # loop2 = asyncio.new_event_loop()
    # loop = asyncio.get_event_loop()
    # forecast = loop.run_until_complete(
    #     grab_Lyrics_spotify("在泥濘中綻放")
    #     )
    # print(forecast[1])