
![](https://img.shields.io/github/pipenv/locked/dependency-version/ncuphysics/hack_bot/py-cord)
![](https://img.shields.io/bower/l/mi)

# Installation

This bot is develop base on [python](https://www.python.org). Python3 is require for installation and ffmpeg for audio procession. Here are the procedure to run Hack bot locally.

1. install python virtual environment
    ```shell
    sudo pip install pipenv
    pipenv install
    ```
2. add personal discord token 

	Edit  `.env_example` and rename the file to `.env`
    
3. Install ffmpeg
	For Windows: [tutorial](https://blog.gregzaal.com/how-to-install-ffmpeg-on-windows/)

	For Mac: `brew install ffmpeg`

    For Linux : `sudo apt-install ffmpeg`

3. activate virtual environment and run
    ```shell
    pipenv shell
    python3 main.py
    ```
