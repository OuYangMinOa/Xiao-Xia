
from utils.info       import logger
from discord.commands import slash_command, Option
from discord.ext      import commands

import discord

MORSE_CODE_DICT = { 'A':'.-', 'B':'-...',
                    'C':'-.-.', 'D':'-..', 'E':'.',
                    'F':'..-.', 'G':'--.', 'H':'....',
                    'I':'..', 'J':'.---', 'K':'-.-',
                    'L':'.-..', 'M':'--', 'N':'-.',
                    'O':'---', 'P':'.--.', 'Q':'--.-',
                    'R':'.-.', 'S':'...', 'T':'-',
                    'U':'..-', 'V':'...-', 'W':'.--',
                    'X':'-..-', 'Y':'-.--', 'Z':'--..',
                    '1':'.----', '2':'..---', '3':'...--',
                    '4':'....-', '5':'.....', '6':'-....',
                    '7':'--...', '8':'---..', '9':'----.',
                    '0':'-----', ', ':'--..--', '.':'.-.-.-',
                    '?':'..--..', '/':'-..-.', '-':'-....-',
                    '(':'-.--.', ')':'-.--.-'}

class Morse(discord.ext.commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="encrypt",description="Encrypt the given message")
    async def encrypt(self,ctx, message: Option(str, "word", required = True)):
        logger.info(f"{ctx.author.username} encrypting message : {message}")
        
        if (all(x.isalpha() or x.isspace() or x.isnumeric() for x in message)):
            cipher = ''
            for letter in message:
                if letter != ' ':
                    cipher += MORSE_CODE_DICT[letter.upper()] + ' '
                else:
                    cipher += ' '
            await ctx.respond(cipher)
        else:
            await ctx.respond("Invalid message")


    @slash_command(name="decrypt",description="Decrypt the given message")
    async def decrypt(self,ctx, message: Option(str, "word", required = True)):
        logger.info(f"{ctx.author.username} decrypting message : {message}")
        message += ' '  
        decipher = ''
        citext = ''
        for letter in message:
            if (letter != ' '):
                i = 0
                citext += letter
            else:
                i += 1
                if i == 2 :
                    decipher += ' ' 
                else:

                    decipher += list(MORSE_CODE_DICT.keys())[list(MORSE_CODE_DICT
                    .values()).index(citext)]
                    citext = ''
        await ctx.respond(decipher,ephemeral=True)



def setup(bot):
    bot.add_cog(Morse(bot))