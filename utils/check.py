from utils.info import music_user, sound_user, recording, alert_channel_id, ALERT_CHANNEL
from utils.info import CheckBool
from utils.eew import EEW, EEW_data
from utils.taiwan_map import mapper

from datetime import datetime

import discord
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
    _map = mapper()

    
        

    async def send(_EEW:EEW_data):
        embed = discord.Embed(
                title="地震 !",
                description=f"{_EEW.HypoCenter} 發生規模{_EEW.Magnitude}有感地震, 最大震度{_EEW.MaxIntensity}級",
                color=discord.Colour.green(), # Pycord provides a class with default colors you can choose from
            )
        
        embed.add_field(name="ID",value=_EEW.id)
        embed.add_field(name="發生時間",value=f"`{_EEW.OriginTime}`",inline=True)
        embed.add_field(name="",value="",inline=True)

        embed.add_field(name="規模",value=f"{EEW.circle_mag(_EEW.Magnitude)} 芮氏 {_EEW.Magnitude}",inline=True)
        embed.add_field(name="深度",value=f"{EEW.circle_depth(_EEW.Depth)} {_EEW.Depth}公里")
        embed.add_field(name="最大震度",value=f"{EEW.circle_intensity(_EEW.MaxIntensity)} {_EEW.MaxIntensity}級",inline=True)

        embed.add_field(name="震央位置",value=_EEW.HypoCenter)
        embed.add_field(name="經度",value=_EEW.Latitude,inline=True)
        embed.add_field(name="緯度",value=_EEW.Longitude,inline=True)
 
        embed.set_footer(text = f"💭 發布於：{datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
        
        for each_channel in alert_channel_id:   
            this_ctx = bot.get_channel(each_channel)
            # print(each_channel)
            await this_ctx.send(embed=embed)

    async def loop():
        eew = EEW()
        await bot.wait_until_ready() 

        await send(
            EEW_data(1,datetime.now(),datetime.now().strftime("%Y年%m月%d日\n%H:%M:%S"),"test",5.0,1.0,5,100,'5')
        )

        
        async for each in eew.alert():
            await send(each)

    def LoopChecking():
        bot.loop.create_task(loop())

    threading.Thread(target=LoopChecking,daemon=True).start()