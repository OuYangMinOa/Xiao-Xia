from utils.info       import logger
from utils.music_ui   import info_embed, COLOR_DONE
from glob             import glob


import discord
import os

def LoadPlaylist(filename):
    output = []
    with open(filename,'r',encoding='utf-8') as f:
        text = f.read()
    for line in text.split("\n"):
        if (',' not in line):
            continue
        # titles may contain commas, the url never does
        title, url = line.rsplit(",", 1)
        output.append((title, url))
    return output

class PlayListSelection:
    def __init__(self,music_class,fullpath):
        self.music_class   = music_class
        self.label,self.path = [],[]
        for i in sorted(glob(fullpath+"/*.txt")):
            self.label.append(os.path.basename(i)[:-4])
            self.path.append(i)

        self.view = discord.ui.View(timeout=3600, disable_on_timeout=True)


        if(len(self.label)>0):
            options = [ discord.SelectOption(label=self.label[i][:100], value=str(i), emoji="📂") for i in range(len(self.label))][:25]

            self.select = discord.ui.Select(
                    placeholder = "選一個歌單",
                    min_values  = 1,
                    max_values  = 1,
                    options = options
                )
            self.select.callback = self.callback
            self.view.add_item(self.select)



    async def callback(self, interaction):
        which_chosen = int(self.select.values[0])
        songs = LoadPlaylist(self.path[which_chosen])
        logger.info(f"[*] loading playlist {self.path[which_chosen]} ({len(songs)} songs)")
        await interaction.response.send_message(embed=info_embed(
            f"📂 {interaction.user.mention} 開始播放歌單 **{discord.utils.escape_markdown(self.label[which_chosen])}**（{len(songs)} 首）",
            COLOR_DONE))
        await self.music_class.clear()
        self.music_class.queqed = songs
        self.music_class.passed = []
        self.music_class.note(f"📂 {interaction.user.display_name} 播放了歌單 {self.label[which_chosen]}")
        await self.music_class._next()
