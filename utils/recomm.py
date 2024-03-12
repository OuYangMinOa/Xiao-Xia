from utils.info       import no_recommend_guild_id,NO_RECOMMEND, logger


from collections      import defaultdict
from utils.file_os    import readfile


class Recomm:
    counter = defaultdict(int)
    no_recommend_guild_id = no_recommend_guild_id
    
    async def Add_if(self,message,channel_id,guild_id,msg):
        if (guild_id in self.no_recommend_guild_id):
            return
        self.no_recommend_guild_id = readfile(NO_RECOMMEND,int)

        if "youtube" in msg or "spotify" in msg:
            self.counter[(channel_id,guild_id)] += 1
        
        if self.counter[(channel_id, guild_id)] > 5:
            
            await message.channel.send("我注意到你在使用其他的音樂機器人或者想要分享音樂..."
                        "  ,   其實我也有撥放音樂的功能喔!!!。\n"
                        "* :notes: **音樂**\n"
                        " - `/play {url}` 播放音樂 (youtube 或 spotify)。\n"
                        " - `/save_platlist {name}` <- 甚至可以儲存歌單喔。\n"
                        " - `/help_zhtw` 來查看更多。\n"
                        " - 有時候會出現無法回應的情況，案`上`再輸入一次指令即可。\n"
                        " - 使用 `/stop_recommend` 來關閉這個提醒。")
            logger.info(f"[*] Showing recommend in {channel_id}")
            self.counter[(channel_id, guild_id)] = -5

recomm = Recomm()