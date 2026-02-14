#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import sys
import time

class OriconRSSGenerator:
    def __init__(self):
        self.base_url = "https://us.oricon-group.com"
        self.category_url = f"{self.base_url}/category/anime/"
        
        # Use CORS proxies to bypass blocking
        self.proxies = [
            "https://api.allorigins.win/raw?url=",
            "https://corsproxy.io/?",
            "https://api.codetabs.com/v1/proxy?quest="
        ]
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
    
    def fetch_page(self):
        print(f"Fetching: {self.category_url}")
        
        # Try direct first
        try:
            print("Trying direct access...")
            response = self.session.get(self.category_url, timeout=30)
            if response.status_code == 200 and len(response.text) > 1000:
                print("Direct access successful!")
                return response.text
        except Exception as e:
            print(f"Direct failed: {e}")
        
        # Try proxies
        for proxy in self.proxies:
            try:
                print(f"Trying proxy: {proxy}")
                proxy_url = proxy + self.category_url
                response = self.session.get(proxy_url, timeout=30)
                
                if response.status_code == 200 and len(response.text) > 1000:
                    print(f"Proxy worked: {proxy}")
                    return response.text
            except Exception as e:
                print(f"Proxy failed: {e}")
                continue
            time.sleep(1)
        
        return None
    
    def parse_articles(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        articles = []
        
        selectors = ['article', '.article-item', '[class*="article"]', 'a[href*="/anime/"]', 'h2 a']
        
        elements = []
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                print(f"Found {len(elements)} with: {selector}")
                break
        
        if not elements:
            articles.append({
                'title': 'Oricon Anime News',
                'link': self.category_url,
                'description': 'Visit Oricon for anime news',
                'pubDate': datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000'),
                'image': None
            })
            return articles
        
        for elem in elements[:20]:
            try:
                title_elem = elem.find(['h1', 'h2', 'h3']) or elem
                title = title_elem.get_text(strip=True)
                
                if not title or len(title) < 5:
                    continue
                
                link_elem = elem if elem.name == 'a' else elem.find('a')
                if not link_elem or not link_elem.get('href'):
                    continue
                
                href = link_elem['href']
                link = href if href.startswith('http') else self.base_url + href
                
                desc_elem = elem.find('p')
                description = desc_elem.get_text(strip=True) if desc_elem else title
                if len(description) > 300:
                    description = description[:297] + "..."
                
                date_elem = elem.find('time')
                pubDate = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
                
                img_elem = elem.find('img')
                image = None
                if img_elem:
                    src = img_elem.get('src') or img_elem.get('data-src')
                    if src:
                        image = src if src.startswith('http') else self.base_url + src
                
                articles.append({
                    'title': title,
                    'link': link,
                    'description': description,
                    'pubDate': pubDate,
                    'image': image
                })
            except:
                continue
        
        return articles
    
    def generate_rss(self, articles):
        now = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
        
        xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Oricon Anime News</title>
    <link>{self.category_url}</link>
    <description>Latest anime news from Oricon</description>
    <lastBuildDate>{now}</lastBuildDate>
'''
        
        for article in articles:
            title = article['title'].replace('&', '&amp;')
            description = article['description'].replace('&', '&amp;')
            
            xml += f'''    <item>
      <title><![CDATA[{title}]]></title>
      <link>{article['link']}</link>
      <description><![CDATA[{description}]]></description>
      <pubDate>{article['pubDate']}</pubDate>
      <guid>{article['link']}</guid>
'''
            if article['image']:
                xml += f'''      <enclosure url="{article['image']}" type="image/jpeg"/>
'''
            xml += '''    </item>
'''
        
        xml += '''  </channel>
</rss>'''
        return xml
    
    def generate(self, output_file):
        html = self.fetch_page()
        
        if not html:
            articles = [{
                'title': 'Feed Temporarily Unavailable',
                'link': self.category_url,
                'description': 'Check back later',
                'pubDate': datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000'),
                'image': None
            }]
        else:
            articles = self.parse_articles(html)
            if not articles:
                articles = [{
                    'title': 'No Articles Found',
                    'link': self.category_url,
                    'description': 'Visit Oricon directly',
                    'pubDate': datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000'),
                    'image': None
                }]
        
        rss_xml = self.generate_rss(articles)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(rss_xml)
        
        print(f"Generated {len(articles)} articles")
        return True

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output', required=True)
    args = parser.parse_args()
    
    generator = OriconRSSGenerator()
    generator.generate(args.output)
