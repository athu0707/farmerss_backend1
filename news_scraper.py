import requests
from bs4 import BeautifulSoup

def get_farmer_news():
    try:
        # PIB agriculture-related search results page
        url = "https://pib.gov.in/PressReleaseAdvancedSearch.aspx?SearchText=agriculture"
        response = requests.get(url, timeout=5)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, "html.parser")

        news_list = []
        for a in soup.select("a"):
            title = a.get_text(strip=True)
            link = a.get("href")
            if link and "Release" in link:  # Only pick press release links
                if not link.startswith("http"):
                    link = "https://pib.gov.in/" + link
                news_list.append({"title": title, "url": link})
            if len(news_list) >= 5:
                break

        # If scraping returns nothing, show fallback sample news
        if not news_list:
            news_list = [
                {"title": "New crop policy boosts farmer income", "url": "#"},
                {"title": "Govt announces MSP hike for key crops", "url": "#"},
                {"title": "Digital tools help optimize farm supply chain", "url": "#"},
                {"title": "Organic farming gaining popularity", "url": "#"},
                {"title": "New irrigation methods save water", "url": "#"}
            ]

        return news_list

    except Exception:
        # Always return fallback if any error occurs
        return [
            {"title": "New crop policy boosts farmer income", "url": "#"},
            {"title": "Govt announces MSP hike for key crops", "url": "#"},
            {"title": "Digital tools help optimize farm supply chain", "url": "#"},
            {"title": "Organic farming gaining popularity", "url": "#"},
            {"title": "New irrigation methods save water", "url": "#"}
        ]
