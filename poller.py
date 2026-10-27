import os
import time
import requests

APIFY_API_TOKEN = os.getenv("SCRAPER_API_KEY")
BACKEND_WEBHOOK_URL = os.getenv("BACKEND_WEBHOOK_URL")

def poll_tiktok_mentions():
    print("🔍 Checking TikTok for new mentions of @remind.meguy via Apify...")
    
    actor_id = "clockworks~tiktok-scraper"
    url = f"https://api.apify.com/v2/acts/{actor_id}/runs?token={APIFY_API_TOKEN}"
    
    payload = {
        "searchQueries": ["@remind.meguy"],
        "resultsPerPage": 10
    }
    
    try:
        # 1. Start the Apify actor run
        response = requests.post(url, json=payload)
        if response.status_code != 201:
            print(f"❌ Failed to trigger Apify actor: {response.text}")
            return
            
        run_data = response.json().get("data", {})
        run_id = run_data.get("id")
        dataset_id = run_data.get("defaultDatasetId")
        
        print(f"🚀 Apify actor triggered (Run ID: {run_id}). Waiting for results...")
        
        # 2. Wait for the Apify run to finish (polling status up to 2 minutes)
        status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_API_TOKEN}"
        for _ in range(24): # tries every 5 seconds for 2 minutes
            time.sleep(5)
            status_res = requests.get(status_url)
            if status_res.status_code == 200:
                status = status_res.json().get("data", {}).get("status")
                print(f"⏳ Actor status: {status}")
                if status == "SUCCEEDED":
                    break
                elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                    print(f"❌ Apify actor run failed with status: {status}")
                    return
        
        # 3. Fetch items from the Apify dataset
        dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={APIFY_API_TOKEN}"
        dataset_res = requests.get(dataset_url)
        
        if dataset_res.status_code != 200:
            print(f"❌ Failed to fetch dataset: {dataset_res.text}")
            return
            
        items = dataset_res.json()
        print(f"📦 Found {len(items)} items from Apify scrape.")
        
        # Ensure webhook URL path is correct
        base_url = BACKEND_WEBHOOK_URL.rstrip("/")
        webhook_url = base_url if base_url.endswith("/webhook/tiktok-comment") else f"{base_url}/webhook/tiktok-comment"

        # 4. Forward each scraped mention to your Render backend
        for item in items:
            # Adjust these keys based on what the Apify actor outputs (e.g., authorMeta/uniqueId or text)
            tiktok_user = item.get("authorMeta", {}).get("name") or item.get("uniqueId") or item.get("username", "unknown")
            comment_text = item.get("text") or item.get("comment", "")
            video_url = item.get("webVideoUrl") or item.get("videoUrl", "https://www.tiktok.com")

            forward_payload = {
                "user": tiktok_user,
                "comment": comment_text,
                "video_url": video_url
            }
            
            webhook_response = requests.post(webhook_url, json=forward_payload)
            print(f"📡 Forwarded comment from @{tiktok_user} to Render: Status {webhook_response.status_code}")

    except Exception as e:
        print(f"❌ Polling error: {e}")

if __name__ == "__main__":
    poll_tiktok_mentions()
