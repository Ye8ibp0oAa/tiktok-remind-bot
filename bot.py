import os
import asyncio
import discord
from discord.ext import commands
from fastapi import FastAPI, Request, HTTPException
import uvicorn
from datetime import datetime, timedelta

# --- Configuration & Environment Variables ---
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# --- Initialize FastAPI & Discord Bot ---
app = FastAPI()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# In-memory storage for user handles (or use a database/json file)
# Maps tiktok_username -> discord_user_id
user_registry = {}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("Bot is online and ready!")

@bot.tree.command(name="register", description="Link your TikTok handle to receive reminder DMs")
async def register(interaction: discord.Interaction, tiktok_handle: str):
    clean_handle = tiktok_handle.lstrip("@").lower()
    user_registry[clean_handle] = interaction.user.id
    await interaction.response.send_message(
        f"✅ Success! Linked TikTok handle `@{clean_handle}` to your Discord account.",
        ephemeral=True
    )

# --- Webhook Endpoint for Apify / GitHub Poller ---
@app.post("/webhook/tiktok-comment")
async def handle_tiktok_comment(request: Request):
    try:
        data = await request.json()
        tiktok_user = data.get("user", "").lstrip("@").lower()
        comment_text = data.get("comment", "")
        video_url = data.get("video_url", "https://www.tiktok.com")

        print(f"Received webhook for TikTok user: {tiktok_user}, comment: {comment_text}")

        # Check if this TikTok user has registered with the bot
        discord_user_id = user_registry.get(tiktok_user)
        if not discord_user_id:
            return {"status": "ignored", "reason": "User not registered"}

        # Fetch the Discord user and send a DM
        discord_user = await bot.fetch_user(discord_user_id)
        if discord_user:
            embed = discord.Embed(
                title="⏰ TikTok Reminder!",
                description=f"You asked to be reminded based on your comment: *\"{comment_text}\"*",
                color=discord.Color.blue()
            )
            embed.add_field(name="Video Link", value=video_url, inline=False)
            await discord_user.send(embed=embed)
            return {"status": "success", "message": "DM sent successfully"}

        return {"status": "error", "message": "Discord user not found"}

    except Exception as e:
        print(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Background task to start Discord bot alongside FastAPI ---
@app.on_event("startup")
async def startup_event():
    # Run the Discord bot in the background loop
    asyncio.create_task(bot.start(DISCORD_TOKEN))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.main(["bot:app", "--host", "0.0.0.0", "--port", str(port)])
