import requests
from bs4 import BeautifulSoup
import json
import time
import random

WEBHOOK_URL = "https://discord.com/api/webhooks/1351274025434873896/wUJ9euEHYLNDBp_vTm-WLhyNhztwk2hGSDV45r54odQq1aLwFmR87oyhesDLMcSdrmom"

#Load proxies from file
def load_proxies(file_path):
    with open(file_path, 'r') as f:
        return [line.strip() for line in f if line.strip()]

#Formatting proxy
def get_proxy(proxies):
    proxy = random.choice(proxies)
    try:
        host, port, user, password = proxy.split(':')
        formatted_proxy = {
            "http": f"http://{user}:{password}@{host}:{port}",
            "https": f"http://{user}:{password}@{host}:{port}"
        }
        print(f"Using proxy: {formatted_proxy['http']}")
        return formatted_proxy
    except ValueError as e:
        print(f"Proxy format error: {e}")
        return None

def send_discord_notification(message):
    data = {"content": message}
    response = requests.post(WEBHOOK_URL, json=data)
    if response.status_code != 204:
        print(f"Failed to send Discord notification: {response.status_code}")

def check_stock(url, proxies, session):
    session.proxies = get_proxy(proxies) or {}  #Fallback to localhost if format fails
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-CA,en;q=0.5",
        "Referer": "https://www.walmart.ca/"
    }
    session.headers.update(headers)
    
    try:
        response = session.get(url, timeout=20)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        print("Debug: Raw HTML snippet:", soup.prettify()[:1000])
        
        #Find script tags with type="application/ld+json"
        script_tags = soup.find_all("script", type="application/ld+json")
        print(f"Debug: Found {len(script_tags)} script tags with type application/ld+json")
        
        #Search for the tag with "availability" and parse
        script_tag = None
        for script in script_tags:
            if script.string:
                print(f"Debug: Script content: {script.string[:200]}...")
                if "availability" in script.string.lower():
                    try:
                        data = json.loads(script.string)
                        #Check if its the product data by looking for "offers"
                        if "offers" in data and isinstance(data["offers"], list):
                            script_tag = script
                            break
                    except json.JSONDecodeError as e:
                        print(f"Debug: JSON parsing failed for this tag: {e}")
                        continue
        
        if script_tag and script_tag.string:
            try:
                data = json.loads(script_tag.string)
                print("Debug: Parsed Product Data:", json.dumps({k: data[k] for k in ["@context", "@type", "offers", "availability"] if k in data}, indent=2))
                #Extract availability from first offer
                availability = data.get("offers", [{}])[0].get("availability")
                print(f"Availability: {availability}")
                return availability == "https://schema.org/InStock"
            except (json.JSONDecodeError, IndexError) as e:
                print(f"Debug: Error processing offers: {e}")
                return False
        else:
            print("No product data script tag with availability found")
            return False
    
    except requests.RequestException as e:
        print(f"Request failed with proxy {session.proxies.get('http', 'no proxy')}: {e}")
        return None

#Monitoring loop
def monitor_product(url, proxy_file, interval=60):
    proxies = load_proxies(proxy_file)
    if not proxies:
        print("Error: No proxies found in file.")
        return
    
    session = requests.Session()
    print(f"Proxy selected: {len(proxies)}...")
    
    while True:
        in_stock = check_stock(url, proxies, session)
        if in_stock is True:
            message = f"Item is in stock! {url}"
            print(message)
            send_discord_notification(message)
            break
        elif in_stock is False:
            print("Item out of stock. Checking again...")
        else:
            print("Request failed, rotating proxy...")
        time.sleep(interval)

#Main function
if __name__ == "__main__":
    product_url = input("Enter Walmart product URL: ")
    proxy_file = input("Enter proxy file path (e.g., proxies.txt): ")
    try:
        monitor_product(product_url, proxy_file, interval=7)
    except KeyboardInterrupt:
        print("\nStopped by user.")
    except Exception as e:
        print(f"Unexpected error: {e}")