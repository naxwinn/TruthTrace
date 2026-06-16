"""
PDF Report Generator
Produces a downloadable forensic analysis report.
"""

from pathlib import Path
from datetime import datetime
from fpdf import FPDF
from typing import List, Optional


class ForensicReportPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, "TruthTrace - Media Forensic Analysis Report", align="L")
        self.ln(4)
        self.set_draw_color(0, 180, 120)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}} | Generated {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", align="C")


def generate_report_pdf(
    filename: str,
    duration: Optional[float],
    file_size: int,
    mime_type: str,
    authenticity_score: float,
    findings: List[dict],
    incidents: List[dict],
    output_path: str,
) -> str:
    """Generate a PDF forensic report and save to output_path."""
    pdf = ForensicReportPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(0, 12, "Forensic Analysis Report", ln=True)
    pdf.ln(4)

    # Executive Summary
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 10, "Executive Summary", ln=True)
    pdf.ln(2)

    # Verdict
    score_pct = int(authenticity_score * 100)
    if authenticity_score >= 0.7:
        verdict = "AUTHENTIC"
        verdict_color = (0, 180, 120)
    elif authenticity_score >= 0.4:
        verdict = "SUSPICIOUS"
        verdict_color = (220, 160, 0)
    else:
        verdict = "TAMPERED"
        verdict_color = (220, 50, 50)

    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(*verdict_color)
    pdf.cell(0, 10, f"Verdict: {verdict} (Authenticity: {score_pct}%)", ln=True)
    pdf.ln(2)

    pdf.set_text_color(60, 60, 60)
    pdf.set_font("Helvetica", "", 10)

    high_findings = [f for f in findings if f.get("confidence", 0) >= 0.7]
    med_findings = [f for f in findings if 0.5 <= f.get("confidence", 0) < 0.7]

    summary_lines = [
        f"Total findings: {len(findings)}",
        f"High confidence: {len(high_findings)}",
        f"Medium confidence: {len(med_findings)}",
        f"Correlated incidents: {len(incidents)}",
    ]
    for line in summary_lines:
        pdf.cell(0, 6, line, ln=True)
    pdf.ln(4)

    # File Information
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 10, "File Information", ln=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(60, 60, 60)
    info_lines = [
        f"Filename: {filename}",
        f"File size: {file_size / 1024 / 1024:.2f} MB",
        f"Type: {mime_type}",
        f"Duration: {_format_time(duration) if duration else 'N/A'}",
    ]
    for line in info_lines:
        pdf.cell(0, 6, line, ln=True)
    pdf.ln(6)

    # Findings
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 10, "Detailed Findings", ln=True)
    pdf.ln(2)

    if not findings:
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 6, "No tampering indicators detected.", ln=True)
    else:
        for i, f in enumerate(findings, 1):
            conf = f.get("confidence", 0)
            if conf >= 0.7:
                pdf.set_text_color(220, 50, 50)
                severity = "HIGH"
            elif conf >= 0.5:
                pdf.set_text_color(220, 160, 0)
                severity = "MEDIUM"
            else:
                pdf.set_text_color(180, 180, 0)
                severity = "LOW"

            pdf.set_font("Helvetica", "B", 10)
            finding_type = f.get("finding_type", "unknown").replace("_", " ").title()
            pdf.cell(0, 6, f"{i}. [{severity}] {finding_type} ({int(conf * 100)}%)", ln=True)

            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(80, 80, 80)

            desc = f.get("description", "")
            if desc:
                pdf.multi_cell(0, 5, f"   {desc}")

            start = f.get("start_time")
            end = f.get("end_time")
            if start is not None:
                time_str = f"   Time: {_format_time(start)}"
                if end is not None:
                    time_str += f" - {_format_time(end)}"
                pdf.cell(0, 5, time_str, ln=True)

            detector = f.get("detector_type", "")
            pdf.cell(0, 5, f"   Detector: {detector}", ln=True)
            pdf.ln(2)

    # Incidents (Correlation)
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 10, "Correlated Incidents", ln=True)
    pdf.ln(2)

    if not incidents:
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 6, "No correlated incidents.", ln=True)
    else:
        for inc in incidents:
            sev = inc.get("severity", "low").upper()
            if sev == "HIGH":
                pdf.set_text_color(220, 50, 50)
            elif sev == "MEDIUM":
                pdf.set_text_color(220, 160, 0)
            else:
                pdf.set_text_color(100, 100, 100)

            pdf.set_font("Helvetica", "B", 10)
            start_t = _format_time(inc.get("start_time", 0))
            end_t = _format_time(inc.get("end_time", 0))
            pdf.cell(0, 6, f"Incident #{inc.get('id', '?')} [{sev}] - {start_t} to {end_t}", ln=True)

            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(80, 80, 80)
            detectors = ", ".join(inc.get("detectors_involved", []))
            pdf.cell(0, 5, f"   Detectors: {detectors}", ln=True)
            pdf.cell(0, 5, f"   Confidence: {int(inc.get('confidence', 0) * 100)}%", ln=True)
            pdf.cell(0, 5, f"   Finding count: {inc.get('finding_count', 0)}", ln=True)
            pdf.ln(3)

    # Recommendations
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 10, "Recommendations", ln=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(60, 60, 60)

    recommendations = []
    if authenticity_score < 0.4:
        recommendations.append("CRITICAL: High probability of tampering. Manual expert review strongly recommended.")
    if high_findings:
        recommendations.append("Multiple high-confidence anomalies found. Cross-reference with original source material.")
    if incidents:
        high_inc = [i for i in incidents if i.get("severity") == "high"]
        if high_inc:
            recommendations.append(f"{len(high_inc)} high-severity incident(s) detected with multi-detector corroboration.")
    if not findings:
        recommendations.append("No tampering indicators detected. File appears authentic.")

    recommendations.append("Review the timeline visualization for temporal context of anomalies.")
    recommendations.append("This report is generated by automated analysis and should be reviewed by a qualified examiner.")

    for rec in recommendations:
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 6, f"  * {rec}")
        pdf.ln(2)

    # Save
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output))
    return str(output)


def _format_time(seconds: float) -> str:
    if seconds is None:
        return "N/A"
    m = int(seconds // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    if m > 0:
        return f"{m}:{s:02d}.{ms:03d}"
    return f"{s}.{ms:03d}s"
