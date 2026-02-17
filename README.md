# 📰 AI News Daily

每日自动从 [Karpathy 推荐的 HN 热门博客 RSS 源](https://gist.github.com/emschwartz/e6d2bf860ccc367fe37ff953ba6de66b) 抓取最新文章，筛选 AI 相关内容，选出最热门的 20 篇，并使用 LLM 生成中文摘要。

灵感来自 Andrej Karpathy 在 2026 年 2 月呼吁大家 "Bring back RSS" 的倡议。

## ✨ 功能

- 🔄 从 95+ 个高质量博客 RSS 源抓取最新文章
- 🤖 使用 AI 筛选与人工智能相关的内容
- 📊 按相关性和新鲜度排序，选出 Top 20
- 📝 使用 LLM（OpenAI API）生成中文摘要
- 📅 通过 GitHub Actions 每日自动运行
- 📄 结果输出为 Markdown 文件，存放在 `output/` 目录

## 🚀 快速开始

### 本地运行

```bash
# 克隆项目
git clone https://github.com/YOUR_USERNAME/ai-news-daily.git
cd ai-news-daily

# 安装依赖
pip install -r requirements.txt

# 设置 OpenAI API Key
export OPENAI_API_KEY="your-api-key-here"

# 运行
python main.py
```

### GitHub Actions 自动运行

1. Fork 本项目
2. 在 Settings → Secrets → Actions 中添加 `OPENAI_API_KEY`
3. GitHub Actions 会在每天 UTC 01:00（北京时间 09:00）自动运行
4. 结果会自动提交到 `output/` 目录

## 📁 项目结构

```
ai-news-daily/
├── main.py              # 主程序入口
├── feeds.opml           # RSS 源列表（OPML 格式）
├── config.py            # 配置文件
├── rss_fetcher.py       # RSS 抓取模块
├── ai_ranker.py         # AI 内容筛选 & 排序
├── summarizer.py        # LLM 摘要生成
├── requirements.txt     # Python 依赖
├── .github/
│   └── workflows/
│       └── daily.yml    # GitHub Actions 定时任务
└── output/              # 每日输出目录
    └── 2026-02-17.md    # 示例输出
```

## ⚙️ 配置

编辑 `config.py` 自定义行为：

```python
TOP_N = 20                    # 选取文章数量
LOOKBACK_HOURS = 24           # 回顾时间窗口（小时）
OPENAI_MODEL = "gpt-4o-mini"  # 使用的模型
LANGUAGE = "zh-CN"            # 摘要语言
```

## 📜 License

MIT
