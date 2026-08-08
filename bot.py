import json
import os
import requests
from bs4 import BeautifulSoup
from config import DISCOUNT_THRESHOLD
from notifier import send_alert

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "en-IN,en;q=0.9"
}

AMAZON_URLS = [
    "https://www.amazon.in/gp/goldbox",
    "https://www.amazon.in/deals?bubble-id=deals-collection-electronics"
]

FLIPKART_URLS = [
    "https://www.flipkart.com/mobiles/pr?sid=tyy,4io",
    "https://www.flipkart.com/laptops/pr?sid=6bo,b5g",
    "https://www.flipkart.com/audio-video/headphones/pr?sid=0pm,fcn",
    "https://www.flipkart.com/wearable-smart-devices/smart-watches/pr?sid=ajy,buh",
    "https://www.flipkart.com/televisions/pr?sid=ckf,czl",
    "https://www.flipkart.com/home-kitchen/home-appliances/air-coolers/pr?sid=j9e,abm,c54"
]

CACHE_FILE = "products_cache.json"

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(list(cache), f)

def parse_price(text):
    digits = "".join(ch for ch in text if ch.isdigit())
    return int(digits) if digits else None

def alert_if_new(cache, key, message):
    if key not in cache:
        send_alert(message)
        cache.add(key)

def scan_flipkart(cache):
    for base in FLIPKART_URLS:
        for page in range(1, 4):
            url = base + ("&page=" + str(page) if "?" in base else "?page=" + str(page))
            try:
                html = requests.get(url, headers=HEADERS, timeout=20).text
                soup = BeautifulSoup(html, "lxml")
                cards = soup.select("div._1AtVbE")
                for card in cards:
                    title = card.select_one("div.KzDlHZ, a.wjcEIp")
                    price = card.select_one("div.Nx9bqj")
                    mrp = card.select_one("div.yRaY8j")
                    if not title or not price or not mrp:
                        continue
                    current = parse_price(price.get_text())
                    original = parse_price(mrp.get_text())
                    if not current or not original or original <= current:
                        continue
                    discount = int((original - current) / original * 100)
                    if discount >= DISCOUNT_THRESHOLD:
                        key = title.get_text(strip=True)
                        msg = (
                            f"Flipkart {discount}% OFF\\n"
                            f"{key}\\n"
                            f"MRP: ₹{original}\\nNow: ₹{current}\\n{url}"
                        )
                        alert_if_new(cache, key, msg)
            except Exception:
                pass

def scan_amazon(cache):
    for url in AMAZON_URLS:
        try:
            html = requests.get(url, headers=HEADERS, timeout=20).text
            soup = BeautifulSoup(html, "lxml")
            cards = soup.select("div[data-deal-target], div.a-section")
            for card in cards:
                title = card.select_one("span.a-truncate-cut, span.a-size-base-plus")
                price = card.select_one("span.a-price-whole")
                mrp = card.select_one("span.a-price.a-text-price span.a-offscreen")
                if not title or not price or not mrp:
                    continue
                current = parse_price(price.get_text())
                original = parse_price(mrp.get_text())
                if not current or not original or original <= current:
                    continue
                discount = int((original - current) / original * 100)
                if discount >= DISCOUNT_THRESHOLD:
                    key = title.get_text(strip=True)
                    msg = (
                        f"Amazon {discount}% OFF\\n"
                        f"{key}\\n"
                        f"MRP: ₹{original}\\nNow: ₹{current}\\n{url}"
                    )
                    alert_if_new(cache, key, msg)
        except Exception:
            pass

def main():
    cache = load_cache()
    scan_amazon(cache)
    scan_flipkart(cache)
    save_cache(cache)

if __name__ == "__main__":
    main()
