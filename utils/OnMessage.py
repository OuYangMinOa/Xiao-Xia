# OnMessage.py

from utils.file_os import readfile    , addtxt
from utils.info    import MASSAGE_DATA, PASS_MSG

import openais
import os




openai.api_key = str(os.getenv('OPENAI_TOKEN'))
PASS_MSG  = readfile()


def prompt_openai(word):
    try:
        completion = openai.Completion.create(engine="text-davinci-003",temperature= 0.5, prompt=word,max_tokens=1024)
        return completion.choices[0].text
        
    except openai.error.InvalidRequestError:
        print("[*] Prompt to many words ..., Cutting down")
        return prompt_openai("\n".join(word.split('\n')[:-1]))



def handle_message(test):

    pass_memory = ""
    count = 0
    for i in range(len(PASS_MSG)-1,-1,-1):
        if ('http' not in PASS_MSG[i] and ('<@' not in PASS_MSG[i]) and  len(re.findall(r'[\u4e00-\u9fff]+',PASS_MSG[i]))>0 ):
            pass_memory =  PASS_MSG[i]+","+ pass_memory
            # print(pass_memory)
            count += 1
        if (count>10 or len(pass_memory) >300):
            break


    word = "你現在是一個discord音樂機器人,名子叫小俠,可以使用/play來播放youtube上的音樂,/help可以看到小俠的全部功能。"+pass_memory+"。\n" + this_message+"\n"
    PASS_MSG.append(this_message)
    PASS_MSG.append(completion.choices[0].text)
    file_os.addtxt(MASSAGE_DATA,this_message.strip())
    file_os.addtxt(MASSAGE_DATA,completion.choices[0].text.strip())