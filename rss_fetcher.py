"""RSS 抓取模块：解析 OPML、并发抓取 RSS feeds"""
import asyncio
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional

import aiohttp
import feedparser

import config


@dataclass
class Article:
    """一篇文章"""
    title: str
    link: str
    source: str              # 来源博客名
    published: datetime       # 发布时间 (UTC)
    summary: str = ""         # 原始摘要 / 描述
    content: str = ""         # 正文片段（用于 AI 分析）
    ai_score: float = 0.0     # AI 相关性评分
    ai_summary: str = ""      # LLM 生成的中文摘要
    tags: list[str] = field(default_factory=list)

    def __hash__(self):
        return hash(self.link)

    def __eq__(self, other):
        return isinstance(other, Article) and self.link == other.link


def parse_opml(filepath: str) -> list[dict]:
    """解析 OPML 文件，返回 [{text, xmlUrl, htmlUrl}, ...]"""
    tree = ET.parse(filepath)
    root = tree.getroot()
    feeds = []
    for outline in root.iter("outline"):
        xml_url = outline.get("xmlUrl")
        if xml_url:
            feeds.append({
                "text": outline.get("text", ""),
                "xmlUrl": xml_url,
                "htmlUrl": outline.get("htmlUrl", ""),
            })
    return feeds


def _parse_datetime(entry) -> Optional[datetime]:
    """从 feedparser entry 中提取发布时间"""
    for attr in ("published_parsed", "updated_parsed"):
        tp = getattr(entry, attr, None)
        if tp:
            try:
                from time import mktime
                dt = datetime.fromtimestamp(mktime(tp), tz=timezone.utc)
                return dt
            except Exception:
                continue
    return None


async def _fetch_one(session: aiohttp.ClientSession, feed: dict, cutoff: datetime) -> list[Article]:
    """抓取单个 RSS feed"""
    articles = []
    try:
        async with session.get(feed["xmlUrl"], timeout=aiohttp.ClientTimeout(total=config.FETCH_TIMEOUT)) as resp:
            if resp.status != 200:
                return []
            text = await resp.text()
    except Exception:
        return []

    parsed = feedparser.parse(text)
    for entry in parsed.entries:
        pub_date = _parse_datetime(entry)
        if not pub_date:
            # 没有时间信息的文章，假设是近期的
            pub_date = datetime.now(timezone.utc)

        if pub_date < cutoff:
            continue

        # 提取内容
        content = ""
        if hasattr(entry, "content") and entry.content:
            content = entry.content[0].get("value", "")
        summary = getattr(entry, "summary", "") or ""

        # 截取前 2000 字符用于 AI 分析
        text_for_ai = (content or summary)[:2000]

        articles.append(Article(
            title=getattr(entry, "title", "Untitled"),
            link=getattr(entry, "link", ""),
            source=feed["text"],
            published=pub_date,
            summary=summary[:500],
            content=text_for_ai,
            tags=[t.get("term", "") for t in getattr(entry, "tags", [])],
        ))

    return articles


async def fetch_all_feeds() -> list[Article]:
    """并发抓取所有 RSS feeds，返回最近文章列表"""
    feeds = parse_opml(config.OPML_FILE)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=config.LOOKBACK_HOURS)

    print(f"📡 开始抓取 {len(feeds)} 个 RSS 源（回顾 {config.LOOKBACK_HOURS} 小时）...")

    sem = asyncio.Semaphore(config.MAX_CONCURRENT)
    all_articles: list[Article] = []

    async def _limited_fetch(feed):
        async with sem:
            return await _fetch_one(session, feed, cutoff)

    connector = aiohttp.TCPConnector(limit=config.MAX_CONCURRENT, ssl=False)
    async with aiohttp.ClientSession(connector=connector, headers={
        "User-Agent": "AI-News-Daily/1.0 (RSS Reader; +https://github.com/ai-news-daily)"
    }) as session:
        tasks = [_limited_fetch(f) for f in feeds]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    success_count = 0
    for result in results:
        if isinstance(result, list):
            all_articles.extend(result)
            if result:
                success_count += 1

    # 去重
    seen = set()
    unique = []
    for a in all_articles:
        if a.link not in seen:
            seen.add(a.link)
            unique.append(a)

    print(f"✅ 成功抓取 {success_count}/{len(feeds)} 个源，共 {len(unique)} 篇文章")
    return unique
