"""
Weather cog — 使用中央氣象署開放資料 API (CWA Open Data)
需要在環境變數 CWA_API_KEY 放入你註冊的授權碼
註冊網址: https://opendata.cwa.gov.tw/
"""
import os
import aiohttp
import discord
from datetime import datetime
from discord.commands import slash_command
from discord.ext import commands
from utils.info import logger

CWA_API_KEY = os.getenv("CWA_API_KEY", "")
BASE = "https://opendata.cwa.gov.tw/api/v1/rest/datastore"

# 縣市對照
CITIES = [
    "基隆市", "臺北市", "新北市", "桃園市", "新竹市", "新竹縣", "苗栗縣",
    "臺中市", "彰化縣", "南投縣", "雲林縣", "嘉義市", "嘉義縣", "臺南市",
    "高雄市", "屏東縣", "宜蘭縣", "花蓮縣", "臺東縣", "澎湖縣", "金門縣", "連江縣",
]

# 依天氣現象挑 emoji
def weather_emoji(desc: str) -> str:
    d = desc or ""
    if "雷" in d:           return "⛈️"
    if "雨" in d:           return "🌧️"
    if "雪" in d:           return "❄️"
    if "霧" in d:           return "🌫️"
    if "陰" in d:           return "☁️"
    if "多雲" in d:         return "⛅"
    if "晴" in d:           return "☀️"
    return "🌡️"

# 依溫度決定 embed 顏色
def temp_color(t: int) -> discord.Color:
    if t >= 32: return discord.Color.from_rgb(231, 76, 60)
    if t >= 26: return discord.Color.from_rgb(241, 153, 60)
    if t >= 20: return discord.Color.from_rgb(241, 196, 15)
    if t >= 14: return discord.Color.from_rgb(46, 204, 113)
    if t >= 8:  return discord.Color.from_rgb(52, 152, 219)
    return discord.Color.from_rgb(155, 89, 182)


async def cwa_get(session: aiohttp.ClientSession, dataset: str, **params) -> dict:
    params["Authorization"] = CWA_API_KEY
    params.setdefault("format", "JSON")
    async with session.get(f"{BASE}/{dataset}", params=params, timeout=20) as r:
        r.raise_for_status()
        return await r.json()


def parse_36h(record: dict) -> dict:
    """把 F-C0032-001 一個 location 解析成 dict"""
    out = {}
    for el in record["weatherElement"]:
        out[el["elementName"]] = el["time"]
    return out


class Weather(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ---------- 今日 ----------
    @slash_command(name="weather_day", description="今日天氣概況（全台）")
    async def weather_day(self, ctx: discord.ApplicationContext):
        # 注意: bot.before_invoke 已經 defer 過，這裡直接用 followup
        try:
            async with aiohttp.ClientSession() as s:
                data = await cwa_get(s, "F-C0032-001")
                warn = await cwa_get(s, "W-C0033-001")

            embed = discord.Embed(
                title="🌏 今日全台天氣概況",
                color=discord.Color.blurple(),
                timestamp=datetime.now(),
            )
            embed.set_footer(text="資料來源：中央氣象署 CWA Open Data")

            for loc in data["records"]["location"]:
                name = loc["locationName"]
                el = parse_36h(loc)
                wx = el["Wx"][0]["parameter"]["parameterName"]
                mint = el["MinT"][0]["parameter"]["parameterName"]
                maxt = el["MaxT"][0]["parameter"]["parameterName"]
                pop = el["PoP"][0]["parameter"]["parameterName"]
                emoji = weather_emoji(wx)
                embed.add_field(
                    name=f"{emoji} {name}",
                    value=f"{wx}\n🌡️ {mint}–{maxt}°C  ☔ {pop}%",
                    inline=True,
                )
            await ctx.followup.send(embed=embed)

            # 天氣特報
            warn_embed = discord.Embed(
                title="⚠️ 天氣特報",
                color=discord.Color.orange(),
            )
            records = warn["records"]["location"]
            active = [r for r in records if r.get("hazardConditions", {}).get("hazards")]
            if not active:
                warn_embed.description = "✅ 目前無天氣特報"
            else:
                for r in active[:25]:
                    hazards = r["hazardConditions"]["hazards"]
                    txt = "\n".join(
                        f"• {h['info']['phenomena']}{h['info'].get('significance','')}"
                        for h in hazards
                    )
                    warn_embed.add_field(name=r["locationName"], value=txt, inline=True)
            await ctx.followup.send(embed=warn_embed)

        except Exception as e:
            logger.error(e)
            await ctx.followup.send(f"❌ 取得天氣資料失敗：{e}")

    # ---------- 一週 ----------
    @slash_command(name="weather_week", description="未來一週天氣預報（縣市選擇）")
    async def weather_week(self, ctx: discord.ApplicationContext):
        await ctx.followup.send("請選擇縣市：", view=WeekView())

    # ---------- 指定縣市 ----------
    @slash_command(name="weather_pos", description="指定縣市的天氣概況")
    async def weather_pos(self, ctx: discord.ApplicationContext):
        await ctx.followup.send("請選擇縣市：", view=PosView())


# ============ Views ============

class CitySelect(discord.ui.Select):
    def __init__(self, placeholder="選擇縣市"):
        opts = [discord.SelectOption(label=c) for c in CITIES]
        super().__init__(placeholder=placeholder, min_values=1, max_values=1, options=opts)


class PosView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=600)
        self.select = CitySelect()
        self.select.callback = self.on_select
        self.add_item(self.select)

    async def on_select(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False, invisible=False)
        city = self.select.values[0]
        try:
            async with aiohttp.ClientSession() as s:
                data = await cwa_get(s, "F-C0032-001", locationName=city)
            loc = data["records"]["location"][0]
            el = parse_36h(loc)

            wx_now = el["Wx"][0]["parameter"]["parameterName"]
            mint = int(el["MinT"][0]["parameter"]["parameterName"])
            maxt = int(el["MaxT"][0]["parameter"]["parameterName"])
            pop = el["PoP"][0]["parameter"]["parameterName"]
            ci = el["CI"][0]["parameter"]["parameterName"]
            avg = (mint + maxt) // 2

            embed = discord.Embed(
                title=f"{weather_emoji(wx_now)} {city} 天氣預報",
                description=f"**{wx_now}**",
                color=temp_color(avg),
                timestamp=datetime.now(),
            )
            # 三個時段
            periods = ["🌙 今晚", "☀️ 明日白天", "🌙 明日晚上"]
            for i, label in enumerate(periods):
                if i >= len(el["Wx"]): break
                w = el["Wx"][i]["parameter"]["parameterName"]
                lo = el["MinT"][i]["parameter"]["parameterName"]
                hi = el["MaxT"][i]["parameter"]["parameterName"]
                p = el["PoP"][i]["parameter"]["parameterName"]
                c = el["CI"][i]["parameter"]["parameterName"]
                embed.add_field(
                    name=label,
                    value=f"{weather_emoji(w)} {w}\n🌡️ {lo}–{hi}°C\n☔ 降雨 {p}%\n👕 {c}",
                    inline=True,
                )
            embed.set_footer(text="資料來源：中央氣象署 CWA Open Data")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(e)
            await interaction.followup.send(f"❌ 失敗：{e}", ephemeral=True)


class WeekView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=600)
        self.select = CitySelect("選擇縣市（一週預報）")
        self.select.callback = self.on_select
        self.add_item(self.select)

    async def on_select(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False, invisible=False)
        city = self.select.values[0]
        try:
            async with aiohttp.ClientSession() as s:
                data = await cwa_get(s, "F-C0032-001", locationName=city)
            loc = data["records"]["location"][0]
            el = parse_36h(loc)

            embed = discord.Embed(
                title=f"📅 {city} 未來預報",
                color=discord.Color.teal(),
                timestamp=datetime.now(),
            )
            for i in range(len(el["Wx"])):
                t = el["Wx"][i]
                start = t["startTime"][5:16].replace("-", "/")
                end = t["endTime"][5:16].replace("-", "/")
                w = t["parameter"]["parameterName"]
                lo = el["MinT"][i]["parameter"]["parameterName"]
                hi = el["MaxT"][i]["parameter"]["parameterName"]
                p = el["PoP"][i]["parameter"]["parameterName"]
                embed.add_field(
                    name=f"{weather_emoji(w)} {start} → {end}",
                    value=f"{w}　🌡️ {lo}–{hi}°C　☔ {p}%",
                    inline=False,
                )
            embed.set_footer(text="資料來源：中央氣象署 CWA Open Data")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(e)
            await interaction.followup.send(f"❌ 失敗：{e}", ephemeral=True)


def setup(bot: discord.Bot):
    bot.add_cog(Weather(bot))