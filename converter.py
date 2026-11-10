"""Convert supported, untrusted uploaded documents to Markdown for model context."""
from __future__ import annotations
import csv
import html
import io
import json
from pathlib import Path

MAX_BYTES = 12 * 1024 * 1024
SUPPORTED = {'.md','.markdown','.txt','.log','.py','.json','.csv','.tsv','.html','.htm','.pdf','.docx','.pptx','.xlsx'}


def md_table(rows):
    rows = [[str(v).replace('|', r'\|').replace('\n', ' ') for v in row] for row in rows]
    if not rows:
        return ''
    width = max(len(row) for row in rows)
    rows = [row + [''] * (width - len(row)) for row in rows]
    return '\n'.join(['| ' + ' | '.join(rows[0]) + ' |', '| ' + ' | '.join(['---']*width) + ' |'] +
                     ['| ' + ' | '.join(r) + ' |' for r in rows[1:]])


def convert(filename: str, data: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED:
        raise ValueError(f'Unsupported file type: {suffix or "(none)"}')
    if len(data) > MAX_BYTES:
        raise ValueError('File exceeds 12 MB limit')
    if not data:
        raise ValueError('File is empty')
    title = f'# Uploaded file: {Path(filename).name}\n\n'
    if suffix in {'.md', '.markdown', '.txt', '.log', '.py'}:
        body = data.decode('utf-8-sig', errors='replace')
        if suffix == '.py':
            body = '```python\n' + body + '\n```'
    elif suffix == '.json':
        body = '```json\n' + json.dumps(json.loads(data), indent=2, ensure_ascii=False) + '\n```'
    elif suffix in {'.csv', '.tsv'}:
        body = md_table(list(csv.reader(io.StringIO(data.decode('utf-8-sig')), delimiter='\t' if suffix == '.tsv' else ',')))
    elif suffix in {'.html', '.htm'}:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(data, 'html.parser')
        for item in soup(['script', 'style']):
            item.decompose()
        body = '\n\n'.join(s.strip() for s in soup.stripped_strings)
    elif suffix == '.pdf':
        import fitz
        doc = fitz.open(stream=data, filetype='pdf')
        if len(doc) > 150:
            raise ValueError('PDF exceeds 150-page limit')
        body = '\n\n'.join(f'## Page {i+1}\n\n{p.get_text(sort=True).strip()}' for i, p in enumerate(doc))
        if not any(p.get_text().strip() for p in doc):
            body = '*No selectable text found; scanned PDFs require OCR (not included).*'
    elif suffix == '.docx':
        from docx import Document
        d = Document(io.BytesIO(data))
        parts = []
        for p in d.paragraphs:
            if p.text.strip():
                style = p.style.name.lower() if p.style else ''
                level = int(style[-1]) if style.startswith('heading ') and style[-1].isdigit() else 0
                parts.append(('#' * level + ' ' if level else '') + p.text)
        for t in d.tables:
            parts.append(md_table([[c.text for c in row.cells] for row in t.rows]))
        body = '\n\n'.join(parts)
    elif suffix == '.pptx':
        from pptx import Presentation
        pres = Presentation(io.BytesIO(data))
        parts = []
        for i, slide in enumerate(pres.slides, 1):
            parts.append(f'## Slide {i}')
            for shape in slide.shapes:
                if shape.has_text_frame and shape.text.strip():
                    parts.append(shape.text.strip())
                if shape.has_table:
                    parts.append(md_table([[cell.text for cell in row.cells] for row in shape.table.rows]))
        body = '\n\n'.join(parts)
    else:  # .xlsx: efficient, read-only parser without Excel process or macros
        from python_calamine import CalamineWorkbook
        wb = CalamineWorkbook.from_filelike(io.BytesIO(data))
        parts = []
        for name in wb.sheet_names:
            sheet = wb.get_sheet_by_name(name)
            rows = sheet.to_python()
            parts.extend([f'## Sheet: {name}', md_table(rows[:5000])])
            if len(rows) > 5000:
                parts.append('*Sheet truncated at 5,000 rows.*')
        body = '\n\n'.join(parts)
    return title + body
