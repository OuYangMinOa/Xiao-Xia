# on raspi
from utils.info    import MASSAGE_DATA, PASS_MSG, silinece_channel, logger,HOST,PORT, XioaXiaContent
import socket
from aiohttp import ClientSession
import google.genai as genai
from google.genai import types
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
    # 定義 Google Search 工具           
    grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
    )

    config = types.GenerateContentConfig(
        system_instruction=XioaXiaContent,
        tools=[grounding_tool]
    )
    client = genai.Client(api_key = os.getenv("GEMINI_API"))
    print("使用 model gemma-4-31b-it")
    print(text)
    response = client.models.generate_content(
        model='gemma-4-31b-it',  
        contents=text,
        config=config,
    )
    raw_text = response.text
    return raw_text

def prompt_wes_com_main(text):
    import asyncio
    return asyncio.run(prompt_wes_com(text))

if __name__ == "__main__":
    print(
        prompt_wes_com("用戶:請自我介紹\n小俠:")
        )