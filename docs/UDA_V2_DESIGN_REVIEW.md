# DEV-020 — ShadowPrompt Lab V2 security and runtime review

**Status: DESIGN ONLY. Do not expose the current development server.**

Source evidence: `README.md`, `app.py`, `requirements.txt`.
ShadowPrompt Lab is a single-operator Flask training sandbox with an Ollama
external model dependency, uploaded-document conversion, forced
operator-defined skill proposals, and separately approved `save_markdown`
and `send_email` actions. A successful model response or manifest parse
**does not** grant either skill execution.

The current `app.py` constructs `output/` and writes converted input,
`audit.jsonl` and approved files. Audit logs can retain uploaded and
model-generated content. The current implementation has process-local
pending approvals and intentionally lacks login, CSRF protection and
isolated tool execution. The README requires `FLASK_HOST=127.0.0.1`;
no unauthenticated LAN/public proxy deployment is safe as-is.

## Mandatory V2 boundary

- Separate required config names from secret values for
  `OLLAMA_URL`, `OLLAMA_MODEL`, SMTP transport, fixed `EMAIL_TO`, and
  any email credentials. Never insert real recipients or secrets in Git.
- Keep all outbound model/email actions disabled-by-default with explicit,
  independently auditable approval; uploaded documents remain untrusted data.
- Scope and protect `output/` and audit files, establish retention,
  archive/cleanup and backups (if data must be retained). Do not publish them
  as static assets or attach their contents to PR comments.
- A future external UDA route requires working app auth, CSRF controls,
  permission-scoped approval requests, single-use durable approval records,
  request-size limits and safe cookie handling before enabling access.
- Create a reviewed production WSGI entrypoint rather than assuming the
  `python app.py` development server is deployment-ready.

## Required acceptance

- [ ] Confirm whether ShadowPrompt Lab is actually installed/live, effective
      process owner, local bind port and UDA registration read-only.
- [ ] Verify safe and deliberate separation of synthetic examples from
      sensitive uploads/audit content.
- [ ] Independently test forced-skill ordering, fail-closed validation,
      approval/rejection and SMTP sink, with no live email sent.
- [ ] Test CSRF/authentication and external-model data boundary.
- [ ] Confirm persistence/retention and separately approved capabilities.
- [ ] Only then create an executable V2 manifest and run canonical validation.

No process, mail, uploaded data, Caddy, UDA or production change was made.
