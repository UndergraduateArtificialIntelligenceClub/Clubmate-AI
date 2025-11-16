import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import random 
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✓ Bot is online as {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    if "hello" in message.content.lower():
        await message.add_reaction("👋")
    
    if message.content.lower() == "ping":
        await message.reply("Pong! 🏓")
    
    await bot.process_commands(message)

@bot.command(name="hello")
async def hello(ctx):
    await ctx.send(f"Hello {ctx.author.name}! 👋")

@bot.command(name="add")
async def add(ctx, num1: int, num2: int):
    result = num1 + num2
    await ctx.send(f"{num1} + {num2} = {result}")

@bot.command(name="roll")
async def roll(ctx,dice: str = "1d6"):
    try:
        parts = dice.lower().split("d")
        num_dice = int(parts[0])
        sides = int(parts[1])
        
        rolls = [random.randint(1, sides) for _ in range(num_dice)]
        total = sum(rolls)
        
        await ctx.send(f"🎲 Rolled {dice}: {rolls} = **{total}**")
    except:
        await ctx.send("Invalid format! Use `!roll 2d6` or `!roll 1d20`")

@bot.command(name="flip")
async def flip(ctx):
    result = random.choice(["Heads 🪙", "Tails 🪙"])
    await ctx.send(f"{ctx.author.name} flipped: {result}")

user_counters = {}

@bot.command(name="count")
async def count(ctx):
    user_id = ctx.author.id
    user_counters[user_id] = user_counters.get(user_id, 0) + 1
    await ctx.send(f"{ctx.author.name}, your count is: **{user_counters[user_id]}**")

@bot.command(name="mycount")
async def mycount(ctx):
    user_id = ctx.author.id
    count = user_counters.get(user_id, 0)
    await ctx.send(f"{ctx.author.name}, you have **{count}** counts!")

bot.run(TOKEN)
