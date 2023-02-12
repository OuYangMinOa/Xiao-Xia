

# <p align="center"><img src="https://github.com/OuYangMinOa/Xiao-Xia/blob/main/icon.png" width = '200' height="200" ></img> </p>

# <p align="center">歐陽小俠</p>
![](https://img.shields.io/github/pipenv/locked/dependency-version/ncuphysics/hack_bot/py-cord)
![](https://img.shields.io/bower/l/mi)

# Installation

If you want to build your own bot, the bot is develop base on [python](https://www.python.org). Python3 is require for installation and ffmpeg for audio procession. Here are the procedure to run Hack bot locally.

1. Install python virtual environment
    ```shell
    sudo pip install pipenv
    pipenv install
    ```
2. Add personal discord token 

	Edit  `.env_example` and rename the file to `.env`
    
3. Install ffmpeg
	For Windows: [tutorial](https://blog.gregzaal.com/how-to-install-ffmpeg-on-windows/)

	For Mac: `brew install ffmpeg`

    For Linux : `sudo apt-install ffmpeg`

3. Activate virtual environment and run
    ```shell
    pipenv shell
    python3 main.py
    ```

# :rocket: Getting Started

* Invite with this <a href="https://discord.com/api/oauth2/authorize?client_id=851419786465771520&permissions=8&scope=bot%20applications.commands">url</a>  

# <p align="center"> :sparkles: Features :sparkles: </p>

# :notes: Music

* `/play {url}` to play music on youtube.
* `/skip` to skip the song.
* `/pause` to pause the song.
* `/list` to show the playlist
* `/loop` to loop current song.
* `/clear`  to clear the playlist
* `/leave` to leave the voice channel.

# :laughing: chat
* I will reply all message, if you want to shut it down, use `/silence` to shut me up
* Use `/talk` so I can keep talking