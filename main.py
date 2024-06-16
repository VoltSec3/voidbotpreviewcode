import discord
import os
import aiohttp
import requests
import random
import json
import io
from PIL import Image
from moviepy.editor import VideoFileClip
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv
from colorama import init, Fore

init(autoreset=True)
load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all(), help_command=None, case_insensitive=True)

@bot.event
async def on_ready():
    print("Connection Success.")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(f"Error syncing commands: {e}")

@bot.event
async def on_command(ctx):
    print(f"{Fore.GREEN}{ctx.author.display_name} has used command {Fore.MAGENTA}{ctx.command}")

@bot.tree.command(name="cat", description="Get a random cat image")
async def cat(interaction: discord.Interaction):
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.thecatapi.com/v1/images/search') as resp:
            if resp.status == 200:
                data = await resp.json()
                cat_url = data[0]['url']
                await interaction.response.send_message(cat_url)
            else:
                await interaction.response.send_message('Could not fetch a cat image, please try again later.')

@bot.tree.command(name="dog", description="Get a random dog image")
async def dog(interaction: discord.Interaction):
    async with aiohttp.ClientSession() as session:
        async with session.get('https://dog.ceo/api/breeds/image/random') as resp:
            if resp.status == 200:
                data = await resp.json()
                dog_url = data['message']
                await interaction.response.send_message(dog_url)
            else:
                await interaction.response.send_message('Could not fetch a dog image, please try again later.')

@bot.tree.command(name="ping", description="Check the bot's latency")
async def ping(interaction: discord.Interaction):
    latency = bot.latency * 1000
    await interaction.response.send_message(f'Pong! Latency: {latency:.2f}ms')


@bot.tree.command(name="clear", description="Clear a number of messages from the channel")
@app_commands.describe(amount="Number of messages to delete")
async def clear(interaction: discord.Interaction, amount: int):
    if interaction.user.guild_permissions.manage_messages:
        await interaction.channel.purge(limit=amount + 1)
        await interaction.response.send_message(f'Cleared {amount} messages!', ephemeral=True)
    else:
        await interaction.response.send_message('You do not have permission to use this command.', ephemeral=True)

def fetch_meme():
    url = "https://meme-api.com/gimme"
    try:
        response = requests.get(url)
        data = response.json()
        return data['url']
    except Exception as e:
        print(f"Error fetching meme: {e}")
        return None
@bot.tree.command(name="meme", description="Fetch a random meme")
async def meme(interaction: discord.Interaction):
    meme_url = fetch_meme()
    if meme_url:
        await interaction.response.send_message(meme_url)
    else:
        await interaction.response.send_message("Failed to fetch a meme. Please try again later.")

@bot.tree.command(name="serverinfo", description="Display information about the server")
async def serverinfo(interaction: discord.Interaction):
    guild = interaction.guild
    embed = discord.Embed(title="Server Information", color=discord.Color.green())
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.add_field(name="Server Name", value=guild.name, inline=True)
    embed.add_field(name="Server ID", value=guild.id, inline=True)
    created_at_formatted = guild.created_at.strftime("%m/%d/%y, at %I:%M %p")
    embed.add_field(name="Created On", value=created_at_formatted, inline=False)
    embed.add_field(name="Member Count", value=guild.member_count, inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="userinfo", description="Show information about a user")
@app_commands.describe(user="The user to get information about")
async def userinfo(interaction: discord.Interaction, user: discord.User):
    embed = discord.Embed(title="User Information", color=discord.Color.blue())
    if isinstance(user, discord.Member):
        embed.set_thumbnail(url=user.avatar.url)
    embed.add_field(name="Username", value=user.name, inline=True)
    embed.add_field(name="Joined Discord", value=user.created_at.strftime("%m/%d/%y, at %I:%M %p"), inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="rps", description="Play rock-paper-scissors")
@app_commands.describe(choice="Your choice: rock, paper, or scissors")
async def rps(interaction: discord.Interaction, choice: str):
    choices = ['rock', 'paper', 'scissors']
    bot_choice = random.choice(choices)
    
    if choice.lower() not in choices:
        await interaction.response.send_message("Please choose either rock, paper, or scissors!")
        return
    
    if choice.lower() == bot_choice:
        await interaction.response.send_message(f"Both chose {bot_choice}. It's a tie!")
    elif (choice.lower() == 'rock' and bot_choice == 'scissors') or \
         (choice.lower() == 'paper' and bot_choice == 'rock') or \
         (choice.lower() == 'scissors' and bot_choice == 'paper'):
        await interaction.response.send_message(f"You chose {choice}. CPU chose {bot_choice}. You win!")
    else:
        await interaction.response.send_message(f"You chose {choice}. CPU chose {bot_choice}. CPU wins!")

@bot.tree.command(name="leet", description="Convert text to leet speak")
@app_commands.describe(text="Text to convert")
async def leet(interaction: discord.Interaction, text: str):
    leet_text = text.lower()
    leet_text = leet_text.replace('a', '4')
    leet_text = leet_text.replace('e', '3')
    leet_text = leet_text.replace('l', '1')
    leet_text = leet_text.replace('o', '0')
    leet_text = leet_text.replace('t', '7')
    leet_text = leet_text.replace('s', '5')
    leet_text = leet_text.replace('i', '!')
    leet_text = leet_text.replace('b', '8')
    
    await interaction.response.send_message(leet_text)

lockdown_status = {}
@bot.tree.command(name="lockdown", description="Toggle lockdown for all text channels")
async def lockdown(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        try:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        except discord.errors.NotFound:
            pass
        return
    guild = interaction.guild
    if guild.id in lockdown_status and lockdown_status[guild.id]:
        for channel in guild.text_channels:
            await channel.set_permissions(guild.default_role, send_messages=None)
        lockdown_status[guild.id] = False
        try:
            await interaction.response.send_message("Lockdown deactivated. Normal channel permissions restored.")
        except discord.errors.NotFound:
            pass 
    else:
        for channel in guild.text_channels:
            await channel.set_permissions(guild.default_role, send_messages=False)
        lockdown_status[guild.id] = True
        try:
            await interaction.response.send_message("Lockdown activated. Only administrators can send messages.")
        except discord.errors.NotFound:
            pass

@bot.command()
async def gif(ctx):
    if len(ctx.message.attachments) == 0:
        await ctx.send("Please attach an image to convert to a GIF.")
        return
    
    attachment = ctx.message.attachments[0]
    if not attachment.filename.endswith(('.png', '.jpg', '.jpeg')):
        await ctx.send("Please attach a valid image file (PNG or JPEG) to convert to a GIF.")
        return
    
    try:
        image_bytes = await attachment.read()
        image = Image.open(io.BytesIO(image_bytes))
        
        gif_io = io.BytesIO()
        image.save(gif_io, format='GIF', save_all=True, append_images=[image], duration=100, loop=0)
        gif_io.seek(0)
        
        await ctx.send(file=discord.File(gif_io, filename='image.gif'))
    except Exception as e:
        print(e)
        await ctx.send("Failed to convert image to GIF.")

bot.run(TOKEN)
