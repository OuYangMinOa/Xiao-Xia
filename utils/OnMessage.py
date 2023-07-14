# OnMessage.py

from utils.file_os import readfile    , addtxt
from utils.info    import MASSAGE_DATA, PASS_MSG, silinece_channel, logger
from utils.wesAi   import prompt_wes_com
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
        logger.error("[*] Prompt to many words ..., Cutting down")
        return prompt_openai("\n".join(word.split('\n')[:-1]))


    
async def handle_message(message):
    this_message = message.content.strip()
    logger.info(f"[*] {message.author.name} : {this_message}")
    if (message.channel.id in silinece_channel):
        return
    if (this_message == ""):
        return 
    pass_memory_arr = []
    count = 0
    for i in range(len(PASS_MSG)-1,-1,-1):
        if ('http' not in PASS_MSG[i] and ('<@' not in PASS_MSG[i]) and  len(re.findall(r'[\u4e00-\u9fff]+',PASS_MSG[i]))>0 ):
            pass_memory_arr.insert(0,PASS_MSG[i])
            count += 1
        if (len("\n".join(pass_memory_arr)) >512):
            break

    pass_memory = "\n".join(pass_memory_arr)
    # print(pass_memory)
    if ("http" not in this_message) :

        word = "你現在是一個來自台灣discord機器人,名字叫歐陽小俠。\n"+ f"{message.author.name}:"+ this_message+"\n小俠:"  # +pass_memory+"。\n" 
        chatgpt_result = prompt_wes_com(word)    ## prompt_openai(word)
        if chatgpt_result:
            await message.channel.send(chatgpt_result)
            logger.info(f"[*] 回復 : {chatgpt_result}")
            PASS_MSG.append(f"{message.author.name}:"+this_message)
            PASS_MSG.append("小俠:"+chatgpt_result)
            addtxt( MASSAGE_DATA,f"{message.author.name}:"+this_message.strip())
            addtxt( MASSAGE_DATA,"小俠:"+chatgpt_result.strip())
        else:
            chosen_message = random.choices(PASS_MSG)[0]
            if (":" in chosen_message): chosen_message = chosen_message.split(":")[-1]

            await message.channel.send(chosen_message)

            logger.info(f"[*] 回復 : {chosen_message}")
            PASS_MSG.append(f"{message.author.name}:"+this_message)
            PASS_MSG.append("小俠:"+chosen_message)
            addtxt( MASSAGE_DATA,f"{message.author.name}:"+this_message.strip())
            addtxt( MASSAGE_DATA,"小俠:"+chosen_message.strip())
