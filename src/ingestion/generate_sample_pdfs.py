"""
generate_sample_pdfs.py

Generates synthetic PDF documents for the entitlement filtering demo.
All content is fictional and for demonstration purposes only.
No real customers, partners, users, or business data is included.
"""

import os
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT


SAMPLE_DOCS_DIR = Path(__file__).parent.parent.parent / "sample-docs"


def build_styles():
    """Create custom styles for the demo PDFs."""
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="DemoTitle",
        parent=styles["Title"],
        fontSize=20,
        textColor=colors.HexColor("#1a3a5c"),
        spaceAfter=12
    ))
    styles.add(ParagraphStyle(
        name="DemoHeading1",
        parent=styles["Heading1"],
        fontSize=14,
        textColor=colors.HexColor("#1a3a5c"),
        spaceBefore=16,
        spaceAfter=8
    ))
    styles.add(ParagraphStyle(
        name="DemoHeading2",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=colors.HexColor("#2e6da4"),
        spaceBefore=12,
        spaceAfter=6
    ))
    styles.add(ParagraphStyle(
        name="DemoBody",
        parent=styles["BodyText"],
        fontSize=10,
        spaceAfter=6,
        leading=14
    ))
    styles.add(ParagraphStyle(
        name="DemoNote",
        parent=styles["BodyText"],
        fontSize=9,
        textColor=colors.HexColor("#888888"),
        spaceAfter=4,
        leading=12
    ))
    return styles


def disclaimer_paragraph(styles):
    return Paragraph(
        "⚠ DEMO ONLY — All names, numbers, and data in this document are entirely fictional "
        "and do not represent any real organization, customer, partner, or business.",
        ParagraphStyle(
            name="Disclaimer",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.HexColor("#cc0000"),
            backColor=colors.HexColor("#fff0f0"),
            borderPadding=4,
            spaceAfter=12
        )
    )


def generate_partner_alpha_client_north_overview():
    """PartnerAlpha | ClientNorth | ProductLineA | RegionOne | RestrictedDemo"""
    path = SAMPLE_DOCS_DIR / "partner-alpha-client-north-overview.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=inch, leftMargin=inch,
                            topMargin=inch, bottomMargin=inch)
    styles = build_styles()
    story = []

    story.append(Paragraph("Partner Alpha — Client North Overview", styles["DemoTitle"]))
    story.append(Paragraph("Product Line A | Region One | Fiscal Period Demo-Q1", styles["DemoNote"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a3a5c")))
    story.append(Spacer(1, 8))
    story.append(disclaimer_paragraph(styles))

    story.append(Paragraph("Executive Summary", styles["DemoHeading1"]))
    story.append(Paragraph(
        "This document provides a quarterly overview of the PartnerAlpha engagement with ClientNorth "
        "for ProductLineA across RegionOne. The relationship has maintained a steady operational cadence "
        "with key milestones achieved in service delivery, support resolution, and product adoption. "
        "All figures presented are synthetic and designed for demonstration purposes only.",
        styles["DemoBody"]
    ))

    story.append(Paragraph("Product Adoption Metrics", styles["DemoHeading2"]))
    data = [
        ["Metric", "Demo Value", "Trend"],
        ["Active Licenses", "1,250", "▲ 8%"],
        ["Module Utilization Rate", "74%", "▲ 3%"],
        ["Support Ticket Volume", "42", "▼ 12%"],
        ["Average Resolution Time", "1.8 days", "▼ 0.4 days"],
    ]
    table = Table(data, colWidths=[2.5 * inch, 2 * inch, 1.5 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Implementation Status — ProductLineA", styles["DemoHeading2"]))
    story.append(Paragraph(
        "The ProductLineA implementation for ClientNorth in RegionOne is currently in Phase 2 of a "
        "three-phase rollout. Phase 1 core module deployment was completed on schedule. Phase 2 covers "
        "advanced configuration, user onboarding, and integration with ClientNorth's internal workflows. "
        "Phase 3 will deliver reporting dashboards and performance monitoring capabilities.",
        styles["DemoBody"]
    ))

    story.append(Paragraph("Operational Observations", styles["DemoHeading2"]))
    story.append(Paragraph(
        "RegionOne operations have been stable with no critical incidents in the demo review period. "
        "Three minor configuration adjustments were made in response to user feedback collected via "
        "the standard support intake process. All adjustments were completed within the agreed SLA window.",
        styles["DemoBody"]
    ))

    story.append(Paragraph("Upcoming Milestones", styles["DemoHeading1"]))
    milestones = [
        ("Demo-Q2 Week 2", "Phase 2 configuration review and sign-off"),
        ("Demo-Q2 Week 4", "User onboarding workshop for ClientNorth team"),
        ("Demo-Q3 Week 1", "Phase 3 kickoff — reporting module deployment"),
        ("Demo-Q3 Week 6", "Final acceptance testing and go-live"),
    ]
    for date, milestone in milestones:
        story.append(Paragraph(f"• <b>{date}</b>: {milestone}", styles["DemoBody"]))

    story.append(Spacer(1, 16))
    story.append(Paragraph(
        "Document Classification: RestrictedDemo | Entitlements: PartnerAlpha, ClientNorth, ProductLineA, RegionOne",
        styles["DemoNote"]
    ))

    doc.build(story)
    print(f"  ✓ Generated: {path.name}")


def generate_partner_alpha_client_south_product_line_a_summary():
    """PartnerAlpha | ClientSouth | ProductLineA | RegionOne | RestrictedDemo"""
    path = SAMPLE_DOCS_DIR / "partner-alpha-client-south-product-line-a-summary.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=inch, leftMargin=inch,
                            topMargin=inch, bottomMargin=inch)
    styles = build_styles()
    story = []

    story.append(Paragraph("Partner Alpha — Client South Product Line A Summary", styles["DemoTitle"]))
    story.append(Paragraph("Product Line A | Region One | Demo Period Summary", styles["DemoNote"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a3a5c")))
    story.append(Spacer(1, 8))
    story.append(disclaimer_paragraph(styles))

    story.append(Paragraph("Product Line A — ClientSouth Deployment Summary", styles["DemoHeading1"]))
    story.append(Paragraph(
        "This document summarizes the ProductLineA deployment status for ClientSouth under the "
        "PartnerAlpha partnership in RegionOne. The engagement has progressed through initial "
        "onboarding and is now in full production operation.",
        styles["DemoBody"]
    ))

    story.append(Paragraph("Key Performance Indicators", styles["DemoHeading2"]))
    data = [
        ["KPI", "Target (Demo)", "Actual (Demo)", "Status"],
        ["System Uptime", "99.5%", "99.7%", "✓ Met"],
        ["User Adoption", "80%", "76%", "⚠ At Risk"],
        ["Batch Processing Volume", "5,000/day", "4,850/day", "✓ Met"],
        ["Error Rate", "<0.5%", "0.3%", "✓ Met"],
    ]
    table = Table(data, colWidths=[2 * inch, 1.5 * inch, 1.5 * inch, 1 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2e6da4")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Risk Register", styles["DemoHeading2"]))
    story.append(Paragraph(
        "User adoption for ClientSouth is currently tracking below the 80% target. The PartnerAlpha "
        "team has identified that additional training sessions are required for the ClientSouth "
        "administrative users. A targeted enablement plan has been prepared and will be executed "
        "in the next two weeks. No other active risks are present at this time.",
        styles["DemoBody"]
    ))

    story.append(Paragraph("Recommendations", styles["DemoHeading1"]))
    for rec in [
        "Schedule two additional ProductLineA training sessions for ClientSouth administrators.",
        "Review integration touchpoints between ProductLineA and ClientSouth's existing workflow tools.",
        "Confirm RegionOne data residency compliance documentation is up to date.",
    ]:
        story.append(Paragraph(f"• {rec}", styles["DemoBody"]))

    story.append(Spacer(1, 16))
    story.append(Paragraph(
        "Document Classification: RestrictedDemo | Entitlements: PartnerAlpha, ClientSouth, ProductLineA, RegionOne",
        styles["DemoNote"]
    ))

    doc.build(story)
    print(f"  ✓ Generated: {path.name}")


def generate_partner_beta_client_east_operational_review():
    """PartnerBeta | ClientEast | ProductLineB | RegionTwo | RestrictedDemo"""
    path = SAMPLE_DOCS_DIR / "partner-beta-client-east-operational-review.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=inch, leftMargin=inch,
                            topMargin=inch, bottomMargin=inch)
    styles = build_styles()
    story = []

    story.append(Paragraph("Partner Beta — Client East Operational Review", styles["DemoTitle"]))
    story.append(Paragraph("Product Line B | Region Two | Demo Operational Period", styles["DemoNote"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a3a5c")))
    story.append(Spacer(1, 8))
    story.append(disclaimer_paragraph(styles))

    story.append(Paragraph("Operational Review Summary", styles["DemoHeading1"]))
    story.append(Paragraph(
        "This operational review covers the PartnerBeta engagement with ClientEast for ProductLineB "
        "in RegionTwo. The review period reflects the operational baseline established following "
        "the initial deployment and includes an analysis of service performance, incident history, "
        "and forward-looking operational considerations.",
        styles["DemoBody"]
    ))

    story.append(Paragraph("Service Performance", styles["DemoHeading2"]))
    data = [
        ["Service Component", "Availability (Demo)", "Incidents (Demo)"],
        ["Core Processing Engine", "99.8%", "0 Critical"],
        ["Integration Middleware", "99.1%", "1 Minor"],
        ["Reporting Module", "98.6%", "2 Minor"],
        ["User Authentication Gateway", "99.9%", "0"],
    ]
    table = Table(data, colWidths=[2.5 * inch, 2 * inch, 1.5 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Incident Analysis", styles["DemoHeading2"]))
    story.append(Paragraph(
        "The two minor incidents in the Reporting Module were related to a scheduled maintenance "
        "window that ran longer than the planned duration. No data integrity issues were identified. "
        "The integration middleware incident was caused by a transient network event in RegionTwo "
        "and was resolved within the SLA window. Root cause analysis is complete.",
        styles["DemoBody"]
    ))

    story.append(Paragraph("ProductLineB Capacity Planning", styles["DemoHeading2"]))
    story.append(Paragraph(
        "Current utilization in RegionTwo is at 68% of provisioned capacity. Projections for the "
        "next demo period indicate potential growth to 82% utilization based on ClientEast's "
        "anticipated transaction volume increase. The PartnerBeta team recommends initiating a "
        "capacity review in advance of the next quarter to ensure headroom is available.",
        styles["DemoBody"]
    ))

    story.append(Spacer(1, 16))
    story.append(Paragraph(
        "Document Classification: RestrictedDemo | Entitlements: PartnerBeta, ClientEast, ProductLineB, RegionTwo",
        styles["DemoNote"]
    ))

    doc.build(story)
    print(f"  ✓ Generated: {path.name}")


def generate_shared_global_reference_guide():
    """Global | PublicDemoReference — accessible to all authorized demo users."""
    path = SAMPLE_DOCS_DIR / "shared-global-reference-guide.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=inch, leftMargin=inch,
                            topMargin=inch, bottomMargin=inch)
    styles = build_styles()
    story = []

    story.append(Paragraph("Shared Global Reference Guide", styles["DemoTitle"]))
    story.append(Paragraph("Classification: PublicDemoReference | Available to all authorized users", styles["DemoNote"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a3a5c")))
    story.append(Spacer(1, 8))
    story.append(disclaimer_paragraph(styles))

    story.append(Paragraph("About This Guide", styles["DemoHeading1"]))
    story.append(Paragraph(
        "This shared reference guide is available to all authorized users regardless of partner, "
        "client, product line, or region affiliation. It contains generic process guidance, "
        "support protocols, and reference standards that apply broadly across all engagements. "
        "This document is classified as PublicDemoReference.",
        styles["DemoBody"]
    ))

    story.append(Paragraph("Support Process Overview", styles["DemoHeading2"]))
    story.append(Paragraph(
        "All support requests should be submitted through the standard intake form. Requests are "
        "triaged within one business day and assigned a priority level based on business impact "
        "and urgency. Critical incidents receive immediate escalation. Minor requests are "
        "addressed within five business days.",
        styles["DemoBody"]
    ))

    story.append(Paragraph("Priority Levels", styles["DemoHeading2"]))
    data = [
        ["Priority", "Description (Demo)", "Target Response"],
        ["P1 — Critical", "Service unavailable, data risk", "Within 1 hour"],
        ["P2 — High", "Major feature impaired", "Within 4 hours"],
        ["P3 — Medium", "Minor feature impaired", "Within 1 business day"],
        ["P4 — Low", "General inquiry or enhancement", "Within 5 business days"],
    ]
    table = Table(data, colWidths=[1.5 * inch, 2.5 * inch, 2 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2e6da4")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Standard Escalation Path", styles["DemoHeading2"]))
    for step in [
        "Step 1: Submit ticket via standard intake channel.",
        "Step 2: Triage team acknowledges within SLA window.",
        "Step 3: Issue is assigned to appropriate support tier.",
        "Step 4: Updates provided at defined intervals until resolution.",
        "Step 5: Post-resolution follow-up and satisfaction confirmation.",
    ]:
        story.append(Paragraph(f"• {step}", styles["DemoBody"]))

    story.append(Paragraph("Reference Data Standards", styles["DemoHeading1"]))
    story.append(Paragraph(
        "All reporting and data exchange follows the standard format specifications documented "
        "in the Data Exchange Reference (DER-001). Date formats use ISO 8601. Identifiers follow "
        "the standard entity reference scheme. Currency values are expressed in the operating "
        "currency of the relevant engagement unless otherwise specified.",
        styles["DemoBody"]
    ))

    story.append(Spacer(1, 16))
    story.append(Paragraph(
        "Document Classification: PublicDemoReference | Available to all authorized users",
        styles["DemoNote"]
    ))

    doc.build(story)
    print(f"  ✓ Generated: {path.name}")


def generate_restricted_client_north_financial_summary():
    """PartnerAlpha | ClientNorth | ProductLineA | RegionOne | RestrictedDemo"""
    path = SAMPLE_DOCS_DIR / "restricted-client-north-financial-summary.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=inch, leftMargin=inch,
                            topMargin=inch, bottomMargin=inch)
    styles = build_styles()
    story = []

    story.append(Paragraph("Restricted: Client North Financial Summary", styles["DemoTitle"]))
    story.append(Paragraph("PartnerAlpha | ClientNorth | ProductLineA | RegionOne | RESTRICTED DEMO", styles["DemoNote"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cc0000")))
    story.append(Spacer(1, 8))
    story.append(disclaimer_paragraph(styles))

    story.append(Paragraph(
        "⚠ This document contains restricted financial information for ClientNorth. "
        "Access is limited to authorized PartnerAlpha personnel with ClientNorth entitlements.",
        ParagraphStyle(
            name="Warning",
            parent=styles["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#cc0000"),
            spaceAfter=12
        )
    ))

    story.append(Paragraph("Synthetic Financial Overview", styles["DemoHeading1"]))
    story.append(Paragraph(
        "The following figures are entirely fabricated and are provided solely to demonstrate "
        "the entitlement filtering pattern. These numbers do not represent any real financial "
        "performance, forecast, or position.",
        styles["DemoBody"]
    ))

    story.append(Paragraph("Demo Revenue Summary (Synthetic Numbers Only)", styles["DemoHeading2"]))
    data = [
        ["Category", "Demo Q1", "Demo Q2", "Demo Q3 Forecast"],
        ["ProductLineA Services", "$1,240,000", "$1,380,000", "$1,450,000"],
        ["Support & Maintenance", "$180,000", "$195,000", "$200,000"],
        ["Professional Services", "$340,000", "$290,000", "$310,000"],
        ["Total (Demo)", "$1,760,000", "$1,865,000", "$1,960,000"],
    ]
    table = Table(data, colWidths=[2 * inch, 1.4 * inch, 1.4 * inch, 1.6 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#8b0000")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#fff5f5")]),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#ffe0e0")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Budget Utilization", styles["DemoHeading2"]))
    story.append(Paragraph(
        "ProductLineA investment for ClientNorth in RegionOne is tracking within the approved "
        "demo budget envelope. Professional services spend is slightly below forecast due to "
        "timeline adjustments in Phase 2. No budget exceptions have been raised. The remaining "
        "demo period budget is sufficient to complete Phase 3 as planned.",
        styles["DemoBody"]
    ))

    story.append(Spacer(1, 16))
    story.append(Paragraph(
        "Document Classification: RestrictedDemo | Entitlements: PartnerAlpha, ClientNorth, ProductLineA, RegionOne",
        styles["DemoNote"]
    ))

    doc.build(story)
    print(f"  ✓ Generated: {path.name}")


def generate_restricted_client_east_implementation_notes():
    """PartnerBeta | ClientEast | ProductLineB | RegionTwo | RestrictedDemo"""
    path = SAMPLE_DOCS_DIR / "restricted-client-east-implementation-notes.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=inch, leftMargin=inch,
                            topMargin=inch, bottomMargin=inch)
    styles = build_styles()
    story = []

    story.append(Paragraph("Restricted: Client East Implementation Notes", styles["DemoTitle"]))
    story.append(Paragraph("PartnerBeta | ClientEast | ProductLineB | RegionTwo | RESTRICTED DEMO", styles["DemoNote"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cc0000")))
    story.append(Spacer(1, 8))
    story.append(disclaimer_paragraph(styles))

    story.append(Paragraph(
        "⚠ This document contains restricted implementation notes for ClientEast. "
        "Access is limited to authorized PartnerBeta personnel with ClientEast entitlements.",
        ParagraphStyle(
            name="Warning",
            parent=styles["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#cc0000"),
            spaceAfter=12
        )
    ))

    story.append(Paragraph("ProductLineB Implementation Architecture", styles["DemoHeading1"]))
    story.append(Paragraph(
        "The ProductLineB implementation for ClientEast in RegionTwo uses a three-tier "
        "architecture pattern. The presentation tier handles user interaction, the processing "
        "tier manages business logic and workflow orchestration, and the data tier provides "
        "persistent storage and reporting capabilities. All tiers are deployed within "
        "RegionTwo to satisfy data residency requirements.",
        styles["DemoBody"]
    ))

    story.append(Paragraph("Integration Points", styles["DemoHeading2"]))
    data = [
        ["Integration", "Protocol (Demo)", "Frequency", "Status"],
        ["ClientEast Identity Provider", "SAML 2.0", "Per session", "Active"],
        ["Inventory Management System", "REST API", "Every 15 min", "Active"],
        ["Financial Reporting Platform", "SFTP (batch)", "Daily 02:00", "Active"],
        ["Legacy Workflow Engine", "Message Queue", "Near real-time", "Pending Migration"],
    ]
    table = Table(data, colWidths=[2 * inch, 1.5 * inch, 1.5 * inch, 1.2 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Known Constraints", styles["DemoHeading2"]))
    for constraint in [
        "Legacy Workflow Engine integration requires migration to message queue protocol before Demo-Q4.",
        "RegionTwo data residency compliance requires all processing to remain within the RegionTwo boundary.",
        "ClientEast Identity Provider supports SAML 2.0 only; OAuth migration is planned for a future phase.",
    ]:
        story.append(Paragraph(f"• {constraint}", styles["DemoBody"]))

    story.append(Paragraph("Configuration Notes", styles["DemoHeading2"]))
    story.append(Paragraph(
        "ProductLineB configuration for ClientEast includes custom workflow rules specific to "
        "ClientEast's operational requirements. These configuration items are documented in "
        "the Configuration Baseline Record (CBR-ClientEast-001) maintained by the PartnerBeta "
        "technical team. Any changes to these configurations require change advisory board approval.",
        styles["DemoBody"]
    ))

    story.append(Spacer(1, 16))
    story.append(Paragraph(
        "Document Classification: RestrictedDemo | Entitlements: PartnerBeta, ClientEast, ProductLineB, RegionTwo",
        styles["DemoNote"]
    ))

    doc.build(story)
    print(f"  ✓ Generated: {path.name}")


def main():
    SAMPLE_DOCS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\nGenerating synthetic demo PDFs in: {SAMPLE_DOCS_DIR}\n")

    generators = [
        generate_partner_alpha_client_north_overview,
        generate_partner_alpha_client_south_product_line_a_summary,
        generate_partner_beta_client_east_operational_review,
        generate_shared_global_reference_guide,
        generate_restricted_client_north_financial_summary,
        generate_restricted_client_east_implementation_notes,
    ]

    for gen in generators:
        try:
            gen()
        except Exception as e:
            print(f"  ✗ Error generating {gen.__name__}: {e}")
            raise

    print(f"\n✓ Generated {len(generators)} synthetic PDF files in {SAMPLE_DOCS_DIR}")
    print("\nAll content is fictional and for demonstration purposes only.")


if __name__ == "__main__":
    main()
