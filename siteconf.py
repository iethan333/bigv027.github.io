"""站点配置。改站点信息、栏目、导航，只改这里，不碰模板。"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
POSTS_DIR = ROOT / "_posts"
PAGES_DIR = ROOT / "_pages"
ASSETS_DIR = ROOT / "assets"
OUT_DIR = ROOT / "site"

SITE = {
    "name": "学习成长再生",
    "tagline": "佛法的老话，照今天的难处。",
    "description": "把现代人的焦虑、职场、家庭，接到佛法里说清楚。",
    "url": "https://iethan333.github.io",
    "author": "乐钧",
    "lang": "zh-Hans",
    "locale": "zh_CN",
    "since": 2026,
}

# order 决定首页与导航顺序
SECTIONS = {
    "deep": {
        "name": "深度", "seal": "深", "order": 1,
        "note": "把现代人的焦虑、职场、家庭，接到佛法里说清楚。",
    },
    "stories": {
        "name": "佛典故事", "seal": "典", "order": 2,
        "note": "一句经、一个故事，看因果如何运转。",
    },
    "notes": {
        "name": "随笔", "seal": "随", "order": 3,
        "note": "更早的笔记与实验：读书、方法、工具。",
    },
}

# 旧分类 → 栏目 key
CATEGORY_MAP = {
    "深度": "deep",
    "佛典故事": "stories",
    "edu": "notes",
    "工作": "notes",
    "学习": "notes",
    "sys": "notes",
    "blog": "notes",
    "": "notes",
}

NAV = [
    ("/deep/", "深度", "deep"),
    ("/stories/", "佛典故事", "stories"),
    ("/notes/", "随笔", "notes"),
    ("/about/", "关于", "about"),
]

READING_SPEED = 400      # 中文字/分钟，取保守值
HOME_PER_SECTION = 4     # 首页每栏显示篇数
RSS_LIMIT = 20
