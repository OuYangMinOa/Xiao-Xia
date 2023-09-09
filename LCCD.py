# Local server continue delop
from sys import platform
from utils.info     import logger
import subprocess

import time
import git
import os


def main():
    while True:
        
        logger.info("[*] Starting server ...")
        p = subprocess.Popen(['python', 'main.py'])
        try:
            while True:
                result = git_pull_change()
                if (result==0):
                    break
                if (result==2):
                    logger.info("[*] Ignore error")
                time.sleep(10)
        except Exception as e:
            logger.error(e)
        p.terminate()


def git_pull_change():
    try:
        this_repo    = '.'
        repo = git.Repo(this_repo)
        current = repo.head.commit

        repo.remotes.origin.pull(force=True)
    except Exception as e:
        logger.error(e)
        return 2

    if current == repo.head.commit:
        return 1
    else:
        logger.info("[*] Repo changed! Activated.")
        return 0

if __name__ == '__main__':
    git_pull_change()
    main()



