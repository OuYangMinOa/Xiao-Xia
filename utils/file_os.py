from functools import partial
from operator  import ne, eq
import os

def readfile(filename):
    if (os.path.isfile(filename)):
        with open(filename,"r",encoding="utf-8") as f:
            out = f.read().split("\n")
        out = [x for x in out if x != '']
        return out
    else:
        with open(filename,"w",encoding="utf-8") as f:
            pass
        return []


def addtxt(filename,msg):
    if (os.path.isfile(filename)):
        with open(filename,"a",encoding="utf-8") as f:
            out = f.write(f"{msg}\n")
        return out
    else:
        with open(filename,"w",encoding="utf-8") as f:
            out = f.write(f"{msg}\n")
        return out


if (__name__=="__main__"):
    print(readfile("hi.txt"))