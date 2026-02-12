#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import sys

class OriconRSSGenerator:
    def __init__(self):
        self.base_url = "https://us.oricon-group.com"
        self.category_url = f"{self.base_url}/category/anime/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch_page(self):
        try:
            print(f"Fetching: {self.category_url}")
            response = self.session.get(self.category_url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def parse_articles(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        articles = []
        
        selectors = ['article', '.post', '[class*="article"]', 'a[href*="/anime/"]']
        elements = []
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                break
        
        for elem in elements[:20]:
            try:
                title_elem = elem.find(['h1', 'h2', 'h3']) or elem
                title = title_elem.get_text(strip=True) or "No title"
                
                link_elem = elem if elem.name == 'a' else elem.find('a')
                if not link_elem or not link_elem.get('href'):
                    continue
                
                href = link_elem['href']
                link = href if href.startswith('http') else self.base_url + href
                
                desc_elem = elem.find('p')
                description = desc_elem.get_text(strip=True) if desc_elem else title
                
                date_elem = elem.find('time')
                if date_elem:
                    date_str = date_elem.get('datetime') or date_elem.get_text(strip=True)
                    try:
                        pubDate = datetime.strptime(date_str[:10], '%Y-%m-%d').strftime('%a, %d %b %Y %H:%M:%S +0000')
                    except:
                        pubDate = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
                else:
                    pubDate = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
                
                img_elem = elem.find('img')
                image = None
                if img_elem and img_elem.get('src'):
                    src = img_elem['src']
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
    <language>en</language>
    <lastBuildDate>{now}</lastBuildDate>
    <atom:link href="{self.category_url}" rel="self" type="application/rss+xml"/>
'''
        
        for article in articles:
            xml += f'''    <item>
      <title><![CDATA[{article['title']}]]></title>
      <link>{article['link']}</link>
      <description><![CDATA[{article['description']}]]></description>
      <pubDate>{article['pubDate']}</pubDate>
      <guid isPermaLink="true">{article['link']}</guid>
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
            return False
        
        articles = self.parse_articles(html)
        if not articles:
            print("No articles found")
            return False
        
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
    success = generator.generate(args.output)
    sys.exit(0 if success else 1)
