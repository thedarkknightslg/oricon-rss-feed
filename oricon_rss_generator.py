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
        
        # Multiple free proxies
        self.proxies = [
            "https://api.allorigins.win/raw?url=",
            "https://corsproxy.io/?",
            "https://api.codetabs.com/v1/proxy?quest=",
            "https://proxy.cors.sh/",
            "https://thingproxy.freeboard.io/fetch/",
        ]
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
    
    def fetch_page(self):
        print(f"Fetching: {self.category_url}")
        
        # Try direct
        try:
            print("Trying direct...")
            response = self.session.get(self.category_url, timeout=30)
            if response.status_code == 200 and len(response.text) > 5000:
                print(f"Direct worked! ({len(response.text)} bytes)")
                return response.text
        except Exception as e:
            print(f"Direct failed: {e}")
        
        # Try proxies
        for i, proxy in enumerate(self.proxies, 1):
            try:
                from urllib.parse import quote
                proxy_url = proxy + quote(self.category_url, safe='') if '?' in proxy else proxy + self.category_url
                
                print(f"Trying proxy {i}...")
                response = self.session.get(proxy_url, timeout=45)
                
                if response.status_code == 200 and len(response.text) > 5000:
                    print(f"Proxy {i} worked! ({len(response.text)} bytes)")
                    return response.text
                else:
                    print(f"Proxy {i}: {response.status_code}, {len(response.text)} bytes")
                    
            except Exception as e:
                print(f"Proxy {i} failed: {str(e)[:80]}")
            
            time.sleep(2)
        
        print("All methods failed!")
        return None
    
    def parse_articles(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        articles = []
        
        selectors = [
            'article',
            '[class*="post"]',
            '[class*="article"]',
            'a[href*="/anime/"]',
            'h2 a',
            'h3 a'
        ]
        
        elements = []
        for selector in selectors:
            elements = soup.select(selector)
            if len(elements) >= 3:
                print(f"Found {len(elements)} with: {selector}")
                break
        
        if not elements:
            return self._placeholder()
        
        seen = set()
        for elem in elements[:50]:
            try:
                title_elem = elem.find(['h1', 'h2', 'h3']) or elem
                title = title_elem.get_text(strip=True)
                
                if not title or len(title) < 10:
                    continue
                
                link_elem = elem if elem.name == 'a' else elem.find('a')
                if not link_elem:
                    continue
                
                href = link_elem.get('href', '')
                if not href or href.startswith(('#', 'javascript:', 'mailto:')):
                    continue
                
                link = href if href.startswith('http') else self.base_url + href
                
                if link in seen:
                    continue
                seen.add(link)
                
                desc_elem = elem.find('p')
                description = desc_elem.get_text(strip=True) if desc_elem else title
                if len(description) > 400:
                    description = description[:397] + "..."
                
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
                
                if len(articles) >= 20:
                    break
                    
            except Exception as e:
                continue
        
        if not articles:
            return self._placeholder()
        
        print(f"Extracted {len(articles)} articles")
        return articles
    
    def _placeholder(self):
        return [{
            'title': 'Oricon Anime News - Feed Temporarily Unavailable',
            'link': self.category_url,
            'description': 'Unable to fetch news. The feed will retry automatically.',
            'pubDate': datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000'),
            'image': None
        }]
    
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
            title = article['title'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            description = article['description'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
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
        print("=== ORICON RSS GENERATOR ===")
        
        html = self.fetch_page()
        articles = self.parse_articles(html) if html else self._placeholder()
        rss_xml = self.generate_rss(articles)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(rss_xml)
        
        print(f"Generated {len(articles)} articles to {output_file}")
        return True

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output', required=True)
    args = parser.parse_args()
    
    generator = OriconRSSGenerator()
    generator.generate(args.output)
                
