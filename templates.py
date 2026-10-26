"""HTML 模板。所有页面结构在这里，样式在 assets/style.css。"""
import json
import re
from html import escape

from siteconf import NAV, SITE, SECTIONS


def abs_url(path):
    if path.startswith("http"):
        return path
    return SITE["url"].rstrip("/") + path


def _ld(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

# 标题换行：中文标题应该断在标点处，而不是任意字间。
# 「四禅比丘：修到第四禅，为什么……」被浏览器断成「…第四 / 禅，…」，
# 把「第四禅」这个术语劈开了。CSS 用 word-break: keep-all 只在标点处断行；
# 但超过一行宽的片段仍会被硬切，所以给它们人工找一个像样的断点。
#
# 断点不能取正中：14 字的「如果有一天你不用再为谋生奔忙」正中切开「不用」。
# 这里在正中附近搜索，优先把虚词完整地留在某一侧。
_TITLE_SEP = re.compile(r"([：，。、？！；·—…《》（）【】「」“”‘’\"'\s]+)")
_WORD_HEAD = "不没别很都也就要会能在是有和与而则才只还得过把被让给对从向于"
_WORD_TAIL = "的了着过和与而就都也又很最才只还"


def _cut_at(seg):
    """在一段无标点文字里挑一个断点，返回切开位置。"""
    n = len(seg)
    mid = n // 2
    best, best_score = mid, -99.0
    for i in range(max(1, mid - 3), min(n - 1, mid + 3) + 1):
        score = 0.0
        if seg[i] in _WORD_HEAD:            # 下一行以虚词开头，虚词不被拆
            score += 3
        if seg[i - 1] in _WORD_TAIL:        # 上一行以虚词收尾，读起来不断气
            score += 2
        if seg[i - 1] in _WORD_HEAD and seg[i] not in _WORD_HEAD:
            score -= 3                      # 拆开了「不用」这类词
        score -= abs(i - mid) * 0.6         # 越靠近正中越好，避免一行过长
        if score > best_score:
            best, best_score = i, score
    return best


def display_title(text, limit=13):
    """超过 limit 字的无标点片段插一个 <wbr>，给浏览器一个体面的断点。

    360px 屏一行约 13 字，430px 约 15 字；取 13 保证两种屏都不出孤字。
    """
    parts = []
    for seg in _TITLE_SEP.split(text):
        if not seg:
            continue
        if len(seg) <= limit or _TITLE_SEP.fullmatch(seg):
            parts.append(escape(seg))
        else:
            i = _cut_at(seg)
            parts.append(escape(seg[:i]) + "<wbr>" + escape(seg[i:]))
    return "".join(parts)


def head(title, desc, path, og_type="website", extra=""):
    url = abs_url(path)
    full = title if title == SITE["name"] else f"{title} · {SITE['name']}"
    return f"""<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(full)}</title>
<meta name="description" content="{escape(desc)}">
<link rel="canonical" href="{url}">
<meta name="theme-color" content="#EFEBE0" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#16140F" media="(prefers-color-scheme: dark)">
<link rel="stylesheet" href="/assets/style.css">
<link rel="icon" href="/assets/favicon.ico" sizes="any">
<link rel="icon" href="/assets/favicon-32.png" type="image/png" sizes="32x32">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<link rel="alternate" type="application/rss+xml" title="{escape(SITE['name'])}" href="/feed.xml">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{escape(SITE['name'])}">
<meta property="og:locale" content="{SITE['locale']}">
<meta property="og:title" content="{escape(title)}">
<meta property="og:description" content="{escape(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{abs_url('/assets/og.png')}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{escape(SITE['name'])}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{escape(title)}">
<meta name="twitter:description" content="{escape(desc)}">
<meta name="twitter:image" content="{abs_url('/assets/og.png')}">
{extra}""".rstrip()


def nav(active=""):
    items = []
    for href, label, key in NAV:
        cur = ' aria-current="page"' if key == active else ""
        items.append(f'<a href="{href}"{cur}>{label}</a>')
    items.append('<a href="/search/" class="nav-aux">搜</a>')
    return (
        '<header class="site-head"><div class="wrap">'
        f'<a class="brand" href="/">{escape(SITE["name"])}</a>'
        f'<nav class="nav">{"".join(items)}</nav>'
        "</div></header>"
    )


def footer():
    year = SITE["since"]
    return (
        '<footer class="site-foot"><div class="wrap">'
        f'<p class="foot-copy">© {year} {escape(SITE["name"])}　保留权利</p>'
        '<p class="foot-links">'
        '<a href="/about/">关于</a>'
        '<a href="/feed.xml">RSS 订阅</a>'
        '<a href="/search/">站内搜索</a>'
        "</p></div></footer>"
    )


def doc(head_html, body):
    return f"""<!doctype html>
<html lang="{SITE['lang']}">
<head>
{head_html}
</head>
<body>
{body}
</body>
</html>
"""


def entries(posts, with_excerpt=False):
    out = ['<ul class="entries">']
    for p in posts:
        ex = f'<span class="entry-excerpt">{escape(p.excerpt)}</span>' if with_excerpt else ""
        out.append(
            f'<li><a class="entry" href="{p.url}">'
            f'<time class="entry-date" datetime="{p.date}">{p.date}</time>'
            f'<span class="entry-body"><span class="entry-title">{escape(p.title)}</span>{ex}</span>'
            "</a></li>"
        )
    out.append("</ul>")
    return "".join(out)


def home(posts):
    shelves = []
    for key, meta in sorted(SECTIONS.items(), key=lambda kv: kv[1]["order"]):
        group = [p for p in posts if p.section == key]
        if not group:
            continue
        shelves.append(
            '<section class="shelf">'
            '<div class="shelf-head">'
            f'<span class="seal" aria-hidden="true">{meta["seal"]}</span>'
            f'<h2 class="shelf-title">{meta["name"]}</h2>'
            f'<a class="shelf-all" href="/{key}/">全部 {len(group)} 篇</a>'
            "</div>"
            f'<p class="shelf-note">{escape(meta["note"])}</p>'
            + entries(group[:4])
            + "</section>"
        )

    body = (
        nav("") +
        '<main class="wrap">'
        f'<section class="hero"><h1 class="lede">{escape(SITE["tagline"])}</h1>'
        f'<p class="hero-sub">{escape(SITE["description"])}</p></section>'
        + "".join(shelves) +
        '<section class="subscribe"><p>这里不打广告，不追热点，只在有话说的时候更新。'
        '想第一时间看到，用 <a href="/feed.xml">RSS</a> 订阅。</p></section>'
        "</main>" + footer()
    )
    ld = _ld({
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": SITE["name"],
        "url": SITE["url"],
        "description": SITE["description"],
        "inLanguage": SITE["lang"],
        "publisher": {"@type": "Person", "name": SITE["author"]},
    })
    h = head(SITE["name"], SITE["description"], "/",
             extra=f'<script type="application/ld+json">{ld}</script>\n')
    return doc(h, body)


def section_page(key, posts):
    meta = SECTIONS[key]
    body = (
        nav(key) +
        '<main class="wrap">'
        '<header class="section-head">'
        f'<span class="seal seal-lg" aria-hidden="true">{meta["seal"]}</span>'
        f'<h1 class="section-title">{meta["name"]}</h1>'
        f'<p class="section-note">{escape(meta["note"])}</p>'
        f'<p class="section-count">共 {len(posts)} 篇 · 按时间倒序</p>'
        "</header>"
        + entries(posts, with_excerpt=True) +
        "</main>" + footer()
    )
    h = head(meta["name"], meta["note"], f"/{key}/",
             extra="")
    return doc(h, body)


def article(post, newer, older):
    meta_bits = [f'<time datetime="{post.date}">{post.date}</time>',
                 f"<span>约 {post.minutes} 分钟</span>"]
    if post.source:
        meta_bits.append(f'<span class="src">出处：{escape(post.source)}</span>')

    colophon = ""
    if post.data_note:
        colophon = f'<div class="colophon"><span>发布数据：{escape(post.data_note)}</span></div>'

    pager = ['<nav class="pager" aria-label="同栏目翻页">']
    if newer:
        pager.append(
            f'<a class="pager-prev" href="{newer.url}"><span class="k">← 上一篇</span>'
            f'<span class="t">{escape(newer.title)}</span></a>')
    if older:
        pager.append(
            f'<a class="pager-next" href="{older.url}"><span class="k">下一篇 →</span>'
            f'<span class="t">{escape(older.title)}</span></a>')
    pager.append("</nav>")

    body = (
        nav(post.section) +
        '<main class="wrap">'
        '<nav class="crumb" aria-label="位置">'
        '<a href="/">首页</a><span class="sep">/</span>'
        f'<a href="/{post.section}/">{post.section_name}</a></nav>'
        '<article class="article">'
        f"<h1>{display_title(post.title)}</h1>"
        f'<div class="article-meta">{"".join(meta_bits)}</div>'
        f'<div class="prose">{post.html}</div>'
        f"{colophon}"
        "</article>"
        + "".join(pager) +
        f'<p class="back"><a href="/{post.section}/">← 回到「{post.section_name}」全部文章</a></p>'
        "</main>" + footer()
    )

    extra = (
        f'<meta property="article:published_time" content="{post.date}">\n'
        f'<meta property="article:section" content="{escape(post.section_name)}">\n'
        f'<script type="application/ld+json">{_ld(article_ld(post))}</script>\n'
        f'<script type="application/ld+json">{_ld(breadcrumb_ld(post))}</script>\n'
    )
    h = head(post.title, post.description, post.url, og_type="article", extra=extra)
    return doc(h, body)


def article_ld(post):
    return {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": post.title,
        "description": post.description,
        "datePublished": post.date,
        "dateModified": post.date,
        "inLanguage": SITE["lang"],
        "articleSection": post.section_name,
        "mainEntityOfPage": {"@type": "WebPage", "@id": abs_url(post.url)},
        "author": {"@type": "Person", "name": SITE["author"]},
        "publisher": {"@type": "Person", "name": SITE["author"]},
    }


def breadcrumb_ld(post):
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": SITE["name"],
             "item": SITE["url"]},
            {"@type": "ListItem", "position": 2, "name": post.section_name,
             "item": abs_url(f"/{post.section}/")},
            {"@type": "ListItem", "position": 3, "name": post.title,
             "item": abs_url(post.url)},
        ],
    }


def page(title, desc, path, html, active=""):
    body = (nav(active) +
            '<main class="wrap">'
            f'<article class="article"><h1>{escape(title)}</h1>'
            f'<div class="prose">{html}</div></article>'
            "</main>" + footer())
    return doc(head(title, desc, path, og_type="article"), body)


def search_page():
    body = (
        nav("") +
        '<main class="wrap">'
        '<header class="section-head"><h1 class="section-title">站内搜索</h1></header>'
        '<form class="search-form" role="search" action="/search/" method="get">'
        '<label class="sr-only" for="q">关键词</label>'
        '<input id="q" name="q" type="search" placeholder="输入关键词，多个词用空格分开…" '
        'autocomplete="off" autofocus>'
        "</form>"
        '<p class="search-status" id="status" aria-live="polite"></p>'
        '<ul class="entries search-results" id="results"></ul>'
        '<noscript><p class="section-note">需要开启 JavaScript 才能搜索。'
        '也可以直接看 <a href="/deep/">深度</a>、<a href="/stories/">佛典故事</a>'
        '的完整目录。</p></noscript>'
        "</main>" + footer()
    )
    extra = '<script src="/assets/search.js" defer></script>\n'
    h = head("站内搜索", f"在{SITE['name']}的全部文章中搜索关键词。", "/search/", extra=extra)
    return doc(h, body)


def notfound():
    body = (
        nav("") +
        '<main class="wrap">'
        '<header class="section-head"><span class="seal seal-lg">无</span>'
        '<h1 class="section-title">404</h1>'
        '<p class="section-note">这个地址没有对应的页面。可能是链接打错了，'
        '也可能是文章改过名。</p></header>'
        '<p class="section-count"><a href="/">回首页</a>　·　'
        '<a href="/search/">搜一下</a></p>'
        "</main>" + footer()
    )
    return doc(head("页面不存在", "没有找到这个页面。", "/404.html"), body)


def redirect(target, label):
    return f"""<!doctype html>
<html lang="{SITE['lang']}">
<head>
<meta charset="utf-8">
<title>跳转至 {escape(label)} · {escape(SITE['name'])}</title>
<meta name="robots" content="noindex, follow">
<link rel="canonical" href="{abs_url(target)}">
<meta http-equiv="refresh" content="0; url={target}">
</head>
<body>
<p>正在跳转到 <a href="{target}">{escape(label)}</a>。</p>
<script>location.replace("{target}" + location.hash);</script>
</body>
</html>
"""
