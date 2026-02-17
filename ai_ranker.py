"""AI 内容筛选 & 排序：使用关键词 + LLM 评分"""
import re
import html
from datetime import datetime, timezone

from rss_fetcher import Article
import config


def _clean_html(text: str) -> str:
    """去除 HTML 标签"""
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _keyword_score(article: Article) -> float:
    """基于关键词匹配计算 AI 相关性分数（0-100）"""
    text = f"{article.title} {article.summary} {article.content}".lower()
    text = _clean_html(text)

    score = 0.0
    matched_keywords = set()

    for kw in config.AI_KEYWORDS:
        kw_lower = kw.lower()
        # 标题中匹配权重更高
        if kw_lower in article.title.lower():
            score += 10
            matched_keywords.add(kw)
        # 正文/摘要匹配
        count = text.count(kw_lower)
        if count > 0:
            score += min(count * 2, 10)  # 单个关键词最多 10 分
            matched_keywords.add(kw)

    # 关键词多样性加分
    score += len(matched_keywords) * 3

    # 时间新鲜度加分（越新越好）
    hours_ago = (datetime.now(timezone.utc) - article.published).total_seconds() / 3600
    freshness_bonus = max(0, 20 - hours_ago)  # 最近的文章加分更多
    score += freshness_bonus

    return min(score, 100)


def rank_articles(articles: list[Article], top_n: int = None) -> list[Article]:
    """对文章进行 AI 相关性评分和排序"""
    if top_n is None:
        top_n = config.TOP_N

    print(f"🔍 正在对 {len(articles)} 篇文章进行 AI 相关性评分...")

    # 计算每篇文章的 AI 相关性分数
    for article in articles:
        article.ai_score = _keyword_score(article)

    # 过滤掉完全不相关的（分数 < 5）
    relevant = [a for a in articles if a.ai_score >= 5]

    # 按分数降序排列
    relevant.sort(key=lambda a: a.ai_score, reverse=True)

    # 如果相关文章不足 top_n，用时间最新的补充
    if len(relevant) < top_n:
        remaining = [a for a in articles if a not in set(relevant)]
        remaining.sort(key=lambda a: a.published, reverse=True)
        relevant.extend(remaining[:top_n - len(relevant)])

    top = relevant[:top_n]
    print(f"📊 筛选出 {len(top)} 篇 AI 相关文章（相关文章总数: {len([a for a in articles if a.ai_score >= 5])}）")

    return top
