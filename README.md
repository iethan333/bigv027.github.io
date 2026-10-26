# 学习成长再生 · 站点工程

纯静态、零前端框架、零 npm。Python + pandoc 把 `_posts/*.md` 编译成 HTML，
产物由 GitHub Actions 自动提交回仓库，GitHub Pages 直接托管。

## 日常发文章：写 md，push，完事

```bash
vim _posts/2026-11-02-your-slug.md
git add . && git commit -m "新文章" && git push
```

推上去之后 GitHub Actions 会自动跑构建、把产物提交回 `master`，一两分钟后线上就更新了。
本地不需要装 python 和 pandoc，也不用手动 build。

想先看效果，本地跑一次：

```bash
python3 build.py --serve     # http://127.0.0.1:8000
```

本地构建需要 `python3` 和 `pandoc`（`sudo pacman -S pandoc`）。

## 目录

```
_posts/      文章源文件（YYYY-MM-DD-slug.md）
_pages/      独立页面（about.md → /about/）
assets/      样式、脚本、图标、分享图（原样复制到 site/assets/）
siteconf.py  站点名、栏目、导航、首页每栏篇数
content.py   读文章、解析 front matter、校验、排序
render.py    Markdown → HTML（pandoc 一次批量转完）
templates.py 页面模板（head / 导航 / 列表 / 文章 / 跳转页）
feeds.py     RSS、sitemap、robots、搜索索引、webmanifest
build.py     构建入口
deploy.py    把 site/ 同步到仓库根目录（Actions 里跑的就是它）
.github/workflows/build.yml   push 后自动构建
site/        产物（不入库）
```

## 文章 front matter

最少这些：

```yaml
---
title: "标题"
categories:
  - 深度          # 深度 / 佛典故事 / edu / 工作 / 学习 / sys / blog
---
```

可选项：

```yaml
permalink: /deep/your-slug.html   # 不写就按文件名生成
source: "《杂宝藏经》卷4"          # 文章末尾的出处
data_note: "展现 40,235 · 阅读 7,032"   # 文末注脚的发布数据
description: "分享卡片和搜索结果的摘要"   # 不写就取正文首句
draft: true                       # 草稿，不发布
```

`categories` 必须是在 `siteconf.py` 的 `CATEGORY_MAP` 里登记过的。
写错不会静默丢文章——构建直接报错退出。

## 几条约定

- **排序**：全站按日期倒序，最新在前。
- **URL**：`/栏目/slug.html`。slug 一律小写连字符（`DoYourHomework` → `do-your-homework`）。
- **旧链接**：改 slug 后 `content.py` 会生成跳转页，带 `noindex` 和 canonical，不跟正文抢收录。
- **标题换行**：CSS 用 `word-break: keep-all`，只在标点处断行，避免把「第四禅」拆成两行。
  无标点的超长片段由 `templates.display_title()` 自动找一个体面的断点。
- **图标**：`assets/favicon.ico`（16/32/48）、`favicon-32.png`、`apple-touch-icon.png`、`icon-192/512.png`。
  换图标就从原图重新生成这一套，别只换一个。
- **分享图**：`assets/og.png`（1200×630）。改站点文案后记得重画。
- **字体**：默认用系统思源宋体 / 宋体。要统一观感，把子集化字体放到 `assets/fonts/`
  并取消 `assets/style.css` 末尾 `@font-face` 的注释。

## 手动部署（Actions 挂了时的兜底）

```bash
python3 build.py
python3 deploy.py .
git add -A && git commit -m "build: 手动" && git push
```

`deploy.py` 读 `.build-manifest.json` 记住上一版生成了哪些文件，
这一版不再需要的会删掉，避免旧文章改名后留下孤儿 HTML。

## 首次接入

仓库里已有 `.github/workflows/build.yml`，push 到 `master` 就生效。
若 Actions 没有写权限：仓库 → Settings → Actions → General → Workflow permissions
→ 选 **Read and write permissions**。
