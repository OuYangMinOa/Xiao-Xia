# on raspi
from utils.info    import MASSAGE_DATA, PASS_MSG, silinece_channel, logger,HOST,PORT
import socket
from aiohttp import ClientSession

def is_port_in_use(port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


async def prompt_wes_com(text):   # use my own LLM AI
    """_summary_

    Args:
        text (str): prompt text

    Returns:
        str|None: LLM AI result
    """

    
    # HOST = socket.gethostbyname(socket.gethostname()) #"192.168.133.209"
    # # print(HOST)
    # HOST = "192.168.0.7"
    # PORT = 8088


    ## change to use restful api
    prompt = {
        "promptWord":text,
        "top_p":0.2,
        "temperature":.7,
        }
    try:
        # response  = requests.post(f"http://{HOST}:{PORT}/prompt",json=prompt,timeout=10)

        async with ClientSession() as session:
            async with session.post(f"http://{HOST}:{PORT}/prompt",json=prompt,timeout=300) as resp:
                reJson = await resp.json()
    except Exception as e:
        logger.error(e)
        return None
    # reJson = resp.json()
    if (reJson["status"] =="ok"):
        return reJson["data"]["ouput"]
    else:
        logger.error(reJson["status"])
        return None
    return None



def prompt_wes_com_main(text):
    import asyncio
    return asyncio.run(prompt_wes_com(text))

if __name__ == "__main__":
    print(
        prompt_wes_com("用戶:請自我介紹\n小俠:")
        )