from utils.info import music_user, sound_user, recording, alert_channel_id, ALERT_CHANNEL
from utils.info import CheckBool
from utils.eew import EEW, EEW_data
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



def EarthQuakeWarning(bot):
    
    async def send(_EEW):
        for each_channel in alert_channel_id:
            this_ctx = bot.get_channel(each_channel)
            print(this_ctx,each_channel)
            await this_ctx.send(_EEW.text)

    async def loop():
        await bot.wait_until_ready() 
        eew = EEW()
        async for each in eew.alert():
            await send(each)

    def LoopChecking():
        bot.loop.create_task(loop())

    threading.Thread(target=LoopChecking,daemon=True).start()