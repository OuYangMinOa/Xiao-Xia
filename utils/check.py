from utils.info import music_user, sound_user, recording, alert_channel_id, ALERT_CHANNEL
from utils.info import CheckBool
from utils.eew import EEW, EEW_data
from utils.taiwan_map import mapper

from datetime import datetime

import discord
import threading
import asyncio
import math

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



class EEWLoop:
    def __init__(self,bot) -> None:
        self.bot = bot
        self._last_fj_time = None # 防止 福建 一直傳送
        self._last_tw_time = None
        self._last_fj_mag  = None 
        self.EEW  = EEW()

    def start_alert_tw(self):
        threading.Thread(target=self.bot.loop.create_task, args=(self.loop_alert("tw"),)).start()
        return self

    def start_alert_jp(self):
        threading.Thread(target=self.bot.loop.create_task, args=(self.loop_alert("jp"),)).start()
        return self
    
    def start_alert_fj(self):
        threading.Thread(target=self.bot.loop.create_task, args=(self.loop_alert("fj"),)).start()  
        return self
    
    def start_alert_sc(self):
        threading.Thread(target=self.bot.loop.create_task, args=(self.loop_alert("sc"),)).start()
        return self

    def fj_time(self,date_string:str):
        return datetime.strptime(date_string.replace("\n"," "), '%Y-%m-%d%H:%M:%S')

    async def loop_alert(self,pos="tw"):
        await self.bot.wait_until_ready()
        print(f"[*] Start alert {pos} !")
        if (pos == "fj"):
            async for each in self.EEW.wss_alert(pos):
                this_time =  self.fj_time(each.OriginTime)
                if (( self._last_tw_time is None or (this_time - self._last_tw_time).total_seconds() > 120 )): # 看台灣中央氣象局已發布此地震
                    if  ( self._last_fj_time is None or(
                        ( (this_time - self._last_fj_time).total_seconds() > 120 or each.Magnitude > self._last_fj_mag+0.2 ))):
                        await self.send(each,pos)
                self._last_fj_time = this_time
                self._last_fj_mag  = each.Magnitude
                print(each)
        else:
            async for each in self.EEW.wss_alert(pos):
                await self.send(each,pos)
                self._last_tw_time = self.fj_time(each.OriginTime)
                print(each)
    
    async def send_test(self,pos):
        await self.bot.wait_until_ready()
        await self.send(
            EEW_data(1,datetime.now(),datetime.now().strftime("%Y年%m月%d日 %H:%M:%S"),pos,23.92,121.59,5.6,40,"5弱"),
            pos
        )

    async def send(self, _EEW:EEW_data,pos):
        if (pos == "jp"):

            if (isinstance(_EEW.MaxIntensity,str)):
                if (_EEW.MaxIntensity[0].isnumeric()):
                    intensity = int(_EEW.MaxIntensity[0])
                else:
                    return
            elif(isinstance(_EEW.MaxIntensity,float) or isinstance(_EEW.MaxIntensity,int)):
                intensity = math.floor(_EEW.MaxIntensity)
            else:
                return
            
            if (intensity < 5):
                return
            



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
        embed.add_field(name="緯度",value=_EEW.Latitude,inline=True)
        embed.add_field(name="經度",value=_EEW.Longitude,inline=True)

        embed.set_footer(text = f"💭 發布於：{datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")

        tasks = []
        for each_channel in alert_channel_id:   
            this_ctx = self.bot.get_channel(each_channel)
            tasks.append(asyncio.create_task(this_ctx.send(embed=embed)))
        await asyncio.gather(*tasks)



def EarthQuakeWarning(bot):
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
        embed.add_field(name="緯度",value=_EEW.Latitude,inline=True)
        embed.add_field(name="經度",value=_EEW.Longitude,inline=True)

        embed.set_footer(text = f"💭 發布於：{datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
        
        for each_channel in alert_channel_id:   
            this_ctx = bot.get_channel(each_channel)
            # print(each_channel)
            await this_ctx.send(embed=embed)

    async def loop():
        eew = EEW()
        await bot.wait_until_ready()
        async for each in eew.ssw_alert():
            await send(each)

    def LoopChecking():
        bot.loop.create_task(loop())

    threading.Thread(target=LoopChecking,daemon=True).start()