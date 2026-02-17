"""主程序：抓取 → 筛选 → 摘要 → 输出"""
import asyncio
import os
from datetime import datetime, timezone, timedelta

from rss_fetcher import fetch_all_feeds
from ai_ranker import rank_articles
from summarizer import summarize_articles
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
        # 格式化发布时间
        pub_time = article.published.strftime("%Y-%m-%d %H:%M UTC")
        # 相关性标签
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
        "*由 [ai-news-daily](https://github.com/) 自动生成*",
    ])

    return "\n".join(lines)


async def main():
    print("=" * 60)
    print("📰 AI News Daily - 开始运行")
    print("=" * 60)

    # 1. 抓取 RSS
    articles = await fetch_all_feeds()
    if not articles:
        print("❌ 没有抓到任何文章，退出")
        return

    # 2. AI 筛选 & 排序
    top_articles = rank_articles(articles)

    # 3. LLM 摘要
    top_articles = summarize_articles(top_articles)

    # 4. 生成输出
    # 使用北京时间作为日期
    beijing_tz = timezone(timedelta(hours=8))
    date_str = datetime.now(beijing_tz).strftime("%Y-%m-%d")

    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(config.OUTPUT_DIR, f"{date_str}.md")

    md_content = generate_markdown(top_articles, date_str)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"\n📄 报告已生成: {output_path}")
    print("=" * 60)
    print("✅ 完成！")
    print("=" * 60)

    # 打印预览
    print("\n📋 Top 5 预览:")
    for i, a in enumerate(top_articles[:5], 1):
        print(f"  {i}. [{a.ai_score:.0f}] {a.title}")
        print(f"     {a.source} | {a.published.strftime('%m-%d %H:%M')}")
        if a.ai_summary:
            print(f"     {a.ai_summary[:80]}...")
        print()


if __name__ == "__main__":
    asyncio.run(main())
