import discord
from discord.ext import commands
import os

TOKEN = 'NzA0NTI5OTYxODY3OTM1NzQ0.XqeeqA.e0JQZN13a6mWjlOYfsF1H2kiacc'
client = commands.Bot(command_prefix = '!')

@client.event
async def on_ready():
    print('Xerneas has connected to Discord')

cogs = [filename for filename in os.listdir("cogs") if filename.endswith(".py")]

for cog in cogs:
	cog_name = cog.split(".py")[0]
	client.load_extension(f"cogs.{cog_name}")
	
client.run(TOKEN)
