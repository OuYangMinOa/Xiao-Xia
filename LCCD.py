# Local server continue delop
from sys import platform
import subprocess

import time
import git



def main():
    while True:

        print("[*] Starting server ...")
        p = subprocess.Popen(['python', 'main.py'])
        try:
            while True:
                if (git_pull_change()):
                    break
                time.sleep(60)
        except Exception as e:
            print(e)
        p.terminate()


def git_pull_change():
    this_repo    = '.'
    repo = git.Repo(this_repo)
    current = repo.head.commit

    repo.remotes.origin.pull()

    if current == repo.head.commit:

        return False
    else:
        print("[*] Repo changed! Activated.")
        return True

if __name__ == '__main__':
    main()



