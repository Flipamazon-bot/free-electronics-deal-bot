import requests
from bs4 import BeautifulSoup
from config import AMAZON_URLS, FLIPKART_URLS, DISCOUNT_THRESHOLD
from notifier import send_alert

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "en-IN,en;q=0.9"
}

def parse_price(text):
    digits = "".join(ch for ch in text if ch.isdigit())
    return int(digits) if digits else None

def scan_flipkart():
    for url in FLIPKART_URLS:
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

                if not current or not original:
                    continue

                discount = int((original - current) / original * 100)

                if discount >= DISCOUNT_THRESHOLD:
                    send_alert(
                        f"Flipkart {discount}% OFF\\n"
                        f"{title.get_text(strip=True)}\\n"
                        f"MRP: ₹{original}\\nNow: ₹{current}\\n{url}"
                    )
        except Exception:
            pass

def scan_amazon():
    for url in AMAZON_URLS:
        try:
            html = requests.get(url, headers=HEADERS, timeout=20).text
            soup = BeautifulSoup(html, "lxml")

            cards = soup.select("div[data-deal-target]")

            for card in cards:
                title = card.select_one("span.a-truncate-cut, span.a-size-base-plus")
                price = card.select_one("span.a-price-whole")
                mrp = card.select_one("span.a-price.a-text-price span.a-offscreen")

                if not title or not price or not mrp:
                    continue

                current = parse_price(price.get_text())
                original = parse_price(mrp.get_text())

                if not current or not original:
                    continue

                discount = int((original - current) / original * 100)

                if discount >= DISCOUNT_THRESHOLD:
                    send_alert(
                        f"Amazon {discount}% OFF\\n"
                        f"{title.get_text(strip=True)}\\n"
                        f"MRP: ₹{original}\\nNow: ₹{current}\\n{url}"
                    )
        except Exception:
            pass

def main():
    scan_amazon()
    scan_flipkart()

if __name__ == "__main__":
    main()
