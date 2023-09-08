from utils.info import music_user, sound_user, recording
from utils.info import CheckBool

import threading
import asyncio

def StartChecking(bot):
    async def WhileChecking():
        CheckBool = True
        await asyncio.sleep(5)
        while CheckBool:
            for eachKey in music_user.copy():
                await music_user[eachKey].check()
            for eachKey in sound_user.copy():
                await sound_user[eachKey].check()
            for eachKey in recording.copy():
                await recording[eachKey].check()
            await asyncio.sleep(1800)

    def LoopChecking():
        bot.loop.create_task(WhileChecking())

    threading.Thread(target=LoopChecking,daemon=True).start()

async def DeleteAllResponse():
    print("\n[*] Clear all responses")
    for eachKey in music_user.copy():
        await music_user[eachKey].check()
    for eachKey in sound_user.copy():
        await sound_user[eachKey].check()


async def RestartBot(bot):
    for eachKey in music_user.copy():
        try:
            await  music_user[eachKey].kill()
        except:
            pass 
    for eachKey in sound_user.copy():
        try:
            await  sound_user[eachKey].kill()
        except:
            pass 
    for eachKey in recording.copy():
        try:
            await  recording[eachKey].kill()
        except:
            pass
    CheckBool = False
    await asyncio.sleep(5)
    StartChecking(bot)