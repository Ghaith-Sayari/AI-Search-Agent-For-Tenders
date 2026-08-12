from __future__ import annotations

from datetime import timezone
from io import BytesIO
from typing import Any

from agents.proposal_generator.models.proposal_output import ProposalOutput


def _add_toc(document: Any) -> None:
    """Insert a Word TOC field (updates on open in MS Word)."""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    p = document.add_paragraph()
    run = p.add_run()._r

    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    run.append(fld_begin)

    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = 'TOC \\o "1-3" \\h \\z \\u'
    run.append(instr)

    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")
    run.append(fld_sep)

    p.add_run("Table of Contents (right-click > Update Field)")

    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run.append(fld_end)


def _compliance_rows(output: ProposalOutput) -> list[dict[str, str]]:
    issue_by_req = {i.requirement_id: i for i in output.compliance_issues}
    rows: list[dict[str, str]] = []

    seen = set()
    for s in sorted(output.sections, key=lambda x: x.order):
        for req_id in s.requirement_ids:
            seen.add(req_id)
            issue = issue_by_req.get(req_id)
            rows.append(
                {
                    "requirement_id": req_id,
                    "status": "Needs attention" if issue else "Covered",
                    "severity": issue.severity if issue else "none",
                    "section": s.title,
                    "notes": issue.message if issue else "Mapped in proposal section.",
                }
            )

    # Include issues without explicit requirement_ids in sections
    for issue in output.compliance_issues:
        if issue.requirement_id in seen:
            continue
        rows.append(
            {
                "requirement_id": issue.requirement_id,
                "status": "Needs attention",
                "severity": issue.severity,
                "section": issue.section_key or "N/A",
                "notes": issue.message,
            }
        )

    return rows


def render_proposal_docx_bytes(output: ProposalOutput, tender_title: str) -> bytes:
    """
    Produce polished DOCX with:
    - cover page
    - table of contents
    - proposal sections
    - compliance matrix table
    """
    try:
        from docx import Document
    except Exception as exc:
        raise RuntimeError(
            "python-docx is required for DOCX export. Install with: pip install python-docx"
        ) from exc

    document = Document()

    # Cover page
    document.add_heading("Tender Proposal", level=0)
    document.add_paragraph(f"Tender: {tender_title}")
    document.add_paragraph(f"Company: {output.profile_name}")
    document.add_paragraph(f"Tender External ID: {output.tender_external_id or 'N/A'}")
    document.add_paragraph(
        f"Generated At (UTC): {output.generated_at.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}"
    )
    document.add_paragraph(f"Decision: {output.decision.upper()}")
    document.add_paragraph(
        f"Score: {output.total_score:.2f} | Confidence: {output.confidence_score:.2f}"
    )
    document.add_page_break()

    # TOC
    document.add_heading("Table of Contents", level=1)
    _add_toc(document)
    document.add_page_break()

    # Main content
    document.add_heading("Executive Summary", level=1)
    document.add_paragraph(output.executive_summary or "")

    for section in sorted(output.sections, key=lambda s: s.order):
        document.add_heading(section.title, level=1)
        for para in (section.content or "").split("\n"):
            if para.strip():
                document.add_paragraph(para.strip())

    # Compliance matrix
    document.add_page_break()
    document.add_heading("Compliance Matrix", level=1)
    rows = _compliance_rows(output)
    table = document.add_table(rows=max(2, len(rows) + 1), cols=5)
    table.style = "Table Grid"
    headers = ["Requirement ID", "Status", "Severity", "Section", "Notes"]
    for idx, text in enumerate(headers):
        table.cell(0, idx).text = text

    if rows:
        for r_idx, row in enumerate(rows, start=1):
            table.cell(r_idx, 0).text = row["requirement_id"]
            table.cell(r_idx, 1).text = row["status"]
            table.cell(r_idx, 2).text = row["severity"]
            table.cell(r_idx, 3).text = row["section"]
            table.cell(r_idx, 4).text = row["notes"]
    else:
        table.cell(1, 0).text = "N/A"
        table.cell(1, 1).text = "Covered"
        table.cell(1, 2).text = "none"
        table.cell(1, 3).text = "N/A"
        table.cell(1, 4).text = "No compliance issues detected."

    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()
