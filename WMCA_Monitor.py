import requests
from bs4 import BeautifulSoup
import time
import random
import json
from urllib.parse import urlparse, parse_qs

WEBHOOK_URL = "https://discord.com/api/webhooks/1349815370428448810/pbl3dUbt21FtjGBWNUlCL3pKLnXRSu08UyZQyLfZyz-IcSQeJf0B8NACpXTZj3MW1q13"

# Load proxies from a file
def load_proxies(file_path):
    with open(file_path, 'r') as f:
        return [line.strip() for line in f if line.strip()]

# Pick a random proxy and format it
def get_proxy(proxies):
    proxy = random.choice(proxies)
    host, port, user, password = proxy.split(':')
    return {
        "http": f"http://{user}:{password}@{host}:{port}",
        "https": f"http://{user}:{password}@{host}:{port}"
    }

# Send discord notification
def send_discord_notification(message):
    data = {"content": message}
    requests.post(WEBHOOK_URL, json=data)

# Check stock 
def check_stock(url, proxies):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
    }
    proxy = get_proxy(proxies)
    
    try:
        response = requests.get(url, headers=headers, proxies=proxy, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        stock_text = soup.find(text="In stock") or soup.find(text="Instock")
        if stock_text:
            return True
        return False
    except requests.RequestException as e:
        print(f"Error with proxy {proxy['http']}: {e}")
        return None

# Monitoring loop
def monitor_product(url, proxy_file, interval=5):
    proxies = load_proxies(proxy_file)
    print(f"Monitoring {url} with {len(proxies)} proxies...")
    
    while True:
        in_stock = check_stock(url, proxies)
        if in_stock is True:
            send_discord_notification(f"Item is in stock! {url}")
            print("Item in stock! Notification sent.")
            break
        elif in_stock is False:
            print("Item out of stock. Checking again...")
        else:
            print("Request failed, rotating proxy...")
        
        time.sleep(interval)

# Run it
if __name__ == "__main__":
    product_url = input("Enter Walmart product URL: ")
    proxy_file = input("Enter proxy file path (e.g., proxies.txt): ")
    monitor_product(product_url, proxy_file)