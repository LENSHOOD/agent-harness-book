from __future__ import annotations

import hashlib
from html import escape
from pathlib import Path
import re

import markdown
import reportlab
from reportlab import rl_config
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Image as RLImage,
    LongTable,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "publishing" / "artifacts"
OUT.mkdir(exist_ok=True)

SNAPSHOT = "2026-08-28"
# ReportLab otherwise embeds the wall-clock build time and a random document ID.
# Invariant mode makes identical inputs produce byte-identical publication files.
rl_config.invariant = 1
pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
REPORTLAB_FONTS = Path(reportlab.__file__).resolve().parent / "fonts"
pdfmetrics.registerFont(TTFont("VeraEmbedded", str(REPORTLAB_FONTS / "Vera.ttf")))
pdfmetrics.registerFont(TTFont("VeraEmbedded-Bold", str(REPORTLAB_FONTS / "VeraBd.ttf")))

CSS = r'''
@page { size: A4; margin: 18mm 17mm 20mm 17mm; }
* { box-sizing:border-box; }
body { font-family:"PingFang SC","Noto Sans CJK SC",sans-serif; color:#18242c;
  font-size:10pt; line-height:1.68; max-width:1040px; margin:0 auto; padding:28px 42px; }
h1,h2,h3,h4 { color:#003d5c; line-height:1.25; }
h1 { font-size:22pt; border-bottom:2px solid #003d5c; padding-bottom:7px; margin:36px 0 17px; }
h2 { font-size:16pt; margin:27px 0 12px; border-bottom:1px solid #aebdc6; padding-bottom:5px; }
h3 { font-size:12.5pt; margin:20px 0 8px; }
img { display:block; max-width:100%; height:auto; margin:14px auto 6px; }
p { margin:0 0 9px; }
a { color:#005b82; text-decoration:none; overflow-wrap:anywhere; }
blockquote { margin:12px 0; padding:8px 14px; border-left:4px solid #407f9b; background:#f3f6f7; color:#3d4a52; }
pre { white-space:pre-wrap; background:#f3f5f6; border-left:3px solid #315d72; padding:10px 12px; font:8.4pt/1.48 monospace; }
code { background:#f1f3f4; padding:1px 3px; }
table { width:100%; border-collapse:collapse; margin:12px 0 17px; font-size:8.6pt; }
th { background:#003d5c; color:white; text-align:left; }
th,td { border:1px solid #ccd5da; padding:6px 7px; vertical-align:top; }
.title-block { background:#003d5c; color:white; padding:58px 48px; margin:-28px -42px 35px; min-height:260px; }
.title-block h1 { color:white; border:0; margin:0 0 14px; }
.title-block .subtitle { font-size:15pt; color:#cce0ea; }
.title-block .meta { margin-top:70px; color:#c1d5df; }
'''


def render_html(md_path: Path, html_path: Path, title: str, subtitle: str) -> None:
    text = md_path.read_text()
    text = re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.S)
    html = markdown.markdown(
        text,
        extensions=["extra", "toc", "sane_lists"],
        extension_configs={"toc": {"title": "自动目录"}},
    )
    doc = (
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width"><title>{title}</title>'
        f"<style>{CSS}</style></head><body>"
        f'<div class="title-block"><h1>{title}</h1><div class="subtitle">{subtitle}</div>'
        f'<div class="meta">研究修订稿<br>资料截面：{SNAPSHOT}</div></div>{html}</body></html>'
    )
    html_path.write_text(doc)


class BookDocTemplate(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if not isinstance(flowable, Paragraph):
            return
        style_name = flowable.style.name
        if style_name not in {"Heading1", "Heading2", "Heading3", "Heading4"}:
            return
        level = {"Heading1": 0, "Heading2": 1, "Heading3": 2, "Heading4": 3}[style_name]
        text = flowable.getPlainText()
        key = flowable._bookmark_key
        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(text, key, level=level, closed=level > 0)
        self.notify("TOCEntry", (level, text, self.page, key))


def page_footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#65737e"))
    canvas.setFont("VeraEmbedded", 8)
    canvas.drawCentredString(A4[0] / 2, 10 * mm, str(doc.page))
    canvas.restoreState()


def cover_page(canvas, doc) -> None:
    """Draw the cover directly so Latin and CJK text use appropriate fonts."""
    canvas.saveState()
    centre = A4[0] / 2
    canvas.setFillColor(colors.HexColor("#003d5c"))
    canvas.setFont("VeraEmbedded-Bold", 29)
    canvas.drawCentredString(centre, 190 * mm, doc.title)
    canvas.setFillColor(colors.HexColor("#407f9b"))
    canvas.setFont("STSong-Light", 15)
    canvas.drawCentredString(centre, 174 * mm, doc.subject)
    canvas.setFillColor(colors.HexColor("#65737e"))
    canvas.setFont("STSong-Light", 10)
    canvas.drawCentredString(centre, 78 * mm, "研究修订稿")
    canvas.drawCentredString(centre, 64 * mm, "资料截面")
    canvas.setFont("VeraEmbedded", 10)
    canvas.drawCentredString(centre, 58 * mm, SNAPSHOT)
    canvas.restoreState()


def inline_markup(text: str) -> str:
    rendered = markdown.markdown(text, extensions=["sane_lists"]).strip()
    rendered = re.sub(r"^<p>|</p>$", "", rendered)
    rendered = rendered.replace("<a href=", "<link href=").replace("</a>", "</link>")
    rendered = rendered.replace("<code>", '<font name="STSong-Light" color="#005b82">')
    rendered = rendered.replace("</code>", "</font>")
    rendered = rendered.replace("<hr />", "")
    return rendered


def styles():
    base = getSampleStyleSheet()
    body = ParagraphStyle(
        "Body",
        parent=base["BodyText"],
        fontName="STSong-Light",
        fontSize=9.5,
        leading=15.5,
        textColor=colors.HexColor("#18242c"),
        spaceAfter=7,
        splitLongWords=True,
        wordWrap="CJK",
    )
    return {
        "Body": body,
        "Heading1": ParagraphStyle(
            "Heading1", parent=body, fontSize=19, leading=25, textColor=colors.HexColor("#003d5c"),
            spaceBefore=12, spaceAfter=12, keepWithNext=True, pageBreakBefore=False,
        ),
        "Heading2": ParagraphStyle(
            "Heading2", parent=body, fontSize=13, leading=18, textColor=colors.HexColor("#075985"),
            spaceBefore=14, spaceAfter=8, keepWithNext=True,
        ),
        "Heading3": ParagraphStyle(
            "Heading3", parent=body, fontSize=11.5, leading=16, textColor=colors.HexColor("#164e63"),
            spaceBefore=10, spaceAfter=6, keepWithNext=True,
        ),
        "Heading4": ParagraphStyle(
            "Heading4", parent=body, fontSize=10.2, leading=15, textColor=colors.HexColor("#28566a"),
            spaceBefore=8, spaceAfter=5, keepWithNext=True,
        ),
        "Quote": ParagraphStyle(
            "Quote", parent=body, leftIndent=10, rightIndent=8, borderColor=colors.HexColor("#407f9b"),
            borderWidth=1, borderPadding=7, backColor=colors.HexColor("#f3f6f7"),
            textColor=colors.HexColor("#3d4a52"), spaceBefore=5, spaceAfter=8,
        ),
        "List": ParagraphStyle("List", parent=body, leftIndent=14, firstLineIndent=-8, bulletIndent=4),
        "Code": ParagraphStyle(
            "Code", parent=body, fontName="STSong-Light", fontSize=7.8, leading=11,
            leftIndent=8, rightIndent=8, borderColor=colors.HexColor("#315d72"), borderWidth=1,
            borderPadding=7, backColor=colors.HexColor("#f3f5f6"), spaceBefore=4, spaceAfter=9,
        ),
        "CodeLabel": ParagraphStyle(
            "CodeLabel", parent=body, fontSize=6.5, leading=8, textColor=colors.HexColor("#65737e"),
            spaceBefore=4, spaceAfter=1,
        ),
        "FigureCaption": ParagraphStyle(
            "FigureCaption", parent=body, fontSize=7.8, leading=11, alignment=TA_CENTER,
            textColor=colors.HexColor("#52636d"), spaceBefore=2, spaceAfter=10,
        ),
        "TableCell": ParagraphStyle("TableCell", parent=body, fontSize=6.5, leading=8.5, spaceAfter=0),
        "TableHead": ParagraphStyle(
            "TableHead", parent=body, fontSize=6.5, leading=8.5, textColor=colors.white, spaceAfter=0,
        ),
        "CoverTitle": ParagraphStyle(
            "CoverTitle", parent=body, fontName="VeraEmbedded-Bold", fontSize=29, leading=38, alignment=TA_CENTER,
            textColor=colors.HexColor("#003d5c"), spaceAfter=18,
        ),
        "CoverSubtitle": ParagraphStyle(
            "CoverSubtitle", parent=body, fontSize=15, leading=23, alignment=TA_CENTER,
            textColor=colors.HexColor("#407f9b"),
        ),
        "CoverMeta": ParagraphStyle(
            "CoverMeta", parent=body, fontSize=10, leading=18, alignment=TA_CENTER,
            textColor=colors.HexColor("#65737e"),
        ),
    }


def markdown_table(lines: list[str], sheet: dict, available_width: float):
    rows = []
    for row_index, line in enumerate(lines):
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        style = sheet["TableHead"] if not rows else sheet["TableCell"]
        rows.append([Paragraph(inline_markup(cell), style) for cell in cells])
    if not rows:
        return Spacer(1, 1)
    columns = max(len(row) for row in rows)
    for row in rows:
        row.extend(Paragraph("", sheet["TableCell"]) for _ in range(columns - len(row)))
    table = LongTable(rows, colWidths=[available_width / columns] * columns, repeatRows=1, hAlign=TA_LEFT)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003d5c")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#b9c7ce")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f8f9")]),
            ]
        )
    )
    return table


def parse_markdown(text: str, sheet: dict, available_width: float, base_dir: Path) -> list:
    text = re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.S)
    lines = text.splitlines()
    story = []
    paragraph: list[str] = []
    code: list[str] = []
    code_language = ""
    in_code = False
    seen_heading1 = False
    heading_serial = 0

    def flush_paragraph():
        if paragraph:
            story.append(Paragraph(inline_markup(" ".join(part.strip() for part in paragraph)), sheet["Body"]))
            paragraph.clear()

    index = 0
    while index < len(lines):
        line = lines[index]
        if in_code:
            if line.startswith("```"):
                if code_language:
                    story.append(Paragraph(escape(code_language.upper()), sheet["CodeLabel"]))
                # Preformatted handles XML-sensitive characters, but ReportLab does not
                # decode &quot;/&#x27; in this flowable. Keep quotes literal so JSON/YAML
                # remains readable while still escaping angle brackets and ampersands.
                story.append(Preformatted(escape("\n".join(code), quote=False), sheet["Code"], maxLineLength=92))
                code.clear()
                in_code = False
                code_language = ""
            else:
                code.append(line)
            index += 1
            continue

        if line.startswith("```"):
            flush_paragraph()
            in_code = True
            code_language = line[3:].strip()
            index += 1
            continue

        if line.startswith("|") and index + 1 < len(lines) and lines[index + 1].startswith("|"):
            flush_paragraph()
            table_lines = []
            while index < len(lines) and lines[index].startswith("|"):
                table_lines.append(lines[index])
                index += 1
            story.append(markdown_table(table_lines, sheet, available_width))
            story.append(Spacer(1, 7))
            continue

        image_match = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", line.strip())
        if image_match:
            flush_paragraph()
            alt, href = image_match.groups()
            image_path = (base_dir / href).resolve()
            if not image_path.is_file():
                raise FileNotFoundError(f"Markdown image not found: {image_path}")
            figure = RLImage(str(image_path))
            scale = min(available_width / figure.imageWidth, (105 * mm) / figure.imageHeight, 1.0)
            figure.drawWidth = figure.imageWidth * scale
            figure.drawHeight = figure.imageHeight * scale
            figure.hAlign = "CENTER"
            story.extend([Spacer(1, 7), figure])
            if alt:
                story.append(Paragraph(escape(alt), sheet["FigureCaption"]))
            index += 1
            continue

        heading = re.match(r"^(#{1,4})\s+(.+)$", line)
        if heading:
            flush_paragraph()
            level = len(heading.group(1))
            if level == 1:
                if seen_heading1:
                    story.append(PageBreak())
                seen_heading1 = True
            elif level == 2 and re.match(r"^(?:第[一二三四五六七八九十百]+章|附录)", heading.group(2)):
                story.append(PageBreak())
            heading_serial += 1
            heading_text = heading.group(2)
            digest = hashlib.sha256(
                f"{heading_serial}\0{level}\0{heading_text}".encode("utf-8")
            ).hexdigest()[:16]
            heading_paragraph = Paragraph(inline_markup(heading_text), sheet[f"Heading{level}"])
            heading_paragraph._bookmark_key = f"heading-{heading_serial}-{digest}"
            story.append(heading_paragraph)
            index += 1
            continue

        if line.strip() == "[TOC]":
            flush_paragraph()
            toc = TableOfContents()
            toc.levelStyles = [
                ParagraphStyle("TOC1", fontName="STSong-Light", fontSize=9, leading=14, leftIndent=0, firstLineIndent=0),
                ParagraphStyle("TOC2", fontName="STSong-Light", fontSize=8, leading=12, leftIndent=12, firstLineIndent=0),
                ParagraphStyle("TOC3", fontName="STSong-Light", fontSize=7, leading=10, leftIndent=24, firstLineIndent=0),
                ParagraphStyle("TOC4", fontName="STSong-Light", fontSize=6.5, leading=9, leftIndent=36, firstLineIndent=0),
            ]
            story.append(toc)
            index += 1
            continue

        if line.startswith("> "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(line[2:].strip()), sheet["Quote"]))
            index += 1
            continue

        list_item = re.match(r"^\s*(?:[-*]|\d+\.)\s+(.+)$", line)
        if list_item:
            flush_paragraph()
            story.append(Paragraph("• " + inline_markup(list_item.group(1)), sheet["List"]))
            index += 1
            continue

        if line.strip() == "---":
            flush_paragraph()
            story.append(HRFlowable(width="100%", thickness=0.4, color=colors.HexColor("#d2dade"), spaceBefore=6, spaceAfter=8))
            index += 1
            continue

        if not line.strip():
            flush_paragraph()
        else:
            paragraph.append(line)
        index += 1

    flush_paragraph()
    return story


def render_pdf(md_path: Path, pdf_path: Path, title: str, subtitle: str) -> None:
    sheet = styles()
    doc = BookDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=17 * mm,
        rightMargin=17 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=title,
        author="Agent Harness Book Research",
        subject=subtitle,
    )
    cover = [PageBreak()]
    story = cover + parse_markdown(md_path.read_text(), sheet, doc.width, md_path.parent)
    doc.multiBuild(story, onFirstPage=cover_page, onLaterPages=page_footer)


def main() -> None:
    publications = [
        (OUT / "agent_harness_book.md", "Agent Harness", "从执行脚手架到自我进化系统"),
        (OUT / "executive_brief.md", "Agent Harness", "企业决策者精简版"),
    ]
    for md_path, title, subtitle in publications:
        render_html(md_path, md_path.with_suffix(".html"), title, subtitle)
        render_pdf(md_path, md_path.with_suffix(".pdf"), title, subtitle)


if __name__ == "__main__":
    main()
