# Chat.py
from utils.wesAi          import prompt_wes_com
from utils.file_os        import readfile    , addtxt
from utils.info           import MASSAGE_FOLDER, MASSAGE_MEMORY_SIZE, logger, XioaXiaContent, XioaXiaName
from collections          import deque

import threading
import random
import os


class Chat:
    def __init__(self,channelId):
        self.channelId = channelId
        self.DataName  = os.path.join(MASSAGE_FOLDER, f"{channelId}.txt")
        self.memory    = deque(maxlen=MASSAGE_MEMORY_SIZE)
        self.result    = None
        self.LoadMessage()

    def LoadMessage(self):
        """
        Loads the message to the memory
        """
        if (os.path.isfile(self.DataName)):
            with open(self.DataName,'r',encoding='utf-8') as f:
                line = f.readline()
                while line:
                    if ('http' not in line and ('<@' not in line) ):
                        self.memory.append(line.strip())
                    line = f.readline()
            return
        else:
            with open(self.DataName,'w',encoding='utf-8') as f:
                pass

    def BuildPrompt(self,name,message):
        """

        Args:
            name (str): The author name
            message (str): author input

        Returns:
            str: The text prompt to LLM
        """
        MemoryParaGraph= '\n'.join(self.memory)

        if (len(self.memory)!=0):
            word = (f"{XioaXiaContent}\n"
                    f"{MemoryParaGraph}"
                    f"\n{name}:{message}\n"
                    f"{XioaXiaName}:")
        else:
            word = (f"{XioaXiaContent}"
                    f"\n{name}:{message}\n"
                    f"{XioaXiaName}:")
        return  word

    def RandomPickFromData(self):
        """Pick a random text from the file.

        Returns:
            str: text
        """
        DataMessageArr = readfile(self.DataName)
        if (len(DataMessageArr)>0):
            picked = random.choices(DataMessageArr)[0]
            if (":" in picked): 
                picked = picked.split(":")[-1]
            return picked
        else:
            return "Hi"

    def ClearMessage(self,msg,name):
        """Clean the message

        Args:
            msg (str): the result from llm

        Returns:
            str: cleaned ,msg
        """
        split_msg  = "歐陽小俠:"
        split_msg2 = f"{name}:"
        if (msg):
            if (split_msg in msg):
                msg = "\n".join(msg.split(split_msg)[0:2]).strip()
            if (split_msg2 in msg):
                msg = "\n".join(msg.split(split_msg2)[0:2]).strip()


            msg =  msg.strip()
        return msg

    async def Talk(self,name,message):
        """Talk to LLM

        Args:
            name (str): The author name
            message (str): author input

        Returns:
            str: the output text
        """
        ThisPrompt = self.BuildPrompt(name,message)
        result =  await prompt_wes_com(ThisPrompt)

        result = self.ClearMessage(result,name)
        if (not result):
            logger.info("[*] Cause to prompt failed, using random way to reply user.")
            result = self.RandomPickFromData()
        
        addtxt( self.DataName,f"{name}:"+message.strip())
        addtxt( self.DataName,"歐陽小俠:"+result.strip())
        self.memory.append(f"{name}:"+message.strip())
        self.memory.append("歐陽小俠:"+result.strip())
        
        return result
    

    def clear_message(self):
        with open(self.DataName,'w',encoding='utf-8') as f:
            pass
        self.memory    = deque(maxlen=MASSAGE_MEMORY_SIZE)
        self.LoadMessage()