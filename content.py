"""读取 _posts/*.md，解析 front matter，产出统一的 Post 对象。"""
import re
from dataclasses import dataclass, field
from pathlib import Path

from siteconf import CATEGORY_MAP, POSTS_DIR, READING_SPEED, SECTIONS

FM_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?", re.S)
DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-(.+)$")


class ContentError(SystemExit):
    """内容有问题就直接中断构建，不要静默跳过。"""


@dataclass
class Post:
    title: str
    slug: str
    section: str
    date: str
    url: str
    body_md: str
    source: str = ""
    data_note: str = ""
    description: str = ""
    excerpt: str = ""
    minutes: int = 1
    chars: int = 0
    html: str = ""
    aliases: list = field(default_factory=list)
    path: Path = None

    @property
    def section_name(self):
        return SECTIONS[self.section]["name"]


def _unquote(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def parse_front_matter(text):
    m = FM_RE.match(text)
    if not m:
        return {}, text
    fm, key = {}, None
    for raw in m.group(1).splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        item = re.match(r"^\s*-\s+(.*)$", raw)
        if item and key:
            if not isinstance(fm.get(key), list):
                fm[key] = []
            fm[key].append(_unquote(item.group(1)))
            continue
        kv = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", raw)
        if kv:
            key = kv.group(1)
            val = _unquote(kv.group(2))
            fm[key] = val if val else []
    return fm, text[m.end():]


def md_plain(md):
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", md)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"^\s{0,3}(#{1,6}|>)\s*", "", t, flags=re.M)
    t = re.sub(r"^\s*[-*+]\s+", "", t, flags=re.M)
    t = re.sub(r"[*_`~]", "", t)
    t = re.sub(r"<[^>]+>", "", t)
    return re.sub(r"\s+", " ", t).strip()


def first_paragraph(body):
    for block in re.split(r"\n\s*\n", body):
        b = block.strip()
        if not b or b.startswith(("#", "!", ">", "|", "---", "```", ":::")):
            continue
        if re.match(r"^[-*+]\s", b):
            continue
        return b
    return ""


def first_sentence(text, limit=78):
    text = text.strip()
    if not text:
        return ""
    for i, ch in enumerate(text):
        if ch in "。！？!?" and 12 <= i + 1 <= limit:
            return text[: i + 1]
    return text[:limit].rstrip("，、；：,;: ") + ("…" if len(text) > limit else "")


def kebab(s):
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"[^A-Za-z0-9\-\u4e00-\u9fff]", "", s)
    return re.sub(r"-{2,}", "-", s).strip("-").lower()


def _as_list(v):
    if isinstance(v, list):
        return [x for x in v if x]
    return [v] if isinstance(v, str) and v else []


def reading_minutes(text):
    body = md_plain(text)
    cjk = len(re.findall(r"[\u4e00-\u9fff]", body))
    latin = len(re.findall(r"[A-Za-z]+", body))
    chars = cjk + latin
    return max(1, round(chars / READING_SPEED)), chars


def _check_permalink(pl, section, name):
    if not pl:
        return ""
    m = re.match(r"^/([a-z0-9-]+)/([^/]+)\.html$", pl)
    if not m:
        raise ContentError(f"✗ {name}: permalink 格式不对 → {pl}")
    if m.group(1) != section:
        raise ContentError(
            f"✗ {name}: permalink 栏目 {m.group(1)!r} 与分类 {section!r} 冲突")
    return pl


def load_posts():
    if not POSTS_DIR.is_dir():
        raise ContentError(f"✗ 找不到文章目录：{POSTS_DIR}")

    posts, problems = [], []
    for f in sorted(POSTS_DIR.glob("*.md")):
        if f.name.startswith("."):
            continue
        raw = f.read_text(encoding="utf-8")
        fm, body = parse_front_matter(raw)

        m = DATE_RE.match(f.stem)
        if not m:
            problems.append(f"{f.name}: 文件名必须以 YYYY-MM-DD- 开头")
            continue
        date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        old_slug = m.group(4)

        title = _unquote(str(fm.get("title") or "")).strip()
        if not title:
            problems.append(f"{f.name}: 缺 title")
            continue
        if not body.strip():
            problems.append(f"{f.name}: 正文为空")
            continue

        cats = _as_list(fm.get("categories"))
        cat = cats[0] if cats else ""
        section = CATEGORY_MAP.get(cat)
        if not section:
            problems.append(f"{f.name}: 未知分类 {cat!r}，请加到 siteconf.CATEGORY_MAP")
            continue

        slug = kebab(old_slug)
        pl = _check_permalink(str(fm.get("permalink") or "").strip(), section, f.name)
        url = pl or f"/{section}/{slug}.html"

        minutes, chars = reading_minutes(body)
        plain = md_plain(first_paragraph(body))
        desc = _unquote(str(fm.get("description") or "")).strip() or first_sentence(plain)

        post = Post(
            title=title, slug=slug, section=section, date=date, url=url,
            body_md=body,
            source=_unquote(str(fm.get("source") or "")),
            data_note=_unquote(str(fm.get("data_note") or "")),
            description=desc,
            excerpt=first_sentence(plain, 90),
            minutes=minutes, chars=chars, path=f,
        )

        # 旧链接保底
        # 1) 老构建在没有 permalink 时，用「日-slug」当路径（/notes/20-woop.html）
        # 2) 老构建在根目录留过同名别名（/woop.html）
        legacy = set()
        if not pl:
            legacy.add(f"/{section}/{m.group(3)}-{old_slug}.html")
        legacy.add(f"/{old_slug}.html")
        post.aliases = sorted(a for a in legacy if a != url)
        posts.append(post)

    if problems:
        raise ContentError("✗ 内容校验失败：\n  " + "\n  ".join(problems))

    if not posts:
        raise ContentError("✗ 一篇文章都没读到")

    # 倒序：最新在前
    posts.sort(key=lambda p: (p.date, p.slug), reverse=True)

    seen = {}
    for p in posts:
        if p.url in seen:
            raise ContentError(f"✗ URL 冲突：{p.url}（{seen[p.url]} 与 {p.path.name}）")
        seen[p.url] = p.path.name
    return posts


def by_section(posts, section):
    return [p for p in posts if p.section == section]


def neighbours(posts, post):
    """同栏目的上一篇（更新）/下一篇（更旧）。"""
    group = by_section(posts, post.section)
    i = group.index(post)
    newer = group[i - 1] if i > 0 else None
    older = group[i + 1] if i + 1 < len(group) else None
    return newer, older
