"""
PDF generation service for battlecards
Creates professionally formatted PDF battlecards for export
"""
from typing import Dict, List, Optional
from io import BytesIO
from datetime import datetime
from loguru import logger

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, Image, HRFlowable
    )
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("ReportLab not installed. PDF generation disabled.")


class PDFGenerator:
    """Generate professional PDF battlecards"""
    
    def __init__(self):
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab is required for PDF generation. Install with: pip install reportlab")
        
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Create custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='BattlecardTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a365d'),
            spaceAfter=20,
            alignment=TA_CENTER
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2b6cb0'),
            spaceBefore=15,
            spaceAfter=10,
            borderPadding=5,
            backColor=colors.HexColor('#ebf8ff')
        ))
        
        # Body text style
        self.styles.add(ParagraphStyle(
            name='BodyText',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#2d3748'),
            alignment=TA_JUSTIFY,
            spaceAfter=8
        ))
        
        # Bullet style
        self.styles.add(ParagraphStyle(
            name='BulletPoint',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#4a5568'),
            leftIndent=20,
            bulletIndent=10,
            spaceAfter=4
        ))
        
        # Kill point style (highlighted)
        self.styles.add(ParagraphStyle(
            name='KillPoint',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#22543d'),
            backColor=colors.HexColor('#c6f6d5'),
            leftIndent=20,
            rightIndent=10,
            spaceBefore=4,
            spaceAfter=4,
            borderPadding=5
        ))
    
    def generate_battlecard_pdf(self, battlecard: Dict) -> BytesIO:
        """Generate PDF for a battlecard"""
        buffer = BytesIO()
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        story = []
        
        # Header
        story.append(Paragraph(
            f"Competitive Battlecard",
            self.styles['BattlecardTitle']
        ))
        story.append(Paragraph(
            f"<b>{battlecard.get('competitor_name', battlecard.get('title', 'Unknown'))}</b>",
            self.styles['Heading1']
        ))
        story.append(Spacer(1, 10))
        
        # Metadata
        meta_data = [
            ['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M')],
            ['Confidence Score:', f"{battlecard.get('confidence_score', 'N/A')}"],
            ['Last Updated:', battlecard.get('updated_at', 'N/A')]
        ]
        meta_table = Table(meta_data, colWidths=[1.5*inch, 3*inch])
        meta_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.gray),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 20))
        
        # Horizontal line
        story.append(HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor('#e2e8f0'),
            spaceAfter=15
        ))
        
        # Overview Section
        if battlecard.get('overview'):
            story.append(Paragraph("📋 Overview", self.styles['SectionHeader']))
            story.append(Paragraph(battlecard['overview'], self.styles['BodyText']))
            story.append(Spacer(1, 10))
        
        # Strengths Section
        if battlecard.get('strengths'):
            story.append(Paragraph("💪 Competitor Strengths", self.styles['SectionHeader']))
            for strength in battlecard['strengths']:
                story.append(Paragraph(
                    f"• {strength}",
                    self.styles['BulletPoint']
                ))
            story.append(Spacer(1, 10))
        
        # Weaknesses Section
        if battlecard.get('weaknesses'):
            story.append(Paragraph("⚠️ Competitor Weaknesses", self.styles['SectionHeader']))
            for weakness in battlecard['weaknesses']:
                story.append(Paragraph(
                    f"• {weakness}",
                    self.styles['BulletPoint']
                ))
            story.append(Spacer(1, 10))
        
        # Kill Points Section (Highlighted)
        if battlecard.get('kill_points'):
            story.append(Paragraph("🎯 Why We Win (Kill Points)", self.styles['SectionHeader']))
            for point in battlecard['kill_points']:
                story.append(Paragraph(
                    f"✓ {point}",
                    self.styles['KillPoint']
                ))
            story.append(Spacer(1, 10))
        
        # Objection Handlers Section
        if battlecard.get('objection_handlers'):
            story.append(PageBreak())
            story.append(Paragraph("🗣️ Objection Handling", self.styles['SectionHeader']))
            
            for handler in battlecard['objection_handlers']:
                story.append(Paragraph(
                    f"<b>Objection:</b> {handler.get('objection', 'N/A')}",
                    self.styles['BodyText']
                ))
                story.append(Paragraph(
                    f"<b>Response:</b> {handler.get('response', 'N/A')}",
                    self.styles['BulletPoint']
                ))
                story.append(Spacer(1, 8))
        
        # Pricing Comparison Section
        if battlecard.get('pricing_comparison'):
            story.append(Paragraph("💰 Pricing Comparison", self.styles['SectionHeader']))
            
            pricing = battlecard['pricing_comparison']
            if isinstance(pricing, list):
                pricing_data = [['Plan', 'Competitor Price', 'Our Price', 'Difference']]
                for plan in pricing:
                    pricing_data.append([
                        plan.get('name', 'N/A'),
                        plan.get('competitor_price', 'N/A'),
                        plan.get('our_price', 'N/A'),
                        plan.get('difference', 'N/A')
                    ])
                
                pricing_table = Table(pricing_data, colWidths=[1.5*inch, 1.3*inch, 1.3*inch, 1.3*inch])
                pricing_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2b6cb0')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')])
                ]))
                story.append(pricing_table)
                story.append(Spacer(1, 15))
        
        # Recent Updates Section
        if battlecard.get('recent_updates'):
            story.append(Paragraph("📰 Recent Competitor Updates", self.styles['SectionHeader']))
            for update in battlecard['recent_updates'][:5]:
                story.append(Paragraph(
                    f"• <b>{update.get('date', 'N/A')}:</b> {update.get('summary', 'N/A')}",
                    self.styles['BulletPoint']
                ))
            story.append(Spacer(1, 10))
        
        # Footer
        story.append(Spacer(1, 30))
        story.append(HRFlowable(
            width="100%",
            thickness=0.5,
            color=colors.HexColor('#cbd5e0'),
            spaceAfter=10
        ))
        story.append(Paragraph(
            "Generated by VigilAI - Competitive Intelligence Platform",
            ParagraphStyle(
                name='Footer',
                fontSize=8,
                textColor=colors.gray,
                alignment=TA_CENTER
            )
        ))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        return buffer
    
    def generate_comparison_pdf(self, competitors: List[Dict]) -> BytesIO:
        """Generate a multi-competitor comparison PDF"""
        buffer = BytesIO()
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        
        story = []
        
        # Title
        story.append(Paragraph(
            "Competitive Landscape Overview",
            self.styles['BattlecardTitle']
        ))
        story.append(Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d')}",
            ParagraphStyle(name='Date', fontSize=10, alignment=TA_CENTER, textColor=colors.gray)
        ))
        story.append(Spacer(1, 30))
        
        # Comparison table
        headers = ['Competitor', 'Key Strength', 'Key Weakness', 'Win Rate']
        table_data = [headers]
        
        for comp in competitors:
            row = [
                comp.get('name', 'Unknown'),
                comp.get('top_strength', 'N/A'),
                comp.get('top_weakness', 'N/A'),
                f"{comp.get('win_rate', 'N/A')}%"
            ]
            table_data.append(row)
        
        comparison_table = Table(table_data, colWidths=[1.5*inch, 2*inch, 2*inch, 1*inch])
        comparison_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(comparison_table)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        return buffer


# Singleton instance
pdf_generator = None

def get_pdf_generator() -> PDFGenerator:
    """Get or create PDF generator instance"""
    global pdf_generator
    if pdf_generator is None:
        pdf_generator = PDFGenerator()
    return pdf_generator
