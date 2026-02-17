"""LLM 摘要生成模块 - Agent 模式（由狗蛋直接生成摘要）"""
import json
import re
import html
import os

from rss_fetcher import Article
import config


def _clean_html(text: str) -> str:
    """去除 HTML 标签"""
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def summarize_articles_fallback(articles: list[Article]) -> list[Article]:
    """无 LLM 时的 fallback 摘要：清洗原始摘要"""
    for article in articles:
        cleaned = _clean_html(article.summary or article.content)
        article.ai_summary = cleaned[:300] if cleaned else "暂无摘要"
    return articles


def build_summary_prompt(articles: list[Article]) -> str:
    """构建给 Agent 的摘要 prompt，返回纯文本"""
    lines = []
    for i, a in enumerate(articles, 1):
        content = _clean_html(a.content or a.summary)[:800]
        lines.append(f"[{i}] 标题: {a.title}\n来源: {a.source}\n链接: {a.link}\n内容: {content}\n")
    return "\n---\n".join(lines)


def parse_agent_summaries(text: str, articles: list[Article]) -> list[Article]:
    """解析 Agent 返回的摘要文本，填充到 articles"""
    # 尝试按编号解析: "1. xxx" 或 "[1] xxx"
    pattern = r'(?:^|\n)\s*(?:\[?\d+\]?[\.\):\s]+)(.+?)(?=\n\s*(?:\[?\d+\]?[\.\):\s]+)|\Z)'
    matches = re.findall(pattern, text, re.DOTALL)

    if matches and len(matches) >= len(articles):
        for i, article in enumerate(articles):
            article.ai_summary = matches[i].strip()
    else:
        # fallback: 整体按段落分割
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        for i, article in enumerate(articles):
            if i < len(paragraphs):
                article.ai_summary = paragraphs[i].strip()
            else:
                article.ai_summary = _clean_html(article.summary)[:300] or "暂无摘要"

    # 确保每篇都有摘要
    for a in articles:
        if not a.ai_summary:
            a.ai_summary = _clean_html(a.summary)[:300] or "暂无摘要"

    return articles
