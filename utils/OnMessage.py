# OnMessage.py
from utils.info           import silinece_channel, logger, MASSAGE_FOLDER, chat_dict
from utils.Chat           import Chat

import threading
import os




def prompt_openai(word):
    import openai
    openai.api_key = str(os.getenv('OPENAI_TOKEN'))
    try:
        completion = openai.Completion.create(engine="text-davinci-003",temperature= 0.5, prompt=word,max_tokens=1024)
        return completion.choices[0].text
        
    except openai.error.InvalidRequestError:
        logger.error("[*] Prompt to many words ..., Cutting down")
        return prompt_openai("\n".join(word.split('\n')[:-1]))



def ThreadHandleMessage(bot,message):
        def LoopChecking():
            bot.loop.create_task(handle_message(message))
    
        threading.Thread(target=LoopChecking,daemon=True).start()
    
async def handle_message(message):
    """Handle a message input

    Args:
        message (a discord message): a discord message
    """
    print( message.content)
    this_message = message.content.strip()
    logger.info(f"[*] {message.author.name} : {this_message}")
    if (message.channel.id in silinece_channel):
        return
    if (this_message == ""):
        return 

    folder_name = f"{MASSAGE_FOLDER}"
    os.makedirs(folder_name, exist_ok=True)

    if (message.channel.id not in chat_dict):
        chat_dict[message.channel.id] = Chat(message.channel.id)


    # print(pass_memory)
    if ("http" not in this_message and this_message) :

        chatgpt_result = chat_dict[message.channel.id].Talk(message.author.name,this_message)
        if chatgpt_result:
            await message.channel.send(chatgpt_result)
            logger.info(f"[*] 回復 : {chatgpt_result}")


