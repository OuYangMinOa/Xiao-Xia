from dataclasses import dataclass
from requests_html import AsyncHTMLSession
import threading
import asyncio
import time
import json

@dataclass
class EEW_data:
    id : str
    updated: str
    text: str
    strong : str



class EEW:
    URL = "https://alerts.ncdr.nat.gov.tw/JSONAtomFeed.ashx?AlertType=6"  ## The taiwan earthquake url endpoint.
    def __init__(self) -> None:
        self.session = AsyncHTMLSession()
        self.state    = True
        self.last_eew = None


    async def grab_result(self) -> EEW_data:
        r = await self.session.get(self.URL)
        await r.html.arender()
        r.json()
        alert_json = r.json()['entry'][-1]

        return EEW_data(
            alert_json['id'],
            alert_json['updated'],
            alert_json['summary']['#text'],
            alert_json['summary']['#text'][-3:-1],
        )
    

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