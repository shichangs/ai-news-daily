"""LLM 摘要生成模块"""
import json
import re
import html
from openai import OpenAI

from rss_fetcher import Article
import config


def _clean_html(text: str) -> str:
    """去除 HTML 标签"""
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _build_article_text(article: Article) -> str:
    """构建用于 LLM 的文章文本"""
    content = _clean_html(article.content or article.summary)
    return f"标题: {article.title}\n来源: {article.source}\n链接: {article.link}\n内容: {content[:1500]}"


def summarize_articles(articles: list[Article]) -> list[Article]:
    """使用 LLM 为文章列表生成中文摘要"""
    if not config.OPENAI_API_KEY:
        print("⚠️  未设置 OPENAI_API_KEY，跳过 AI 摘要，使用原始摘要")
        for article in articles:
            article.ai_summary = _clean_html(article.summary)[:200] if article.summary else "暂无摘要"
        return articles

    client = OpenAI(
        api_key=config.OPENAI_API_KEY,
        base_url=config.OPENAI_BASE_URL,
    )

    print(f"🤖 正在使用 {config.OPENAI_MODEL} 生成中文摘要...")

    # 分批处理，每批 5 篇
    batch_size = 5
    for i in range(0, len(articles), batch_size):
        batch = articles[i:i + batch_size]
        batch_text = "\n\n---\n\n".join(
            f"[文章 {j+1}]\n{_build_article_text(a)}"
            for j, a in enumerate(batch)
        )

        try:
            response = client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是一个专业的科技新闻编辑。请为以下每篇文章写一段简洁的中文摘要（2-3句话），"
                            "突出核心要点和技术亮点。\n\n"
                            "请以 JSON 数组格式返回，每个元素包含 index（从1开始）和 summary 字段。\n"
                            "示例: [{\"index\": 1, \"summary\": \"摘要内容\"}, ...]"
                        )
                    },
                    {
                        "role": "user",
                        "content": batch_text,
                    }
                ],
                temperature=0.3,
                max_tokens=2000,
            )

            result_text = response.choices[0].message.content.strip()

            # 提取 JSON
            json_match = re.search(r'\[.*\]', result_text, re.DOTALL)
            if json_match:
                summaries = json.loads(json_match.group())
                for item in summaries:
                    idx = item.get("index", 0) - 1
                    if 0 <= idx < len(batch):
                        batch[idx].ai_summary = item.get("summary", "")
            else:
                # fallback: 用整段作为第一篇的摘要
                for a in batch:
                    if not a.ai_summary:
                        a.ai_summary = _clean_html(a.summary)[:200] or "暂无摘要"

        except Exception as e:
            print(f"⚠️  LLM 调用失败: {e}")
            for a in batch:
                if not a.ai_summary:
                    a.ai_summary = _clean_html(a.summary)[:200] or "暂无摘要"

        print(f"  ✅ 已处理 {min(i + batch_size, len(articles))}/{len(articles)} 篇")

    # 确保所有文章都有摘要
    for a in articles:
        if not a.ai_summary:
            a.ai_summary = _clean_html(a.summary)[:200] or "暂无摘要"

    return articles
