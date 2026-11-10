# ShadowPrompt Lab

A **Flask** educational sandbox for demonstrating how a visible prompt, separate editable operator instruction and untrusted uploaded document interact with an **Ollama** model. Default model: `gpt-oss:120b-cloud`.

## Install and run (Python 3.11+)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env if Ollama is on another server
python app.py
```

Open <http://127.0.0.1:5000>. Your Ollama instance must already have access to `gpt-oss:120b-cloud` (cloud access may require a signed-in Ollama setup):

```bash
ollama run gpt-oss:120b-cloud
```

If Ollama runs on another host, set `OLLAMA_URL` accordingly. **Do not expose a raw, unauthenticated Ollama endpoint publicly.**

## File-to-Markdown pipeline

Every uploaded file is converted into Markdown **before** sending content to Ollama; the Markdown is also saved in `output/` and shown in the interface.

| Input | Conversion |
|---|---|
| `.md`, `.markdown`, `.txt`, `.log`, `.py` | UTF-8 text (Python fenced) |
| `.csv`, `.tsv` | Markdown table |
| `.json` | Formatted JSON block |
| `.html`, `.htm` | Visible text stripped of scripts/styles |
| `.pdf` | Text by page (scanned PDFs need separate OCR) |
| `.docx` | Paragraphs/headings and tables |
| `.pptx` | Text and tables by slide |
| `.xlsx` | Cells as Markdown tables by sheet (first 5,000 rows each) |

Conversion is **best effort**. Layout, embedded images, formulas, comments, and some ordering are not preserved. Unsupported formats are rejected. Input is capped at 12 MB; model context is truncated to `MAX_CONTEXT_CHARS`.

Source code remains Python/HTML; **documents uploaded into the app** become Markdown. Original uploaded files are not saved or executed.

## Two supervised skills

The model can *propose* a `save_markdown` action or a `send_email` action, with selected text. Actions are displayed for manual approval. Markdown is written to `output/approved_*.md`. Emails go only to the fixed `EMAIL_TO` address from `.env`, using configured SMTP credentials. No automatic sending; no model-supplied recipient or filename.

`.env` remains untracked. A JSONL audit log is saved in `output/audit.jsonl`, including the visible and hidden prompts: **use synthetic course data only**.

## Suggested exercise

1. Upload a benign document; ask for a summary without the additional instruction.
2. Add a hidden operator instruction, compare model output.
3. Embed a simulated malicious instruction inside a test document; examine whether it tries to issue a tool action.
4. Check the proposed action contents and the audit log. Only approve actions using synthetic, non-sensitive test data.

**Trust boundaries:** Hidden operator instructions and malicious document-embedded instructions are not the same. The latter are lower-trust content and should not override user intent. Model-generated tool proposals are advisory, require manual review, and are not proof that an attack succeeded.

## Limitations

Single-user local teaching prototype: no authentication, session isolation, or persistent action queue. Keep bound to `127.0.0.1`; do not deploy publicly without hardening. The cloud Ollama model may send your submitted text to a remote service: avoid private or confidential files.
