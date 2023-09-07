from datetime import datetime
import discord


class VoteSection(discord.ui.View):
    def __init__(self, options, channel,*args, **kwargs):
        super().__init__(*args, **kwargs)

        self.channel        = channel
        self.all_vote       = {options[i]:0 for i in range(len(options))}
        self.options        = options
        self.vote_dict      = {}
        self.select_options = [ discord.SelectOption(label=options[i]) for i in range(len(options))]

        self.select = discord.ui.Select(
            placeholder = "All team member",
            min_values  = 1, 
            max_values  = 1,
            options = self.select_options
            )


        self.select.callback = self.this_callback

        self.add_item(self.select)

    async def on_timeout(self):
        # print('[*] timeout')
        for user, voted in self.vote_dict.items():
            self.all_vote[voted] += 1


        sorted_vote = sorted(self.all_vote.items(), key=lambda x:x[1],reverse=True)


        name, get = "", ""
        for i,j in sorted_vote:
            name = name + str(i) + '\n'
            get  = get  + str(j) + '\n'

        embed = discord.Embed( title=f"Vote result.")
        embed.add_field(name="Option"  , value=name    ,inline=True)
        embed.add_field(name="number of votes" , value=get ,inline=True)
        await self.channel.send(embed=embed)

    async def this_callback(self, interaction):
        # which_chosen = self.options.index(self.select.values[0])

        if (interaction.user.id in self.vote_dict):
            await interaction.response.send_message(f"Change your vote to {self.select.values[0]}", ephemeral=True)
        else:
            await interaction.response.send_message(f"You voted {self.select.values[0]}", ephemeral=True)

        self.vote_dict[interaction.user.id] = self.select.values[0]
        # self.all_vote[which_chosen] = self.all_vote[which_chosen] + 1 
        # self.vote_dict

class DecideVote(discord.ui.Modal):
    def __init__(self, channel, timeout_min ,*args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.timeout_min = timeout_min
        self.channel     = channel
        self.add_item(discord.ui.InputText(label="Vote Option (Split with chage line)(換行來新增選項)", style=discord.InputTextStyle.long))


    async def callback(self, interaction: discord.Interaction):
        get_word = self.children[0].value.strip()
        if (len(get_word) == 0):
            await interaction.response.send_message(content=':white_check_mark: create a poll failed', ephemeral=True)
            return

        self.options = get_word.split("\n") 

        if (len(self.options) <= 1):
            await interaction.response.send_message(content=':white_check_mark: create a poll failed', ephemeral=True)
            return


        VoteS = VoteSection(self.options, self.channel, timeout=self.timeout_min*60)

        await interaction.response.send_message(content=':white_check_mark:  You have successfully create a vote', view=VoteS)