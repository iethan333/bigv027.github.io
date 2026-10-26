#!/usr/bin/env python3
"""构建静态站：_posts/*.md → site/

用法：
    python3 build.py            构建
    python3 build.py --serve    构建后本地预览 http://127.0.0.1:8000
"""
import shutil
import sys
import time
from pathlib import Path

import feeds
import templates
from content import ContentError, by_section, load_posts, neighbours, parse_front_matter
from render import md_batch_to_html, md_to_html, pandoc_ready
from siteconf import ASSETS_DIR, OUT_DIR, PAGES_DIR, SITE, SECTIONS

GENERATED = []


def write(rel, text):
    p = OUT_DIR / rel.lstrip("/")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    GENERATED.append(str(p.relative_to(OUT_DIR)))


def about_html():
    src = PAGES_DIR / "about.md"
    if src.is_file():
        fm, body = parse_front_matter(src.read_text(encoding="utf-8"))
        title = str(fm.get("title") or "关于")
        return title, md_to_html(body, src.name)
    return "关于", f"<p>{SITE['description']}</p>"


def build():
    t0 = time.time()
    if not pandoc_ready():
        raise SystemExit("✗ 需要 pandoc：sudo pacman -S pandoc")

    posts = load_posts()

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)

    # 文章页
    htmls = md_batch_to_html([(p.body_md, p.path.name) for p in posts])
    for p, html in zip(posts, htmls):
        p.html = html
        newer, older = neighbours(posts, p)
        write(p.url, templates.article(p, newer, older))

    # 栏目页
    for key in SECTIONS:
        write(f"/{key}/index.html",
              templates.section_page(key, by_section(posts, key)))

    # 首页 / 关于 / 搜索 / 404
    write("/index.html", templates.home(posts))
    about_title, about_body = about_html()
    write("/about/index.html",
          templates.page(about_title, SITE["description"], "/about/", about_body, active="about"))
    write("/search/index.html", templates.search_page())
    write("/404.html", templates.notfound())

    # 旧链接跳转
    taken = {p.url for p in posts} | {"/index.html", "/404.html"}
    for p in posts:
        for alias in p.aliases:
            if alias in taken:
                continue
            taken.add(alias)
            write(alias, templates.redirect(p.url, p.title))

    # 订阅与爬虫
    write("/feed.xml", feeds.rss(posts))
    write("/robots.txt", feeds.robots())
    extra = [("/", "1.0"), ("/about/", "0.5")]
    extra += [(f"/{k}/", "0.7") for k in SECTIONS]
    write("/sitemap.xml", feeds.sitemap(posts, extra))
    write("/index.json", feeds.search_index(posts))
    write("/site.webmanifest", feeds.webmanifest())
    (OUT_DIR / ".nojekyll").write_text("", encoding="utf-8")

    # 静态资产
    if ASSETS_DIR.is_dir():
        dst = OUT_DIR / "assets"
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(ASSETS_DIR, dst)

    size = sum(f.stat().st_size for f in OUT_DIR.rglob("*") if f.is_file())
    dt = time.time() - t0
    counts = {k: len(by_section(posts, k)) for k in SECTIONS}
    detail = "、".join(f"{SECTIONS[k]['name']} {v}" for k, v in counts.items())
    print(f"✓ {len(posts)} 篇（{detail}）")
    print(f"✓ 生成 {len(GENERATED)} 个页面 · {size / 1024:.0f} KB · {dt:.2f}s")
    print(f"→ {OUT_DIR}")


def main():
    serve = "--serve" in sys.argv
    try:
        build()
    except ContentError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    if serve:
        import http.server
        import os
        import socketserver
        os.chdir(OUT_DIR)
        with socketserver.TCPServer(("127.0.0.1", 8000),
                                    http.server.SimpleHTTPRequestHandler) as httpd:
            print("预览：http://127.0.0.1:8000  （Ctrl-C 停止）")
            httpd.serve_forever()


if __name__ == "__main__":
    main()
