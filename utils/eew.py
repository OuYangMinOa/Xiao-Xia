from dataclasses import dataclass
from requests_html import AsyncHTMLSession
import threading
import asyncio
import time
import json

@dataclass
class EEW_data:
    id: int
    ReportTime: str
    OriginTime: str
    HypoCenter: str
    Latitude: float 
    Longitude: float
    Magnitude: float
    Depth: int
    MaxIntensity: str



class EEW:
    URL = "https://api.wolfx.jp/cwa_eew.json"  ## The taiwan earthquake url endpoint.
    def __init__(self) -> None:
        self.session = AsyncHTMLSession()
        self.state    = True
        self.last_eew = None
    
    def json_to_eewdata(self,json_data) -> EEW_data:
        return EEW_data(
            json_data['ID'],
            json_data['ReportTime'].replace(" ","\n"),
            json_data['OriginTime'].replace(" ","\n"),
            json_data['HypoCenter'],
            json_data['Latitude'],
            json_data['Longitude'],
            json_data['Magunitude'],
            json_data['Depth'],
            json_data['MaxIntensity'],
        )

    async def grab_result(self) -> EEW_data:
        r = await self.session.get(self.URL)
        await r.html.arender()
        r.json()
        alert_json = r.json()

        return self.json_to_eewdata(alert_json)
    

    async def alert(self):
        if self.last_eew is None:
            self.last_eew = await self.grab_result()
        while (self.state):
            time.sleep(5)
            this_eew = await self.grab_result()
            if (this_eew.id != self.last_eew.id):
                yield this_eew
                self.last_eew = this_eew

    async def close(self):
        self.state = False
        await self.session.close()


async def test():
    eew = EEW()
    print(await eew.grab_result())
    print("Listen to alert system")
    async for each in eew.alert():
        print(each)
    await eew.close()

if __name__ == '__main__':
    asyncio.run(test())