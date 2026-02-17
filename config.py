"""配置文件"""
import os

# RSS 抓取配置
OPML_FILE = os.path.join(os.path.dirname(__file__), "feeds.opml")
LOOKBACK_HOURS = 24          # 回顾最近多少小时的文章
FETCH_TIMEOUT = 15           # 单个 feed 的请求超时（秒）
MAX_CONCURRENT = 20          # 并发抓取数量

# AI 筛选 & 排序
TOP_N = 20                   # 最终选取的文章数量
AI_KEYWORDS = [
    "ai", "artificial intelligence", "machine learning", "deep learning",
    "llm", "large language model", "gpt", "transformer", "neural network",
    "diffusion", "generative", "chatgpt", "openai", "anthropic", "claude",
    "gemini", "mistral", "llama", "stable diffusion", "midjourney",
    "reinforcement learning", "rl", "rlhf", "fine-tuning", "finetuning",
    "rag", "retrieval augmented", "embedding", "vector database",
    "prompt engineering", "agent", "agentic", "multimodal",
    "computer vision", "nlp", "natural language", "speech recognition",
    "robotics", "autonomous", "self-driving", "tesla fsd",
    "gpu", "cuda", "tpu", "inference", "training",
    "hugging face", "pytorch", "tensorflow", "jax",
    "alignment", "safety", "interpretability", "explainability",
    "scaling law", "emergent", "reasoning", "chain of thought",
    "coding assistant", "copilot", "cursor", "vibe coding",
]

# LLM 摘要配置
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
LANGUAGE = "zh-CN"           # 摘要语言

# 输出配置 - 数据存本地，不放 GitHub
DATA_DIR = os.path.expanduser("~/.openclaw/workspace/ai-news-daily-data")
OUTPUT_DIR = os.path.join(DATA_DIR, "daily")
