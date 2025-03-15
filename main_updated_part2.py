def get_articles_from_website(site_url, num_articles=3):
    """Webサイトから直接記事を取得する"""
    try:
        logger.info(f"Webサイトから記事を取得しています: {site_url}")
        response = requests.get(site_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 記事リストを探す (サイト構造によって調整が必要)
        articles = []
        
        # 様々な記事コンテナの可能性を試す
        article_elements = soup.find_all('article') or soup.find_all('div', class_=lambda c: c and ('post' in c or 'article' in c))
        
        if not article_elements:
            # より一般的な方法で記事を探してみる
            article_elements = soup.find_all(['div', 'section'], class_=lambda c: c and ('post' in c or 'article' in c or 'entry' in c))
        
        logger.info(f"記事候補数: {len(article_elements)}")
        
        for article_elem in article_elements[:num_articles]:
            # タイトルを探す
            title_elem = article_elem.find(['h1', 'h2', 'h3', 'h4']) or article_elem.find(class_=lambda c: c and ('title' in c))
            
            # リンクを探す
            link_elem = None
            if title_elem and title_elem.find('a'):
                link_elem = title_elem.find('a')
            else:
                link_elem = article_elem.find('a', href=lambda h: h and not h.startswith('#'))
            
            # 日付を探す
            date_elem = article_elem.find(['time', 'span', 'div'], class_=lambda c: c and ('date' in c or 'time' in c or 'pub' in c))
            
            if title_elem and link_elem:
                title = title_elem.get_text().strip()
                link = link_elem.get('href')
                
                # 相対URLを絶対URLに変換
                if link and not link.startswith(('http://', 'https://')):
                    link = f"https://rocket-boys.co.jp{link}" if not link.startswith('/') else f"https://rocket-boys.co.jp{link}"
                
                date_str = date_elem.get_text().strip() if date_elem else "日付不明"
                
                articles.append({
                    "title": title,
                    "link": link,
                    "date": date_str
                })
        
        logger.info(f"取得した記事数: {len(articles)}")
        return articles
    
    except Exception as e:
        logger.error(f"記事取得エラー: {e}")
        return []

def extract_article_content(url):
    """記事の本文を抽出する"""
    try:
        logger.info(f"記事内容を取得しています: {url}")
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # ページから公開日を抽出してみる
        date_elem = soup.find(['time', 'span', 'div'], class_=lambda c: c and ('date' in c or 'time' in c or 'pub' in c))
        pub_date = date_elem.get_text().strip() if date_elem else None
        
        # 記事本文を探す方法を複数試す
        content = None
        
        # 方法1: entry-content クラス
        content_elem = soup.find('div', class_='entry-content')
        
        # 方法2: article タグ
        if not content_elem:
            content_elem = soup.find('article')
        
        # 方法3: コンテンツらしきdivを探す
        if not content_elem:
            content_elem = soup.find('div', class_=lambda c: c and ('content' in c or 'body' in c))
        
        # 方法4: メインコンテンツっぽい場所
        if not content_elem:
            main_elem = soup.find(['main', 'div'], id=lambda i: i and ('main' in i or 'content' in i))
            if main_elem:
                # main要素内の段落をすべて取得
                paragraphs = main_elem.find_all('p')
                if paragraphs:
                    content = "\n".join([p.get_text().strip() for p in paragraphs])
        
        if content_elem and not content:
            # 不要なタグを削除
            for tag in content_elem.find_all(['script', 'style', 'aside', 'nav', 'footer']):
                tag.decompose()
            
            content = content_elem.get_text().strip()
        
        if content:
            # テキストの正規化（余分な空白の削除など）
            content = re.sub(r'\s+', ' ', content).strip()
            logger.info(f"記事内容取得成功: {len(content)} 文字")
            return content, pub_date
        else:
            logger.warning(f"記事本文が見つかりませんでした: {url}")
            return None, None
    
    except Exception as e:
        logger.error(f"記事内容取得エラー: {url} - {e}")
        return None, None