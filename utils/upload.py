import requests, os, base64


from utils.info import logger
from glob import glob
from aiohttp import ClientSession, FormData

async def upload_wp(file_path):
# 設定 WordPress 網站的 URL 和 API 端點
    wordpress_url = 'https://ouyangminwei.com'
    api_endpoint = '/wp-json/wp/v2/media'

    data_string = os.getenv("MY_APP_ID")+":"+os.getenv("WP_APP_PASS")
    token = base64.b64encode(data_string.encode())
    headers = {'Authorization': 'Basic ' + token.decode('utf-8')}

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
    os.system("pwd")
    print("Starting")
    for eachfile in glob("../data/empty*"):
        print(eachfile)
        asyncio.run(upload_wp(eachfile))