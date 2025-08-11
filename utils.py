import requests
from bs4 import BeautifulSoup

def fetch_news_from_pib():
    url = "https://pib.gov.in/allRel.aspx?menuid=10351"
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")

        news_items = []
        for link in soup.select("ul.pressrelease li a"):
            title = link.text.strip()
            href = link.get("href")
            if href and "PressReleseDetail.aspx" in href:
                full_link = "https://pib.gov.in/" + href
                news_items.append({"title": title, "link": full_link})

        return news_items[:5]
    except Exception as e:
        print(f"[ERROR] Failed to fetch PIB news: {e}")
        return []
