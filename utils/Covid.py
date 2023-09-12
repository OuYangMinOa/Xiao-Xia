from aiohttp import ClientSession

import asyncio
import datetime
import requests
import bs4

async def get_covid():
    """ get the Covid data from the covid-19.nchc.org.tw
    """
    url = "https://covid-19.nchc.org.tw/?language=en"
    headers = {"User-Agent": "Mozilla/5.0", "Referer": url}
    async with ClientSession() as session:
            async with session.get(url, headers = headers,timeout=20) as re:
                thisContent = await re.content.read()

    soup = bs4.BeautifulSoup(thisContent, 'html.parser')

    # print(soup)
    total_people = soup.find_all(class_="mb-1 text-dark display-4")
    numbers = []
    for i in total_people:
        # print(i.text.strip())
        numbers.append(i.text.strip().split("+")[0])
        numbers.append(i.text.strip().split("+")[1])
    global_people = soup.find_all("a",href="2023_world_confirmed.php")
    print(global_people[1].text.strip())
    print(numbers)


    message = f"""
{datetime.datetime.now().strftime('%Y %#m/%#d')}:
=====================
今日本土確診 : {numbers[1]}
今日死亡人數 : {numbers[3]}
=====================
全台累積確診 : {numbers[0]}
全球累積確診 : {global_people[1].text.strip().split()[0][:-5]}
全台累積死亡 : {numbers[2]}   :skull_crossbones: :skull_crossbones: :skull_crossbones:
=====================
資料來源 : https://covid-19.nchc.org.tw/?language=en
"""
    
    # print(total_people)
    return message




def get_covid2():
    """ Get covid information from yahoo (abandoned)
    """
    url = "https://news.campaign.yahoo.com.tw/2019-nCoV/index.php"
    headers = {"User-Agent": "Mozilla/5.0", "Referer": url}
    re      = requests.get(url, headers = headers,verify=False,timeout=20)
    soup    = bs4.BeautifulSoup(re.content, 'html.parser')

    date  = soup.find_all(class_="secTaiwan")[0].text.split()
    print(date)
    TOTAL = date[3]
    TODAY = date[7]
    T_tol = date[8][2:]
    DEAD_ = date[-1][2:]
    came  = date[-5]
    D_TOD = date[-2]

    this_datatime = datetime.datetime.strptime(date[1][5:],"%Y年%m月%d日%H時%M分")
    data_date = this_datatime.strftime("%Y %#m/%#d")

    TODAY_DATE = datetime.datetime.now().strftime('%Y %#m/%#d')
    print(data_date,TODAY_DATE,data_date==TODAY_DATE)

    if (data_date != TODAY_DATE):
        TODAY_DATE = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y %#m/%#d')
        # print(data_date,TODAY_DATE,data_date==TODAY_DATE)
    
    
    message = f"""
{data_date}:
=====================
今日本土確診 : {TODAY}
今日境外移入 : {came}
今日死亡人數 : {D_TOD}
=====================
本土累積確診 : {T_tol} 
全台累積確診 : {TOTAL}
全台累積死亡 : {DEAD_}   :skull_crossbones: :skull_crossbones: :skull_crossbones:
=====================
資料來源 : yahoo.com.tw
"""
    return message


if __name__ == "__main__":
    asyncio.run(get_covid())
