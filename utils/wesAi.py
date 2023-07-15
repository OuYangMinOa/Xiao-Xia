# on raspi
from utils.info    import MASSAGE_DATA, PASS_MSG, silinece_channel, logger

import time
import socket
import threading

def is_port_in_use(port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def prompt_wes_com(text):   # use my own LLM AI

    # HOST = "192.168.0.2"
    HOST = "127.0.0.1"
    PORT = 1564

    while is_port_in_use(PORT):
        time.sleep(5)


    try:
        mysocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        mysocket.settimeout(50)
        mysocket.bind((HOST, PORT))
        mysocket.listen(10)

        client,addr = mysocket.accept()

        result = client.recv(4096)
        client.send(text.encode())
        result = client.recv(4096)
        client.close()
        return result.decode()
    except Exception as e:
        logger.error(e)
        return None


if __name__ == "__main__":
    print(
        prompt_wes_com("用戶:請自我介紹\n小俠:")
        )