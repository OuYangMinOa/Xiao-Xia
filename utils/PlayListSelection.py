from utils.info       import silinece_channel
from discord.commands import slash_command, Option
from discord.ext      import commands
from utils.info       import logger
from utils.info       import sound_user, music_user
from glob             import glob
from pydub            import AudioSegment


import utils.MusicBot     as my_mb # my class
import discord
import os

def LoadPlaylist(filename):
    output = []
    with open(filename,'r',encoding='utf-8') as f:
        text = f.read()
    for line in text.split("\n"):
        output.append(line.split(","))
    return output

class PlayListSelection:
    def __init__(self,music_class,fullpath):
        self.music_class   = music_class
        self.label,self.path = [],[]
        for i in glob(fullpath+"/*.txt"):
            self.label.append(os.path.basename(i)[:-4])
            self.path.append(i)

        self.view = discord.ui.View(timeout=3600)


        if(len(self.label)>0):
            options = [ discord.SelectOption(label=self.label[i])for i in range(len(self.label))]

            self.select = discord.ui.Select(    
                    placeholder = "Playlist",
                    min_values  = 1, 
                    max_values  = 1,
                    options = options
                )
            self.select.callback = self.callback
            self.view.add_item(self.select)



    async def callback(self, interaction):
        which_chosen = self.label.index(self.select.values[0])
        await interaction.response.send_message(f'Playing : {self.label[which_chosen]}')
        await self.music_class.clear()
        self.music_class.queqed = LoadPlaylist(self.path[which_chosen])
        self.music_class.passed = []
        await self.music_class._next()