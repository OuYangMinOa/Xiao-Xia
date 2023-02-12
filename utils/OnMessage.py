# OnMessage.py

from utils.file_os import readfile    , addtxt
from utils.info    import MASSAGE_DATA, PASS_MSG

import openai
import random
import os
import re




openai.api_key = str(os.getenv('OPENAI_TOKEN'))
PASS_MSG  = readfile(MASSAGE_DATA)


def prompt_openai(word):
    try:
        completion = openai.Completion.create(engine="text-davinci-003",temperature= 0.5, prompt=word,max_tokens=1024)
        return completion.choices[0].text
        
    except openai.error.InvalidRequestError:
        print("[*] Prompt to many words ..., Cutting down")
        return prompt_openai("\n".join(word.split('\n')[:-1]))



async def handle_message(message):
    this_message = message.content.strip()
    print(f"[*] {message.author.name} : {this_message}")
    pass_memory_arr = []
    count = 0
    for i in range(len(PASS_MSG)-1,-1,-1):
        if ('http' not in PASS_MSG[i] and ('<@' not in PASS_MSG[i]) and  len(re.findall(r'[\u4e00-\u9fff]+',PASS_MSG[i]))>0 ):
            if (":" in PASS_MSG[i]):
                pass_memory_arr.insert(0,PASS_MSG[i])
            else:
                if ( abs(len(PASS_MSG)-i)%2 == 0):
                    pass_memory_arr.insert(0,"A:"+PASS_MSG[i])
                else:
                    pass_memory_arr.insert(0,"Q:"+PASS_MSG[i])

            count += 1
        if (count>10 or len("\n".join(pass_memory_arr)) >1000):
            break

    pass_memory = "\n".join(pass_memory_arr)
    print(pass_memory)
    if ("http" not in this_message) :
        try:
            word = "你現在是一個discord音樂機器人,名子叫小俠,可以使用/play來播放youtube上的音樂,/help可以看到小俠的全部功能,如果聽不懂的話,可以隨便回復一句幹話或句點他就好了。"+pass_memory+"。\n" + f"{message.author.name}:"+ this_message+"\nA:"
            chatgpt_result = prompt_openai(word)
            await message.channel.send(chatgpt_result)
            print(f"[*] 回復 : {chatgpt_result}")
            PASS_MSG.append(f"{message.author.name}:"+this_message)
            PASS_MSG.append("小俠:"+chatgpt_result)
            addtxt( MASSAGE_DATA,f"{message.author.name}:"+this_message.strip())
            addtxt( MASSAGE_DATA,"小俠:"+chatgpt_result.strip())
        except Exception as e:
            print(e)
            chosen_message = random.choices(PASS_MSG)[0]
            if (":" in chosen_message): chosen_message = chosen_message.split(":")[-1]
            await message.channel.send(chosen_message)