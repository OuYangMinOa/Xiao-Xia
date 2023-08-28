# on raspi
from utils.info    import MASSAGE_DATA, PASS_MSG, silinece_channel, logger

import time
import socket
import requests
import threading

def is_port_in_use(port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def prompt_wes_com(text):   # use my own LLM AI

    """Prompt messages to my AI

    Returns:
        Text: AI result
    """


    
    HOST = "192.168.0.7"
    # HOST = "127.0.0.1"
    PORT = 1564


    # time.sleep(1)
    # while is_port_in_use(PORT):
    #     time.sleep(5)

    ## Socket way
    # try:
    #     mysocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     mysocket.settimeout(50)
    #     mysocket.connect((HOST, PORT))
    #     mysocket.send(text.encode())
    #     result = mysocket.recv(4096)
    #     mysocket.close()

    #     return result.decode()
    # except Exception as e:
    #     logger.error(e)
    #     return None
    

    ## change to use restful api
    prompt = {
        "promptWord":text,
        "top_p":0.2,
        "temperature":1,
        }
    response  = requests.post("http://192.168.0.10:8088/prompt",json=prompt)
    reJson = response.json()

    if (reJson["status"] =="ok"):
        return reJson["data"]["ouput"]
    else:
        logger.error(reJson["status"])
        return None




if __name__ == "__main__":
    print(
        prompt_wes_com("用戶:請自我介紹\n小俠:")
        )