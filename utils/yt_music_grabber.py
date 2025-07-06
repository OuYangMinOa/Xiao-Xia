import httpx
import asyncio
import os
import re

from tqdm import tqdm
from urllib.parse import unquote
import aiofiles

# --- Part 1: 通用、解耦的下載函式 ---

async def download_file(url: str, folder: str = ".", custom_filename: str = ""):
    """
    從指定的 URL 非同步下載檔案，並顯示進度條。
    此函式已解耦，會自行建立 HTTP client。

    :param url: 要下載的檔案 URL
    :param folder: 要儲存檔案的資料夾
    :param custom_filename: (可選) 自訂檔名，如果為空則自動偵測
    """
    bar = None
    try:
        # 在函式內部建立 client，實現高內聚、低耦合
        async with httpx.AsyncClient(follow_redirects=True, timeout=60) as client:
            async with client.stream("GET", url) as res:
                res.raise_for_status()

                os.makedirs(folder, exist_ok=True)

                # 如果使用者提供自訂檔名，就使用它
                if custom_filename:
                    filename = custom_filename
                else:
                    # 智慧判斷檔名 (邏輯不變)
                    filename = ""
                    if "content-disposition" in res.headers:
                        disposition = res.headers['content-disposition']
                        filename_parts = [part for part in disposition.split(';') if 'filename' in part]
                        if filename_parts:
                            filename = filename_parts[0].split('=')[-1].strip(" \"'")
                            filename = unquote(filename, encoding='utf-8')
                    
                    if not filename:
                        filename = os.path.basename(unquote(str(res.url).split('?')[0]))

                    if not filename:
                        filename = "downloaded_file.tmp"

                file_path = os.path.join(folder, filename)
                total_size = int(res.headers.get("content-length", 0))

                bar = tqdm(desc=filename, total=total_size, unit="iB", unit_scale=True, unit_divisor=1024)

                async with aiofiles.open(file_path, "wb") as f:
                    async for data in res.aiter_bytes(chunk_size=1024):
                        await f.write(data)
                        bar.update(len(data))
                
                bar.close()
                bar = None
                print(f"\n下載完成！檔案已儲存至：{file_path}")

    except httpx.RequestError as e:
        print(f"\n下載時發生網路錯誤 ({url[:30]}...): {e}")
    except Exception as e:
        print(f"\n下載時發生未知錯誤 ({url[:30]}...): {e}")
    finally:
        if bar:
            bar.close()


# --- Part 2: 專門負責處理 YouTube 下載的類別 ---

class YouTubeDownloader:
    """
    一個專門用來從 clipto.com 解析並下載 YouTube 音訊的類別。
    """
    BASE_URL = "https://www.clipto.com/zh-TW/media-downloader/youtube-audio-downloader"
    API_URL = "https://www.clipto.com/api/youtube"
    CSV_URL = "https://www.clipto.com/api/csrf"
    
    def __init__(self, headers: dict = None):
        self.headers = headers or {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        }
        # 在類別內部維護一個共用的 client，相當於 session 的作用
        self.client = httpx.AsyncClient(headers=self.headers, timeout=30)

    async def __aenter__(self):
        # 讓這個類別可以被用在 async with 中，自動初始化 client
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # 自動關閉 client
        await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def download_mp3(self, yt_url : str, download_folder : str, filename : str):
        csf_res = await self.client.get(self.CSV_URL)
        csf_token = csf_res.json().get('csrfToken', '')
        mp3_url = f"{self.API_URL}/mp3?url={yt_url}&csrfToken={csf_token}"
        print(f"正在下載 MP3 檔案: {mp3_url}")
        await download_file(mp3_url, folder=download_folder, custom_filename=filename)

    async def fetch_download_links(self, yt_url: str) -> list[dict]:
        """
        根據 YouTube URL，從 Clipto API 獲取音訊的下載連結。
        """
        print("正在初始化連線...")
        await self.client.get(self.BASE_URL)
        
        print(f"正在為 {yt_url} 請求下載連結...")
        payload = {"url": yt_url}
        try:
            res = await self.client.post(self.API_URL, json=payload)
            res.raise_for_status()
            data : dict = res.json()
            
            audio_links = []
            for media in data.get('medias', []):
                if media.get('label', '').startswith('m4a') and media.get('url'):
                    audio_links.append(media)
            
            if not audio_links:
                print("API 回應中未找到 m4a 格式的音訊。")
            
            return audio_links
            
        except httpx.RequestError as e:
            print(f"API 請求失敗: {e}")
            return []
        except Exception as e:
            print(f"解析 API 回應時出錯: {e}")
            return []

    async def download_all_audio(self, yt_url: str, download_folder: str = "downloads"):
        """
        主流程：獲取所有音訊連結，然後並行下載它們。
        """

        os.makedirs(download_folder, exist_ok=True)

        audio_media = await self.fetch_download_links(yt_url)
        if not audio_media:
            return

        print(f"\n找到 {len(audio_media)} 個音訊檔案，準備並行下載...")
        
        tasks = []
        for media in audio_media:
            # 呼叫獨立的 download_file 函式
            task = download_file(
                url=media['url'],
                folder=download_folder,
                # Clipto API 有時不會在下載連結中提供檔名，但它在 JSON 中提供了
                # 我們可以把這個檔名傳給 download_file
                custom_filename=media.get('formattedTitle') + '.m4a'
            )
            tasks.append(task)
        
        await asyncio.gather(*tasks)

    def _find_best_audio(self, audio_media: list[dict]) -> dict | None:
        """從媒體清單中找出位元率最高的音訊。"""
        if not audio_media:
            return None

        best_audio = None
        max_bitrate = -1

        for media in audio_media:
            label = media.get('label', '')  # 例如 'm4a / 127 kbps'
            # 使用正規表示式從 label 中提取數字
            match = re.search(r'(\d+)\s*kb/s', label)
            
            if match:
                bitrate = int(match.group(1))
                if bitrate > max_bitrate:
                    max_bitrate = bitrate
                    best_audio = media
        
        # 如果所有 media 都沒有標示 bitrate，就回傳第一個作為預設
        if not best_audio and audio_media:
            print("警告：無法在標籤中找到位元率資訊，將下載清單中的第一個音訊。")
            return audio_media[0]
            
        return best_audio

    # --- 新增的公開方法 ---
    async def download_best_audio(self, yt_url: str, download_folder: str = "downloads", filename: str = ""):
        """
        主流程：獲取所有音訊連結，找出品質最好的那一個並下載。
        """

        os.makedirs(download_folder, exist_ok=True)

        audio_media = await self.fetch_download_links(yt_url)
        if not audio_media:
            return

        best_audio = self._find_best_audio(audio_media)

        if best_audio:
            label = best_audio.get('label', 'N/A')
            if not filename:
                # 如果沒有提供自訂檔名，就使用格式化的標題
                filename = best_audio.get('formattedTitle', 'best_audio') + '.m4a'
            
            print(f"\n找到最高品質音訊: {label}")
            print("準備開始下載...")
            
            # 只下載最好的那一個
            await download_file(
                url=best_audio['url'],
                folder=download_folder,
                custom_filename=filename
            )
        else:
            print("錯誤：無法在找到的音訊中確定要下載哪一個。")

# --- Part 3: 主執行區塊 ---

async def main():
    yt_url_to_download = "https://www.youtube.com/watch?v=JoLyKYBbYW4" # 換成你想下載的 YouTube 影片網址
    # 使用 async with 可以確保 client 被妥善關閉
    async with YouTubeDownloader() as downloader:
        await downloader.download_mp3(yt_url=yt_url_to_download, download_folder="MyYouTubeMusic", filename = "test.m4a")

if __name__ == "__main__":
    asyncio.run(main())