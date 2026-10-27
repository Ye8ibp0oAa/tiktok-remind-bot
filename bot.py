import os
import asyncio
import datetime
import dateparser
from fastapi import FastAPI, Request
import discord
from discord.ext import commands

app = FastAPI()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Simple in-memory user mapping: {"tiktok_handle": "discord_user_id"}
USER_MAPPINGS = {}

@app.on_event("startup")
async def startup_event():
    # Automatically start the Discord bot in the background when FastAPI boots up
    asyncio.create_task(bot.start(DISCORD_BOT_TOKEN))

@bot.tree.command(name="register", description="Link your TikTok handle to receive reminder DMs here")
async def register(interaction: discord.Interaction, tiktok_handle: str):
    clean_handle = tiktok_handle.replace("@", "").strip().lower()
    USER_MAPPINGS[clean_handle] = str(interaction.user.id)
    
    await interaction.response.send_message(
        f"✅ Successfully linked **@{clean_handle}** to your Discord account! You will now receive your TikTok reminders in your DMs.",
        ephemeral=True
    )

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"🤖 Discord Bot logged in as: {bot.user} | Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"❌ Command sync failed: {e}")

@app.post("/webhook/tiktok-comment")
async def handle_tiktok_comment(request: Request):
    data = await request.json()

    raw_user = data.get("user", "").replace("@", "").strip().lower()
    comment_text = data.get("comment", "")
    video_url = data.get("video_url", "No video link provided")

    # Check if the user has linked their Discord account
    discord_id = USER_MAPPINGS.get(raw_user)
    if not discord_id:
        return {"status": "ignored", "reason": f"User @{raw_user} has not registered on Discord yet."}

    # Extract time phrase (e.g., "@remind.meguy in 2 hours" -> "in 2 hours")
    time_phrase = comment_text.lower().replace("@remind.meguy", "").strip()
    
    remind_at = dateparser.parse(
        time_phrase,
        settings={'PREFER_DATES_FROM': 'future', 'RELATIVE_BASE': datetime.datetime.now()}
    )

    if not remind_at:
        return {"status": "error", "message": f"Could not parse time string: '{time_phrase}'"}

    delay_seconds = int((remind_at - datetime.datetime.now()).total_seconds())
    if delay_seconds <= 0:
        return {"status": "error", "message": "Reminder time must be in the future."}

    # Schedule background timer for Discord DM delivery
    asyncio.create_task(
        schedule_discord_dm(delay_seconds, discord_id, raw_user, video_url, remind_at)
    )

    return {"status": "scheduled", "user": raw_user, "remind_at": remind_at.isoformat()}

async def schedule_discord_dm(delay: int, discord_id: str, tiktok_user: str, video_url: str, remind_at: datetime.datetime):
    await asyncio.sleep(delay)
    try:
        user = await bot.fetch_user(int(discord_id))
        embed = discord.Embed(
            title="⏰ TikTok Reminder!",
            description=f"Hey **@{tiktok_user}**, here is the video you asked to be reminded about:",
            color=0xfe2c55
        )
        embed.add_field(name="Video Link", value=video_url, inline=False)
        embed.set_footer(text=f"Scheduled for: {remind_at.strftime('%b %d, %Y at %I:%M %p')}")
        
        await user.send(embed=embed)
        print(f"✅ Reminder delivered to Discord user: {discord_id}")
    except Exception as e:
        print(f"❌ Failed to send Discord DM: {e}")
