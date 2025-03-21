import sys
sys.path.append("..")

try:
    from utils.info import logger
except:
    ...
from utils.eew  import EEW, EEW_data
from datetime   import datetime
from aiohttp    import ClientSession, FormData
from glob       import glob

import base64
import random
import os

def chosse_head():
    colors = [
        ("#007bff", "#cce5ff"),  # 藍色
        ("#28a745", "#d4edda"),  # 綠色
        ("#dc3545", "#f8d7da"),  # 紅色
        ("#fd7e14", "#ffeeba"),  # 橙色
        ("#6f42c1", "#e2d8f3")   # 紫色
    ]

    # 隨機選取顏色
    border_color, background_color = random.choice(colors)

    # 生成 <div>
    div_code = f'<div style="border: 2px solid {border_color}; padding: 20px; border-radius: 10px; background-color: {background_color}; margin: 20px 0; font-family: Arial, sans-serif;">'
    return div_code

def get_this_eew_html(data : EEW_data  ):
    return f"""
{chosse_head()}
    <h2 style="color: #856404; text-align: center;">地震速報</h2>
    <p style="font-size: 16px; margin: 5px 0;" ><strong>地點：</strong>{data.HypoCenter}</p>
    <p style="font-size: 16px; margin: 5px 0;" ><strong>發生時間：</strong>{data.OriginTime}</p>
    <p style="font-size: 16px; margin: 5px 0;" ><strong>地震規模：</strong>{EEW.circle_mag(data.Magnitude)[1]} 芮氏 {data.Magnitude}</p>
    <p style="font-size: 16px; margin: 5px 0;" ><strong>地震深度：</strong>{EEW.circle_depth(data.Depth)[1]} {data.Depth}公里</p>
    <p style="font-size: 16px; margin: 5px 0;" ><strong>最大震度：</strong>{EEW.circle_intensity(data.MaxIntensity)[1]} {data.MaxIntensity}級</p>
    <p style="font-size: 16px; margin: 5px 0;" ><strong>震央位置：</strong>{data.HypoCenter}</p>
    <p style="font-size: 16px; margin: 5px 0;" ><strong>緯度：</strong>{data.Latitude}</p>
    <p style="font-size: 16px; margin: 5px 0;" ><strong>經度：</strong>{data.Longitude}</p>
    <p style="font-size: 16px; margin: 5px 0;" ><strong>發布時間：</strong>{datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}</p>
</div>
<p></p>
<hr class="wp-block-separator has-alpha-channel-opacity"/>
<p>\n\n</p>
"""

async def update_website(data:EEW_data):
    this_content  = get_this_eew_html(data)
    subtitle      = '<p style="color: #ff0000"><strong>此為預警系統自動上傳之資訊，準確信息請以交通部中央氣象署為主!</strong></p>'
    wordpress_url = 'https://ouyangminwei.com/wp-json/wp/v2/posts/636'
    data_string   = os.getenv("MY_APP_ID")+":"+os.getenv("WP_APP_PASS")
    token         = base64.b64encode(data_string.encode())
    headers       = {'Authorization': 'Basic ' + token.decode('utf-8')}
    
    async with ClientSession() as session:
        async with session.get("https://ouyangminwei.com/wp-json/wp/v2/posts/636", headers = headers) as resp:
            response = await resp.json()
    
    old_content = response['content']['rendered'].replace(subtitle,"")
    new_content = subtitle + this_content + old_content
    data = {
        'title'   : '地震警報',
        'content' : f"{new_content}",
        'status'  : 'publish' # 可以設置為'draft'或'publish'
    }
    try:
        async with ClientSession() as session:  
            async with session.put(wordpress_url, headers = headers, data = data ) as resp:
                response = await resp.json()
                logger.info(f"[*] update website content {response['content']['rendered']}")
    except Exception as e:
        logger.error(e)

async def upload_wp(file_path : str):
# 設定 WordPress 網站的 URL 和 API 端點
    wordpress_url = 'https://ouyangminwei.com'
    api_endpoint  = '/wp-json/wp/v2/media'
    data_string   = os.getenv("MY_APP_ID")+":"+os.getenv("WP_APP_PASS")
    token         = base64.b64encode(data_string.encode())
    headers       = {'Authorization': 'Basic ' + token.decode('utf-8')}

    # 準備上傳的 MP3 檔案
    # files = {'file': (os.path.basename(file_path), open(file_path, 'rb'), 'audio/mp3'),}

    # 準備上傳的其他媒體信息（標題、描述等）
    data = FormData()
    data.add_field('title',os.path.basename(file_path))
    data.add_field('description','語音版')
    data.add_field('file',open(file_path, 'rb'))


    # 發送 POST 請求上傳 MP3 檔案
    logger.info(f'[*] Uploading {file_path}')

    async with ClientSession() as session:
        async with session.post(wordpress_url + api_endpoint, headers=headers, data=data) as resp:
            response = await resp.json()
            if resp.status == 201:
                print("MP3 檔案上傳成功！")
                print("媒體 ID：", response['id'])
                logger.info(f'MP3 檔案上傳成功！')
            else:
                print("MP3 檔案上傳失敗。")
                print("回應狀態碼：", response['data']['status'])
                print("回應內容：", response['message'])
                logger.info(f'[*] MP3 檔案上傳失敗。')


if __name__ == '__main__':
    import asyncio
    # print("Starting")
    # files = glob("../data/*.mp3")
    # files.sort(key=os.path.getmtime)

    # for eachfile in files:
    #     print(eachfile)
    #     asyncio.run(upload_wp(eachfile))
    


    asyncio.run(update_website(EEW_data.fake_data()))