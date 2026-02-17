"""主程序：抓取 → 筛选 → 输出（摘要由 Agent 外部生成）"""
import asyncio
import os
import sys
import json
from datetime import datetime, timezone, timedelta

from rss_fetcher import fetch_all_feeds
from ai_ranker import rank_articles
from summarizer import summarize_articles_fallback, build_summary_prompt, parse_agent_summaries
import config


def generate_markdown(articles, date_str: str) -> str:
    """生成 Markdown 格式的每日报告"""
    lines = [
        f"# 📰 AI 新闻日报 - {date_str}",
        "",
        f"> 自动生成于 {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"> 数据源: [Karpathy 推荐的 HN 热门博客 RSS](https://gist.github.com/emschwartz/e6d2bf860ccc367fe37ff953ba6de66b)",
        "",
        "---",
        "",
    ]

    for i, article in enumerate(articles, 1):
        pub_time = article.published.strftime("%Y-%m-%d %H:%M UTC")
        score_emoji = "🔥" if article.ai_score >= 50 else "⭐" if article.ai_score >= 20 else "📌"

        lines.extend([
            f"## {score_emoji} {i}. {article.title}",
            "",
            f"**来源:** [{article.source}]({article.link}) | **发布:** {pub_time} | **AI相关度:** {article.ai_score:.0f}",
            "",
            f"{article.ai_summary}",
            "",
            f"🔗 [阅读原文]({article.link})",
            "",
            "---",
            "",
        ])

    lines.extend([
        "",
        "## 📊 统计",
        "",
        f"- 扫描 RSS 源数量: 95+",
        f"- 筛选文章数量: {len(articles)}",
        f"- 时间范围: 最近 {config.LOOKBACK_HOURS} 小时",
        "",
        "---",
        "",
        "*由 [ai-news-daily](https://github.com/shichangs/ai-news-daily) 自动生成*",
    ])

    return "\n".join(lines)


async def run_fetch_and_rank():
    """步骤 1+2: 抓取 + 筛选，输出中间结果"""
    articles = await fetch_all_feeds()
    if not articles:
        print("❌ 没有抓到任何文章")
        return []

    top_articles = rank_articles(articles)
    return top_articles


def save_intermediate(articles, filepath):
    """保存中间结果为 JSON"""
    data = []
    for a in articles:
        data.append({
            "title": a.title,
            "link": a.link,
            "source": a.source,
            "published": a.published.isoformat(),
            "summary": a.summary,
            "content": a.content[:800],
            "ai_score": a.ai_score,
            "tags": a.tags,
        })
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_intermediate(filepath):
    """从 JSON 加载中间结果"""
    from rss_fetcher import Article
    from datetime import datetime
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    articles = []
    for d in data:
        a = Article(
            title=d["title"],
            link=d["link"],
            source=d["source"],
            published=datetime.fromisoformat(d["published"]),
            summary=d.get("summary", ""),
            content=d.get("content", ""),
            ai_score=d.get("ai_score", 0),
            tags=d.get("tags", []),
        )
        articles.append(a)
    return articles


def generate_report(articles, summaries_text=None):
    """步骤 3: 生成最终报告"""
    if summaries_text:
        articles = parse_agent_summaries(summaries_text, articles)
    else:
        articles = summarize_articles_fallback(articles)

    beijing_tz = timezone(timedelta(hours=8))
    date_str = datetime.now(beijing_tz).strftime("%Y-%m-%d")

    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(config.OUTPUT_DIR, f"{date_str}.md")

    md_content = generate_markdown(articles, date_str)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    return output_path, md_content


async def main():
    """完整流程：抓取 → 筛选 → 保存中间结果 → 生成报告"""
    print("=" * 60)
    print("📰 AI News Daily - 开始运行")
    print("=" * 60)

    # 1+2. 抓取 + 筛选
    top_articles = await run_fetch_and_rank()
    if not top_articles:
        return

    # 保存中间结果（供 Agent 读取生成摘要）
    intermediate_path = os.path.join(config.OUTPUT_DIR, "latest_articles.json")
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    save_intermediate(top_articles, intermediate_path)

    # 生成摘要 prompt
    prompt = build_summary_prompt(top_articles)
    prompt_path = os.path.join(config.OUTPUT_DIR, "summary_prompt.txt")
    with open(prompt_path, "w", encoding="utf-8") as f:
        f.write(prompt)

    print(f"\n📋 已保存 {len(top_articles)} 篇文章到 {intermediate_path}")
    print(f"📝 摘要 prompt 已保存到 {prompt_path}")

    # 如果通过命令行传入了摘要文本，直接生成报告
    if len(sys.argv) > 1 and sys.argv[1] == "--with-summaries":
        summaries_file = sys.argv[2] if len(sys.argv) > 2 else os.path.join(config.OUTPUT_DIR, "summaries.txt")
        if os.path.exists(summaries_file):
            with open(summaries_file, "r", encoding="utf-8") as f:
                summaries_text = f.read()
            output_path, _ = generate_report(top_articles, summaries_text)
            print(f"\n📄 报告已生成: {output_path}")
    else:
        # 无摘要模式：用 fallback
        output_path, _ = generate_report(top_articles)
        print(f"\n📄 报告已生成（无AI摘要）: {output_path}")

    print("=" * 60)
    print("✅ 完成！")

    # 预览 Top 5
    print("\n📋 Top 5 预览:")
    for i, a in enumerate(top_articles[:5], 1):
        print(f"  {i}. [{a.ai_score:.0f}] {a.title}")
        print(f"     {a.source} | {a.published.strftime('%m-%d %H:%M')}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
