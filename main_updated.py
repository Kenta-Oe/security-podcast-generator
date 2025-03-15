import asyncio
import feedparser
import requests
from bs4 import BeautifulSoup
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import logging
import re
import subprocess
import shutil

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("podcast_generator.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 定数
SITE_URL = "https://rocket-boys.co.jp/security-measures-lab/"
RSS_URL = "https://rocket-boys.co.jp/feed/"
BASE_DIR = Path(__file__).parent.resolve()
SCRIPTS_DIR = BASE_DIR / "scripts"
OUTPUT_DIR = BASE_DIR / "output"
SUMMARY_DIR = OUTPUT_DIR / "要約"
TEMP_DIR = BASE_DIR / "temp"

# BGMファイルのパス
BGM_FILE = r"C:\Users\takky\OneDrive\デスクトップ\code_work\code_woek\test-podcast\bgm\296_long_BPM85.mp3"

# OpenAI プロンプト
PODCAST_PROMPT = """あなたはプロのPodcastの話し手です。 上記の文章と各URLを検索して4000文字程度のPodcast用の台本を作成してください。 
・出力は普通の丁寧語で口語のみとし、目次やタイトルは除外する（一連の文章だけの出力とする） 
・最大限のリソースを使用してハルシネーションを防止すること 
・出力はすべてソースのあるものから行い、あいまいな情報は使用しない 
・上記の条件を何があっても必ず逸脱しないこと 
・出力は下記のフォーマットとすること、出力にリンクと記事のタイトルは表示させないが、企業名は表示させること 
・出力内容を検証し、同じ名用を言っていないか検証すること。同じであれば独自に検索して内容を付け足して、同じ言い回しや内容はできるだけ使いまわさず、実のある内容にして 
・出力内容は一度精査し、内容にうそや矛盾がないことを検証すること"""

# 固定のあいさつ
OPENING_GREETING = "こんにちは、皆さん。ようこそ、私はホストの大江です。"
CLOSING_MESSAGE = "今後もこうしたニュースの背景や影響について、皆さんと一緒に考えていきたいと思います。もしこのエピソードについてご意見や質問がありましたら、ぜひお寄せください。また、ポッドキャストを楽しんでいただけたなら、評価やレビューもお願いします。それでは、次回もお楽しみに。ありがとうございました。"

def get_yesterday_date():
    """昨日の日付を取得する"""
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime('%Y-%m-%d')

def fetch_rss_feed(url):
    """RSSフィードを取得する"""
    try:
        feed = feedparser.parse(url)
        logger.info(f"RSS取得成功: {len(feed.entries)}件のエントリを検出")
        return feed
    except Exception as e:
        logger.error(f"RSSフィード取得エラー: {e}")
        return None
