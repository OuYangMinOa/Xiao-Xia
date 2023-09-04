# Local server continue delop
from sys import platform
from utils.info     import logger
import subprocess

import time
import git



def main():
    while True:
        
        logger.info("[*] Starting server ...")
        p = subprocess.Popen(['python', 'main.py'])
        try:
            while True:
                if (git_pull_change()):
                    break
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
        # input("wait for fix ...")

    if current == repo.head.commit:
        return False
    else:
        logger.info("[*] Repo changed! Activated.")
        return True

if __name__ == '__main__':
    git_pull_change()
    main()



