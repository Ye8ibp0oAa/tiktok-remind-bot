import os
import requests

# Configuration via environment variables
SCRAPER_API_URL = os.getenv("SCRAPER_API_URL", "https://api.scraper-provider.com/v1/tiktok/search/comments")
SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY")
BACKEND_WEBHOOK_URL = os.getenv("BACKEND_WEBHOOK_URL") # e.g., https://your-bot.onrender.com/webhook/tiktok-comment

def poll_tiktok_mentions():
    print("🔍 Checking TikTok for new mentions of @remind.meguy...")
    
    headers = {"Authorization": f"Bearer {SCRAPER_API_KEY}"}
    params = {"query": "@remind.meguy"}
    
    try:
        response = requests.get(SCRAPER_API_URL, headers=headers, params=params, timeout=30)
        results = response.json().get("comments", [])
        
        for item in results:
            payload = {
                "comment_id": item.get("comment_id"),
                "user": item.get("author_username"),
                "comment": item.get("text"),
                "video_url": item.get("video_url")
            }
            
            # Fire to your FastAPI backend
            res = requests.post(BACKEND_WEBHOOK_URL, json=payload, timeout=10)
            print(f"Forwarded comment: {res.json()}")
            
    except Exception as e:
        print(f"❌ Polling error: {e}")

if __name__ == "__main__":
    poll_tiktok_mentions()