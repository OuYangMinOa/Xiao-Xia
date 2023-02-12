# Local server continue delop
import subprocess
import time
from sys import platform
import git



def main():
    while True:
        if platform == "linux" or platform == "linux2":
            p = subprocess.Popen(['python3', 'main.py'])

        else:
            p = subprocess.Popen(['python', 'main.py'])
        while git_pull_change():
            time.sleep(300)
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



