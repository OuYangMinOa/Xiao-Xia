
from datetime import datetime, timezone
import base64


class GoogleMap:

    @staticmethod
    def decimal_to_dms(degree : float) -> tuple[int, int, float]:
        # 取得度數
        d = int(degree)
        # 取得分數
        m = int((degree - d) * 60)
        # 取得秒數
        s = (degree - d - m / 60) * 3600
        return d, m, s

    @staticmethod
    def format_dms(lat : float, lon : float) -> str:
        # 轉換緯度
        lat_d, lat_m, lat_s = GoogleMap.decimal_to_dms(abs(lat))
        lat_direction = 'N' if lat >= 0 else 'S'
        # 轉換經度
        lon_d, lon_m, lon_s = GoogleMap.decimal_to_dms(abs(lon))
        lon_direction = 'E' if lon >= 0 else 'W'
        
        # 格式化為 DMS 字符串
        lat_dms = f"{lat_d}°{lat_m:02d}'{lat_s:.1f}\"{lat_direction}"
        lon_dms = f"{lon_d}°{lon_m:02d}'{lon_s:.1f}\"{lon_direction}"
        return f"{lat_dms} {lon_dms}"

    @staticmethod
    def get_google_map_embed(lat : float, lon : float) -> str :
        current_millis = int(datetime.now(tz=timezone.utc).timestamp() * 1000)
        lat_lon_base64 = base64.b64encode(GoogleMap.format_dms(lat, lon).encode("utf-8")).decode("utf-8")
        coordinateString =  f"""<iframe src="https://www.google.com/maps/embed?pb=!1m17!1m12!1m3!1d600000!2d{lon}!3d{lat}!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m2!1m1!2z{lat_lon_base64}!5e0!3m2!1szh-TW!2stw!4v{current_millis}!5m2!1szh-TW!2stw"  style="border:0; width: 100%; height: 300px;"  allowfullscreen="" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>"""
        return coordinateString
    

if __name__ == "__main__":
    print(GoogleMap.get_google_map_embed(23.13, 120.69))