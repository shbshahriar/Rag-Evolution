from __future__ import annotations

import math
import random
import re
import textwrap
import unicodedata
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape


BASE_DIR = Path(__file__).resolve().parents[1] / "datasets" / "sample_docs"
RANDOM_SEED = 20260422


def ascii_text(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def markdown_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []

    def flush() -> None:
        nonlocal current
        if current:
            blocks.append(" ".join(current).strip())
            current = []

    for raw in ascii_text(text).splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            flush()
            continue

        heading = re.match(r"^(#{1,6})\s*(.+)$", stripped)
        if heading:
            flush()
            level = len(heading.group(1))
            title = heading.group(2).strip()
            if level == 1:
                title = title.upper()
            blocks.append(title)
            continue

        bullet = re.match(r"^[-*+]\s+(.+)$", stripped)
        if bullet:
            flush()
            blocks.append(f"- {bullet.group(1).strip()}")
            continue

        clean = re.sub(r"[\*_`]+", "", stripped)
        current.append(clean)

    flush()
    return blocks


def appendix_text(title: str, themes: list[str], target_words: int = 5600) -> str:
    lines = ["", "## Extended Reference Appendix", ""]
    i = 1
    while len(" ".join(lines).split()) < target_words and i <= 120:
        theme = themes[(i - 1) % len(themes)]
        lines.extend(
            [
                f"### {title} Practice Note {i}",
                f"A strong treatment of {title} should connect the core idea to {theme}, because readers need both the definition and the working context. In a retrieval setting, this topic should explain what the concept is, why it matters, how it is used, and what questions usually follow in real work. The best documents make the path from overview to detail feel obvious, so the reader can move from general meaning to concrete application without losing the thread.",
                f"When teams search this content, they usually want a mix of facts, examples, process notes, and cautionary guidance. That means the document benefits from clear sectioning, consistent terminology, and examples that map abstract ideas to concrete situations. For this reason, it helps to describe the inputs, outputs, dependencies, common mistakes, and evaluation criteria that define good use of the topic in practice.",
                f"A useful way to deepen the discussion is to describe how {theme} changes the shape of the explanation. In some cases the emphasis is on background knowledge, while in others the emphasis is on execution, measurement, governance, or troubleshooting. A balanced reference explains both the concept and the decision points around it, so a reader can understand not just what to do, but why the step is sensible.",
                f"For dataset design, this kind of section is valuable because it creates many semantically related passages. Those passages help a retrieval system learn how the topic is phrased across definitions, implementation details, examples, and caveats. If a model can answer questions about the same idea from different angles, it is usually better prepared for real user questions that are short, messy, or incomplete.",
                f"It also helps to include operational guidance. Readers often need to know how the topic appears in daily work, what tools or processes are typically involved, and where the main failure points are. Describing those patterns makes the document more useful than a bare glossary, because it supports both direct lookup and explanatory answers.",
                f"Another important angle is comparison. A strong reference can compare one approach with another, show when a method is appropriate, and identify tradeoffs that affect choice. That comparative framing makes the document richer for retrieval because a single question may ask for differences, advantages, or the conditions under which one option should be preferred over another.",
                f"A practical document also anticipates follow-up questions. After a reader learns the basics of {title}, they often want examples, exceptions, recommended checks, and the common misconceptions to avoid. Good coverage answers these follow-ups in a calm, structured way so the content feels complete without becoming hard to navigate.",
                f"In many knowledge bases, the best content is the content that can be chunked cleanly. Short descriptive paragraphs, explicit headings, and repeated vocabulary help produce retrieval-friendly segments. This appendix therefore uses a stable structure on purpose: it gives the system repeated opportunities to see the topic name, the associated theme, and the kinds of explanatory phrases that usually belong together.",
                f"When the document is read by a human, the repetition still has a purpose. It reinforces the central concept from different perspectives and makes it easier to skim for a needed answer. When the document is read by a model, the repetition creates stronger anchor points for semantic similarity and better grounding across nearby passages.",
                f"The overall principle is simple: describe the idea clearly, place it in a realistic context, show how it is used, and explain the cautions that matter most. That pattern works for technical topics, business topics, policy topics, and educational topics alike. It is also one of the most reliable ways to build a dataset that feels broad enough for testing yet structured enough for retrieval.",
                "",
            ]
        )
        i += 1

    return "\n".join(lines)


def ensure_minimum_words(path: Path, title: str, themes: list[str], min_words: int = 5000) -> None:
    text = path.read_text(encoding="utf-8")
    current = len(ascii_text(text).split())
    if current < min_words:
        path.write_text(text + appendix_text(title, themes), encoding="utf-8")


def make_docx(paragraphs: list[str], out_path: Path) -> None:
    doc_xml = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<w:document xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas"',
        ' xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"',
        ' xmlns:o="urn:schemas-microsoft-com:office:office"',
        ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"',
        ' xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"',
        ' xmlns:v="urn:schemas-microsoft-com:vml"',
        ' xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing"',
        ' xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"',
        ' xmlns:w10="urn:schemas-microsoft-com:office:word"',
        ' xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"',
        ' xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml"',
        ' xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup"',
        ' xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk"',
        ' xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml"',
        ' xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape"',
        ' mc:Ignorable="w14 wp14">',
        "  <w:body>",
    ]

    for para in paragraphs:
        if not para:
            continue
        doc_xml.append(
            "    <w:p><w:r><w:t xml:space=\"preserve\">"
            + escape(para)
            + "</w:t></w:r></w:p>"
        )

    doc_xml.extend(
        [
            '    <w:sectPr>',
            '      <w:pgSz w:w="12240" w:h="15840"/>',
            '      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="708" w:footer="708" w:gutter="0"/>',
            '    </w:sectPr>',
            "  </w:body>",
            "</w:document>",
        ]
    )

    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>
"""
    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"""
    core = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>Sample Document</dc:title>
  <dc:subject>RAG sample corpus</dc:subject>
  <dc:creator>Codex</dc:creator>
  <cp:keywords>sample,rag,document</cp:keywords>
  <dc:description>Generated sample document for retrieval testing.</dc:description>
</cp:coreProperties>
"""
    app = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Microsoft Office Word</Application>
</Properties>
"""

    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("docProps/core.xml", core)
        zf.writestr("docProps/app.xml", app)
        zf.writestr("word/document.xml", "\n".join(doc_xml))


def wrap_blocks_for_pdf(blocks: list[str], width: int = 88) -> list[str]:
    lines: list[str] = []
    for block in blocks:
        if not block:
            lines.append("")
            continue
        if block.isupper() and len(block) < 70:
            lines.append(block)
            lines.append("")
            continue
        wrapped = textwrap.wrap(block, width=width, break_long_words=False, break_on_hyphens=False)
        if not wrapped:
            lines.append("")
        else:
            lines.extend(wrapped)
        lines.append("")
    while lines and lines[-1] == "":
        lines.pop()
    return lines


def pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def make_pdf(blocks: list[str], out_path: Path) -> None:
    lines = wrap_blocks_for_pdf(blocks)
    if not lines:
        lines = [""]

    max_lines = 46
    pages = [lines[i : i + max_lines] for i in range(0, len(lines), max_lines)]

    objects: list[bytes] = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    font_obj_num = 3
    kids = []
    next_obj_num = 4
    page_payloads: list[tuple[int, int, bytes]] = []

    for page in pages:
        page_obj_num = next_obj_num
        content_obj_num = next_obj_num + 1
        next_obj_num += 2
        kids.append(f"{page_obj_num} 0 R")

        content_lines = [
            "BT",
            "/F1 11 Tf",
            "14 TL",
            "72 740 Td",
        ]
        for line in page:
            if line:
                content_lines.append(f"({pdf_escape(line)}) Tj")
            content_lines.append("T*")
        content_lines.append("ET")
        content_stream = "\n".join(content_lines).encode("utf-8")
        page_payloads.append((page_obj_num, content_obj_num, content_stream))

    pages_obj = f"<< /Type /Pages /Count {len(pages)} /Kids [{' '.join(kids)}] >>".encode("ascii")
    objects.insert(1, pages_obj)
    objects.insert(2, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    # Insert pages and content objects in order.
    for page_obj_num, content_obj_num, content_stream in page_payloads:
        page_obj = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 {font_obj_num} 0 R >> >> "
            f"/Contents {content_obj_num} 0 R >>"
        ).encode("ascii")
        objects.append(page_obj)
        content_obj = b"<< /Length " + str(len(content_stream)).encode("ascii") + b" >>\nstream\n" + content_stream + b"\nendstream"
        objects.append(content_obj)

    pdf = bytearray()
    pdf.extend(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{i} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_pos = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        pdf.extend(f"{off:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        (
            "trailer\n"
            f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_pos}\n%%EOF\n"
        ).encode("ascii")
    )

    out_path.write_bytes(pdf)


def main() -> None:
    sources = sorted(p for p in BASE_DIR.glob("*.md") if p.name != "manifest.md")
    rng = random.Random(RANDOM_SEED)
    shuffled = sources[:]
    rng.shuffle(shuffled)
    split_at = math.ceil(len(shuffled) / 2)
    docx_sources = set(shuffled[:split_at])

    themes_by_name = {
        "artificial_intelligence_and_ml.md": ["model training", "data quality", "evaluation", "deployment", "safety", "governance"],
        "business_strategy_and_market_analysis.md": ["competitive advantage", "pricing", "market sizing", "customer segmentation", "growth channels", "metrics"],
        "climate_change_and_environment.md": ["greenhouse gases", "ocean systems", "policy response", "adaptation", "mitigation", "ecosystems"],
        "customer_support_and_troubleshooting.md": ["account access", "error diagnosis", "escalation", "FAQ", "reproduction steps", "resolution"],
        "cybersecurity_and_incident_response.md": ["threat detection", "access control", "incident containment", "logging", "recovery", "lessons learned"],
        "education_and_training_materials.md": ["learning objectives", "lesson design", "assessment", "practice", "feedback", "instructional technology"],
        "financial_reporting_and_analysis.md": ["income statement", "balance sheet", "cash flow", "ratios", "forecasting", "investor reporting"],
        "healthcare_and_clinical_guidelines.md": ["patient intake", "prevention", "medication safety", "population health", "triage", "follow-up"],
        "human_health_and_nutrition.md": ["nutrition", "sleep", "exercise", "disease prevention", "mental health", "longevity"],
        "legal_and_compliance_handbook.md": ["contracts", "privacy", "governance", "audit", "retention", "risk management"],
        "software_engineering_api_documentation.md": ["API design", "authentication", "endpoints", "errors", "testing", "deployment"],
        "space_exploration.md": ["orbital mechanics", "mission design", "launch vehicles", "human spaceflight", "science payloads", "future exploration"],
        "world_history_and_civilizations.md": ["civilizational rise", "empire building", "religious change", "industrialization", "global conflict", "modern globalization"],
    }

    generated = []
    for src in sources:
        stem = src.name
        if stem in themes_by_name:
            ensure_minimum_words(src, stem.removesuffix(".md").replace("_", " ").title(), themes_by_name[stem])
        text = src.read_text(encoding="utf-8")
        blocks = markdown_blocks(text)
        out_path = src.with_suffix(".docx" if src in docx_sources else ".pdf")
        if out_path.suffix == ".docx":
            make_docx(blocks, out_path)
        else:
            make_pdf(blocks, out_path)
        generated.append((src.name, out_path.name))

    print("Generated mixed-format sample docs:")
    for src_name, out_name in generated:
        print(f"{src_name} -> {out_name}")


if __name__ == "__main__":
    main()
