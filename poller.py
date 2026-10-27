import os
import requests

APIFY_API_TOKEN = os.getenv("SCRAPER_API_KEY")
BACKEND_WEBHOOK_URL = os.getenv("BACKEND_WEBHOOK_URL")

def poll_tiktok_mentions():
    print("🔍 Checking TikTok for new mentions of @remind.meguy via Apify...")
    
    # Trigger the official Apify TikTok Scraper actor
    actor_id = "clockworks~tiktok-scraper"
    url = f"https://api.apify.com/v2/acts/{actor_id}/runs?token={APIFY_API_TOKEN}"
    
    payload = {
        "searchQueries": ["@remind.meguy"],
        "resultsPerPage": 10
    }
    
    try:
        # Start the Apify actor run
        response = requests.post(url, json=payload)
        if response.status_code != 201:
            print(f"❌ Failed to trigger Apify actor: {response.text}")
            return
            
        run_data = response.json().get("data", {})
        run_id = run_data.get("id")
        
        print(f"🚀 Apify actor triggered successfully (Run ID: {run_id}).")
        
        # Send test webhook to Render with guaranteed correct path alignment
        if BACKEND_WEBHOOK_URL:
            base_url = BACKEND_WEBHOOK_URL.rstrip("/")
            if not base_url.endswith("/webhook/tiktok-comment"):
                webhook_url = f"{base_url}/webhook/tiktok-comment"
            else:
                webhook_url = base_url

            test_payload = {
                "user": "your_tiktok_username",
                "comment": "@remind.meguy in 1 minute",
                "video_url": "https://www.tiktok.com/@example/video/123456789"
            }
            webhook_response = requests.post(webhook_url, json=test_payload)
            print(f"📡 Sent test webhook to {webhook_url}: Status {webhook_response.status_code}")

    except Exception as e:
        print(f"❌ Polling error: {e}")

if __name__ == "__main__":
    poll_tiktok_mentions()
