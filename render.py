"""Markdown → HTML。走 pandoc，再做几处必要的后处理。"""
import re
import shutil
import subprocess

PANDOC_ARGS = [
    "pandoc", "-f", "markdown", "-t", "html5",
    "--wrap=none",
]


def pandoc_ready():
    return shutil.which("pandoc") is not None


def md_to_html(md_text, name=""):
    try:
        out = subprocess.run(
            PANDOC_ARGS, input=md_text, capture_output=True, text=True, check=True
        ).stdout
    except FileNotFoundError:
        raise SystemExit("✗ 没装 pandoc。装一个：sudo pacman -S pandoc")
    except subprocess.CalledProcessError as e:
        raise SystemExit(f"✗ pandoc 转换失败 {name}:\n{e.stderr}")
    return polish(out)


SPLIT = '<div class="__s"></div>'


def normalize_md(md):
    """引用块前面缺空行时，pandoc 会把它当成上一段的一部分（页面上直接出现 >）。

    中文写作里「图片 / 正文 紧接着 > 引文」几乎都是漏了空行，这里补上。
    """
    out, prev = [], ""
    for line in md.split("\n"):
        s = line.strip()
        if s.startswith(">") and prev and not prev.strip().startswith(">"):
            out.append("")
        out.append(line)
        prev = line
    return "\n".join(out)


def md_batch_to_html(items):
    """一次性转完所有正文。items=[(md, name)]，返回同长度的 html 列表。

    pandoc 每次启动约 0.4s，30 篇逐篇调用要 13s；合并成一次约 0.5s。
    用一段原样输出的 HTML 块做分隔符，pandoc 不会改动它。
    """
    if not items:
        return []
    joined = f"\n\n{SPLIT}\n\n".join(normalize_md(md) for md, _ in items)
    try:
        out = subprocess.run(
            PANDOC_ARGS, input=joined, capture_output=True, text=True, check=True
        ).stdout
    except FileNotFoundError:
        raise SystemExit("✗ 没装 pandoc。装一个：sudo pacman -S pandoc")
    except subprocess.CalledProcessError as e:
        raise SystemExit(f"✗ pandoc 批量转换失败:\n{e.stderr}")

    parts = re.split(r'<div class="__s">\s*</div>', out)
    if len(parts) != len(items):
        # 分隔符被吃掉就退回逐篇，宁可慢也不要错
        return [md_to_html(md, name) for md, name in items]
    return [polish(p) for p in parts]


QUOTE_RE = re.compile(r"[\u201c\u201d]")


def fix_quotes(html):
    """中文里 pandoc 的 smart 引号经常把开口引号判成闭口（引号紧跟汉字时）。

    中文引号永远成对出现，按出现顺序“闭开交替”重排就能纠正，
    已经正确的不受影响。英文撇号（’）不动，避免误伤。
    """
    lines = []
    for line in html.split("\n"):
        if QUOTE_RE.search(line):
            n = 0
            buf = []
            for ch in line:
                if ch in "“”":
                    buf.append("“" if n % 2 == 0 else "”")
                    n += 1
                else:
                    buf.append(ch)
            line = "".join(buf)
        lines.append(line)
    return "\n".join(lines)


def polish(html):
    html = fix_quotes(html)
    # 图片懒加载，避免长文首屏拖慢
    html = re.sub(
        r"<img\s",
        '<img loading="lazy" decoding="async" ',
        html,
    )
    # 宽表格在移动端横滚，而不是把版面撑破
    html = html.replace("<table>", '<div class="table-wrap"><table>')
    html = html.replace("</table>", "</table></div>")
    # 外链加 rel，内链不动
    html = re.sub(
        r'<a href="(https?://[^"]+)"',
        r'<a href="\1" rel="noopener"',
        html,
    )
    return html.strip()
