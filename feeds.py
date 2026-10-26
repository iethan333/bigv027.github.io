"""订阅与爬虫入口：RSS、sitemap、robots、站内搜索索引。"""
import json
from datetime import date, datetime, timezone
from html import escape

from siteconf import RSS_LIMIT, SITE, SECTIONS
from templates import abs_url


def _rfc822(d):
    dt = datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")


def rss(posts):
    items = []
    for p in posts[:RSS_LIMIT]:
        items.append(
            "    <item>\n"
            f"      <title>{escape(p.title)}</title>\n"
            f"      <link>{abs_url(p.url)}</link>\n"
            f'      <guid isPermaLink="true">{abs_url(p.url)}</guid>\n'
            f"      <pubDate>{_rfc822(p.date)}</pubDate>\n"
            f"      <category>{escape(p.section_name)}</category>\n"
            f"      <description>{escape(p.excerpt or p.description)}</description>\n"
            "    </item>"
        )
    last = _rfc822(posts[0].date) if posts else _rfc822("2026-01-01")
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
        "  <channel>\n"
        f"    <title>{escape(SITE['name'])}</title>\n"
        f"    <link>{SITE['url']}</link>\n"
        f"    <description>{escape(SITE['description'])}</description>\n"
        f"    <language>{SITE['lang']}</language>\n"
        f"    <lastBuildDate>{last}</lastBuildDate>\n"
        f'    <atom:link href="{abs_url("/feed.xml")}" rel="self" type="application/rss+xml"/>\n'
        + "\n".join(items) + "\n"
        "  </channel>\n"
        "</rss>\n"
    )


def sitemap(posts, extra_paths):
    lines = []
    for p in posts:
        lines.append(
            f'  <url><loc>{abs_url(p.url)}</loc>'
            f"<lastmod>{p.date}</lastmod>"
            f"<changefreq>monthly</changefreq><priority>0.8</priority></url>"
        )
    for path, prio in extra_paths:
        lines.append(
            f'  <url><loc>{abs_url(path)}</loc>'
            f"<changefreq>weekly</changefreq><priority>{prio}</priority></url>"
        )
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(lines) + "\n</urlset>\n"
    )


def robots():
    return (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /_posts/\n"
        "Disallow: /_pages/\n"
        f"Sitemap: {abs_url('/sitemap.xml')}\n"
    )


def search_index(posts):
    """短键压缩体积：t=标题 u=地址 s=栏目 d=日期 x=摘要 c=正文字数"""
    data = [
        {"t": p.title, "u": p.url, "s": p.section_name,
         "d": p.date, "x": p.excerpt}
        for p in posts
    ]
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def webmanifest():
    """主屏图标。安卓「添加到主屏幕」时读这个。"""
    return json.dumps({
        "name": SITE["name"],
        "short_name": "学习成长",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#EFEBE0",
        "theme_color": "#EFEBE0",
        "icons": [
            {"src": "/assets/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/assets/icon-512.png", "sizes": "512x512", "type": "image/png"},
        ],
    }, ensure_ascii=False, indent=2)


def manifest(site_files):
    return json.dumps({"generated": date.today().isoformat(),
                       "files": sorted(site_files)},
                      ensure_ascii=False, separators=(",", ":"))
