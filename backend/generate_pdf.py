# Save this file as generate_pdf.py and run: pip install reportlab
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """Adds 'Page X of Y' on every page for citation/page testing."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawString(54, 36, "CONFIDENTIAL - TEST MASTER SERVICES AGREEMENT")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 54, 36, page_str)
        self.restoreState()

def create_contract_pdf(output_path="sample_master_services_agreement.pdf"):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        alignment=1,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=12
    )

    h2_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'ContractBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6
    )

    story = [
        Paragraph("MASTER SERVICES AGREEMENT", title_style),
        HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0f172a"), spaceAfter=10),
        Paragraph(
            "This Master Services Agreement (\"Agreement\") is entered into as of October 15, 2024 (\"Effective Date\"), "
            "by and between <b>Apex Cloud Solutions LLC</b>, a Delaware limited liability company with its principal office "
            "at 100 Market St, Suite 400, San Francisco, CA (\"Provider\"), and <b>Vanguard Retail Enterprises Inc.</b>, "
            "a New York corporation with offices at 500 5th Avenue, New York, NY (\"Client\").",
            body_style
        ),
        Spacer(1, 8),

        Paragraph("Section 1: Scope of Services &amp; Deliverables", h2_style),
        Paragraph("1.1 Provider agrees to perform the digital transformation, database migration, and cloud maintenance services described in individual Statements of Work (\"SOW\") executed under this Agreement.", body_style),
        Paragraph("1.2 Provider shall use commercially reasonable efforts to deliver the deliverables in accordance with the milestones outlined in each SOW. Any estimated timelines or roadmaps provided verbally or in slide decks are non-binding projections.", body_style),

        Paragraph("Section 2: Fees, Invoicing, and Payment Terms", h2_style),
        Paragraph("2.1 Client shall pay Provider the fees set forth in the applicable SOW. All invoices are due and payable within thirty (30) days from the invoice date.", body_style),
        Paragraph("2.2 Past due balances will accrue interest at the rate of one and a half percent (1.5%) per month or the maximum rate permitted by law, whichever is higher, plus all reasonable collection costs and legal fees.", body_style),
        Paragraph("2.3 Provider reserves the right to suspend all services and withhold deliverables if an invoice remains unpaid for more than fifteen (15) business days past its due date.", body_style),

        Paragraph("Section 3: Term and Automatic Renewal", h2_style),
        Paragraph("3.1 This Agreement commences on the Effective Date and continues for an initial period of twenty-four (24) months (\"Initial Term\").", body_style),
        Paragraph("3.2 Upon expiration of the Initial Term, this Agreement shall automatically renew for successive terms of twenty-four (24) months each, unless Client provides written notice of non-renewal via certified registered mail at least ninety (90) days prior to the expiration of the then-current term. Notice sent via email is explicitly considered invalid for non-renewal.", body_style),

        Paragraph("Section 4: Termination &amp; Suspension", h2_style),
        Paragraph("4.1 Either party may terminate this Agreement immediately if the other party breaches any material term and fails to cure such breach within forty-five (45) days of receiving written notice.", body_style),
        Paragraph("4.2 Provider may terminate this Agreement for convenience at any time upon thirty (30) days' prior written notice to Client. Client shall not be entitled to terminate this Agreement for convenience prior to the expiration of the full term.", body_style),
        Paragraph("4.3 Upon termination for any reason, Client shall immediately pay Provider for all services completed, work-in-progress, and any non-cancelable third-party commitments incurred by Provider.", body_style),

        Paragraph("Section 5: Confidentiality and Proprietary Information", h2_style),
        Paragraph("5.1 \"Confidential Information\" means any proprietary information disclosed by one party (\"Disclosing Party\") to the other (\"Receiving Party\"), whether orally or in writing, that is designated as confidential or reasonably understood to be confidential.", body_style),
        Paragraph("5.2 Receiving Party agrees to protect Confidential Information with the same degree of care it uses for its own sensitive data, but no less than reasonable care.", body_style),
        Paragraph("5.3 Exclusions: Confidential Information does not include information that: (a) is or becomes publicly known through no breach of this Agreement; (b) was already known to Receiving Party without obligation of confidentiality; or (c) is independently developed without reference to Disclosing Party's Confidential Information. Provider reserves the right to use aggregated, anonymized telemetry and architectural benchmarks derived from Client data for model training and platform improvement.", body_style),

        Paragraph("Section 6: Intellectual Property Rights", h2_style),
        Paragraph("6.1 Client shall own all right, title, and interest in and to the custom end-user deliverables specifically commissioned and fully paid for under a SOW (\"Client Deliverables\").", body_style),
        Paragraph("6.2 Provider retains sole ownership of all pre-existing tools, algorithms, libraries, APIs, and proprietary code bases used to create the Deliverables (\"Provider IP\"). Provider grants Client a limited, non-exclusive, non-transferable, revocable license to utilize Provider IP solely as embedded within the delivered solution.", body_style),

        Paragraph("Section 7: Indemnification (One-Way / Non-Standard)", h2_style),
        Paragraph("7.1 Client agrees to defend, indemnify, and hold harmless Provider, its affiliates, directors, officers, employees, and subcontractors against any and all claims, liabilities, losses, damages, penalties, costs, and expenses (including uncapped attorneys' fees and litigation expenses) arising out of or related to: (a) Any breach of this Agreement by Client; (b) Any third-party claim alleging that Client-provided data or materials infringe any intellectual property or privacy right; or (c) Provider's compliance with any specification or instruction issued by Client.", body_style),
        Paragraph("7.2 Provider shall have no obligation to indemnify, defend, or hold harmless Client under any circumstances, including third-party IP infringement claims stemming from Provider's tools or code.", body_style),

        Paragraph("Section 8: Non-Solicitation and Exclusivity", h2_style),
        Paragraph("8.1 During the term of this Agreement and for a period of twenty-four (24) months following termination, Client shall not directly or indirectly solicit, recruit, employ, or contract with any employee, consultant, or subcontractor of Provider without Provider's express written consent.", body_style),
        Paragraph("8.2 In the event of a breach of Clause 8.1, Client agrees to pay Provider a liquidated damages sum equal to two hundred percent (200%) of the employee's annualized base salary.", body_style),

        Paragraph("Section 9: Governing Law and Dispute Resolution", h2_style),
        Paragraph("9.1 This Agreement shall be governed by, and construed in accordance with, the laws of the State of Delaware, without giving effect to conflict of laws principles.", body_style),
        Paragraph("9.2 Any dispute, controversy, or claim arising out of or relating to this contract shall be settled by binding arbitration in Dover, Delaware, administered by the American Arbitration Association (AAA) in accordance with its Commercial Arbitration Rules. Each party waives any right to a jury trial or class action proceedings.", body_style),

        Paragraph("Section 10: Miscellaneous", h2_style),
        Paragraph("10.1 Severability: If any provision of this Agreement is held invalid or unenforceable, the remaining provisions will remain in full force and effect.", body_style),
        Paragraph("10.2 Entire Agreement: This Agreement constitutes the complete and exclusive agreement between the parties and supersedes all prior negotiations, proposals, or understandings.", body_style),
    ]

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated test contract at: {output_path}")

if __name__ == "__main__":
    create_contract_pdf()