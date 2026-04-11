# on raspi
from utils.info    import MASSAGE_DATA, PASS_MSG, silinece_channel, logger,HOST,PORT, XioaXiaContent
import socket
from aiohttp import ClientSession
import google.generativeai as genai
from dotenv import load_dotenv
import os
import re

THOUGHT_RE = re.compile(r"<\|channel\|?>thought.*?<\|?channel\|?>\s*", re.DOTALL)

def strip_thought(text: str) -> str:
    return THOUGHT_RE.sub("", text).strip()

def is_port_in_use(port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API"))

async def prompt_wes_com(text : str):   # use my own LLM AI
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

    # ## change to use restful api
    # prompt = {
    #     "promptWord":text,
    #     "top_p":0.2,
    #     "temperature":.7,
    #     }
    # try:
    #     # response  = requests.post(f"http://{HOST}:{PORT}/prompt",json=prompt,timeout=10)

    #     async with ClientSession() as session:
    #         async with session.post(f"http://{HOST}:{PORT}/prompt",json=prompt,timeout=300) as resp:
    #             reJson = await resp.json()
    # except Exception as e:
    #     logger.error(e)
    #     return None
    # # reJson = resp.json()
    # if (reJson["status"] =="ok"):
    #     return reJson["data"]["ouput"]
    # else:
    #     logger.error(reJson["status"])
    #     return None
    # return None

    # 1. 設定您的 API 金鑰
    

    # 2. 初始化 Gemma 4 31B 模型
    # 注意：模型名稱為 'models/gemma-4-31b-it'
    model = genai.GenerativeModel('gemma-4-31b-it', system_instruction=XioaXiaContent)
    print("使用 model gemma4")
    print(text)
    response = model.generate_content(contents=text)
    raw_text = response.text
    print(raw_text)
    # 使用正則表達式移除 <think> 到 </think> 之間的所有內容
    # re.DOTALL 確保正則表達式可以跨越多行進行匹配
    cleaned_text = "".join([line for line in raw_text.splitlines() if not line.strip().startswith("*")])
    # 去除頭尾可能殘留的空白與換行符號
    return cleaned_text.strip()

def prompt_wes_com_main(text):
    import asyncio
    return asyncio.run(prompt_wes_com(text))

if __name__ == "__main__":
    print(
        prompt_wes_com("用戶:請自我介紹\n小俠:")
        )