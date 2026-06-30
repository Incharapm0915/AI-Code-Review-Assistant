import os
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics import renderPDF


SEVERITY_COLORS = {
    'critical': colors.HexColor('#DC2626'),
    'high': colors.HexColor('#EA580C'),
    'medium': colors.HexColor('#D97706'),
    'low': colors.HexColor('#2563EB'),
    'info': colors.HexColor('#6B7280'),
}

GRADE_COLORS = {
    'A': colors.HexColor('#10B981'),
    'B': colors.HexColor('#3B82F6'),
    'C': colors.HexColor('#F59E0B'),
    'D': colors.HexColor('#EF4444'),
    'F': colors.HexColor('#DC2626'),
}


class ReportGenerator:

    def generate_pdf(self, report_data: dict, output_path: str, user_info: dict = None) -> str:
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch
        )

        styles = self._build_styles()
        story = []

        story.extend(self._build_header(styles, report_data, user_info))
        story.append(Spacer(1, 0.3 * inch))

        story.extend(self._build_summary_section(styles, report_data))
        story.append(Spacer(1, 0.2 * inch))

        story.extend(self._build_scores_section(styles, report_data))
        story.append(Spacer(1, 0.2 * inch))

        story.extend(self._build_metrics_section(styles, report_data))
        story.append(PageBreak())

        story.extend(self._build_issues_section(styles, report_data))
        story.append(Spacer(1, 0.2 * inch))

        story.extend(self._build_vulnerabilities_section(styles, report_data))
        story.append(Spacer(1, 0.2 * inch))

        story.extend(self._build_suggestions_section(styles, report_data))

        story.extend(self._build_footer(styles))

        doc.build(story)
        return output_path

    def _build_styles(self):
        styles = getSampleStyleSheet()

        styles.add(ParagraphStyle(
            name='RptTitle',
            fontSize=24,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#1E293B'),
            alignment=TA_CENTER,
            spaceAfter=6
        ))
        styles.add(ParagraphStyle(
            name='RptSubtitle',
            fontSize=12,
            fontName='Helvetica',
            textColor=colors.HexColor('#64748B'),
            alignment=TA_CENTER,
            spaceAfter=12
        ))
        styles.add(ParagraphStyle(
            name='SectionHeader',
            fontSize=14,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#1E293B'),
            spaceBefore=12,
            spaceAfter=6,
            borderPad=4
        ))
        styles.add(ParagraphStyle(
            name='RptBody',
            fontSize=10,
            fontName='Helvetica',
            textColor=colors.HexColor('#374151'),
            spaceAfter=4
        ))
        styles.add(ParagraphStyle(
            name='RptCode',
            fontSize=8,
            fontName='Courier',
            textColor=colors.HexColor('#1F2937'),
            backColor=colors.HexColor('#F3F4F6'),
            borderPad=4,
            spaceAfter=4
        ))
        styles.add(ParagraphStyle(
            name='RptCritical',
            fontSize=10,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#DC2626'),
            spaceAfter=2
        ))

        return styles

    def _build_header(self, styles, report_data, user_info):
        elements = []

        header_data = [
            [Paragraph('AI Code Review Report', styles['RptTitle'])],
            [Paragraph(f'Generated: {datetime.now().strftime("%B %d, %Y at %H:%M UTC")}', styles['RptSubtitle'])],
        ]
        if user_info:
            header_data.append([Paragraph(f'Developer: {user_info.get("username", "Unknown")}', styles['RptSubtitle'])])

        header_table = Table(header_data, colWidths=[6.5 * inch])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
            ('ROUNDEDCORNERS', [8]),
            ('TOPPADDING', (0, 0), (-1, -1), 16),
            ('BOTTOMPADDING', (0, -1), (-1, -1), 16),
            ('LEFTPADDING', (0, 0), (-1, -1), 20),
            ('RIGHTPADDING', (0, 0), (-1, -1), 20),
            ('LINEBELOW', (0, -1), (-1, -1), 2, colors.HexColor('#6366F1')),
        ]))
        elements.append(header_table)
        return elements

    def _build_summary_section(self, styles, report_data):
        elements = []
        elements.append(Paragraph('Executive Summary', styles['SectionHeader']))
        elements.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#E2E8F0')))
        elements.append(Spacer(1, 0.1 * inch))

        summary = report_data.get('summary', {})
        scores = report_data.get('scores', {})
        grade = scores.get('grade', 'N/A')
        grade_color = GRADE_COLORS.get(grade, colors.gray)

        summary_data = [
            ['Metric', 'Value'],
            ['Overall Grade', grade],
            ['Verdict', summary.get('verdict', 'N/A')],
            ['Total Issues', str(report_data.get('total_issues', 0))],
            ['Critical Issues', str(summary.get('critical_issues', 0))],
            ['Security Vulnerabilities', str(summary.get('vulnerabilities', 0))],
            ['Language', report_data.get('language', 'N/A').title()],
            ['Lines Analyzed', str(report_data.get('lines_analyzed', 0))],
        ]

        table = Table(summary_data, colWidths=[3 * inch, 3.5 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(table)

        elements.append(Spacer(1, 0.1 * inch))
        desc = summary.get('description', '')
        if desc:
            elements.append(Paragraph(f'<i>{desc}</i>', styles['RptBody']))

        return elements

    def _build_scores_section(self, styles, report_data):
        elements = []
        elements.append(Paragraph('Quality Scores', styles['SectionHeader']))
        elements.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#E2E8F0')))
        elements.append(Spacer(1, 0.1 * inch))

        scores = report_data.get('scores', {})
        score_data = [
            ['Category', 'Score', 'Rating'],
            ['Overall Quality', f"{scores.get('overall', 0)}/100", self._rate(scores.get('overall', 0))],
            ['Security', f"{scores.get('security', 0)}/100", self._rate(scores.get('security', 0))],
            ['Code Quality', f"{scores.get('quality', 0)}/100", self._rate(scores.get('quality', 0))],
            ['Complexity', f"{scores.get('complexity', 0)}/100", self._rate(scores.get('complexity', 0))],
            ['Maintainability', f"{scores.get('maintainability', 0)}/100", self._rate(scores.get('maintainability', 0))],
        ]

        table = Table(score_data, colWidths=[2.5 * inch, 2 * inch, 2 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(table)
        return elements

    def _build_metrics_section(self, styles, report_data):
        elements = []
        elements.append(Paragraph('Code Metrics', styles['SectionHeader']))
        elements.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#E2E8F0')))
        elements.append(Spacer(1, 0.1 * inch))

        metrics = report_data.get('metrics', {})
        if not metrics:
            return elements

        metrics_data = [
            ['Metric', 'Value', 'Metric', 'Value'],
            ['Total Lines', str(metrics.get('total_lines', 0)),
             'Code Lines', str(metrics.get('code_lines', 0))],
            ['Comment Lines', str(metrics.get('comment_lines', 0)),
             'Blank Lines', str(metrics.get('blank_lines', 0))],
            ['Functions', str(metrics.get('function_count', 0)),
             'Classes', str(metrics.get('class_count', 0))],
            ['Cyclomatic Complexity', str(metrics.get('cyclomatic_complexity', 1)),
             'Maintainability Index', str(metrics.get('maintainability_index', 0))],
            ['Comment Ratio', f"{metrics.get('comment_ratio', 0)}%",
             'Avg Function Complexity', str(metrics.get('avg_function_complexity', 0))],
        ]

        table = Table(metrics_data, colWidths=[2 * inch, 1.25 * inch, 2 * inch, 1.25 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('SPAN', (0, 0), (1, 0)),
            ('SPAN', (2, 0), (3, 0)),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (2, 1), (2, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(table)
        return elements

    def _build_issues_section(self, styles, report_data):
        elements = []
        issues = report_data.get('issues', [])
        elements.append(Paragraph(f'Detected Issues ({len(issues)})', styles['SectionHeader']))
        elements.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#E2E8F0')))
        elements.append(Spacer(1, 0.1 * inch))

        if not issues:
            elements.append(Paragraph('✅ No issues detected! Great code quality.', styles['RptBody']))
            return elements

        for issue in issues[:30]:
            sev = issue.get('severity', 'info')
            sev_color = SEVERITY_COLORS.get(sev, colors.gray)

            issue_data = [
                [Paragraph(f'<b>[{sev.upper()}]</b> {issue.get("message", "")}', styles['RptBody']),
                 Paragraph(f'Line {issue.get("line", "?")}', styles['RptBody'])],
            ]
            if issue.get('code_snippet'):
                issue_data.append([
                    Paragraph(f'<font name="Courier" size="8">{issue["code_snippet"][:150]}</font>', styles['RptCode']),
                    ''
                ])

            issue_table = Table(issue_data, colWidths=[5.5 * inch, 1 * inch])
            issue_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FAFAFA')),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, -1), (-1, -1), 6),
                ('LINEBEFORE', (0, 0), (0, -1), 3, sev_color),
                ('LINEBELOW', (0, -1), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ]))
            elements.append(issue_table)
            elements.append(Spacer(1, 0.05 * inch))

        if len(issues) > 30:
            elements.append(Paragraph(f'... and {len(issues) - 30} more issues.', styles['RptBody']))

        return elements

    def _build_vulnerabilities_section(self, styles, report_data):
        elements = []
        vulns = report_data.get('vulnerabilities_list', [])
        elements.append(Paragraph(f'Security Vulnerabilities ({len(vulns)})', styles['SectionHeader']))
        elements.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#E2E8F0')))
        elements.append(Spacer(1, 0.1 * inch))

        if not vulns:
            elements.append(Paragraph('✅ No security vulnerabilities detected!', styles['RptBody']))
            return elements

        for vuln in vulns:
            sev = vuln.get('severity', 'medium')
            sev_color = SEVERITY_COLORS.get(sev, colors.gray)

            vuln_data = [
                [Paragraph(f'<b>[{sev.upper()}] {vuln.get("category", "")}</b>', styles['RptBody']),
                 Paragraph(f'Line {vuln.get("line", "?")} | {vuln.get("cve", "")}', styles['RptBody'])],
                [Paragraph(vuln.get('description', ''), styles['RptBody']), ''],
                [Paragraph(f'<i>Fix: {vuln.get("recommendation", "")}</i>', styles['RptBody']), ''],
            ]
            if vuln.get('code_snippet'):
                vuln_data.insert(2, [
                    Paragraph(f'<font name="Courier" size="8">{vuln["code_snippet"][:150]}</font>', styles['RptCode']),
                    ''
                ])

            vuln_table = Table(vuln_data, colWidths=[5.5 * inch, 1 * inch])
            vuln_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFF7F7')),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, -1), (-1, -1), 6),
                ('LINEBEFORE', (0, 0), (0, -1), 4, sev_color),
                ('LINEBELOW', (0, -1), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ]))
            elements.append(vuln_table)
            elements.append(Spacer(1, 0.05 * inch))

        return elements

    def _build_suggestions_section(self, styles, report_data):
        elements = []
        suggestions = report_data.get('suggestions_list', [])
        elements.append(Paragraph(f'Optimization Suggestions ({len(suggestions)})', styles['SectionHeader']))
        elements.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#E2E8F0')))
        elements.append(Spacer(1, 0.1 * inch))

        if not suggestions:
            elements.append(Paragraph('No specific optimizations identified.', styles['RptBody']))
            return elements

        for i, s in enumerate(suggestions[:15], 1):
            text = f'{i}. <b>{s.get("suggestion", "")}</b>'
            if s.get('impact'):
                text += f' <font color="#6366F1">[{s["impact"]}]</font>'
            elements.append(Paragraph(text, styles['RptBody']))
            if s.get('example'):
                elements.append(Paragraph(
                    f'<font name="Courier" size="8">Example: {s["example"]}</font>', styles['RptCode']
                ))
            elements.append(Spacer(1, 0.05 * inch))

        return elements

    def _build_footer(self, styles):
        elements = [
            Spacer(1, 0.3 * inch),
            HRFlowable(width='100%', thickness=1, color=colors.HexColor('#E2E8F0')),
            Spacer(1, 0.1 * inch),
            Paragraph(
                'Generated by <b>AI Code Review Assistant</b> | Powered by AI/ML Analysis',
                ParagraphStyle('footer', fontSize=9, textColor=colors.HexColor('#94A3B8'), alignment=TA_CENTER)
            )
        ]
        return elements

    def generate_text_report(self, report_data: dict, output_path: str) -> str:
        lines = []
        lines.append('=' * 70)
        lines.append('          AI CODE REVIEW ASSISTANT - ANALYSIS REPORT')
        lines.append('=' * 70)
        lines.append(f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}')
        lines.append(f'Language: {report_data.get("language", "N/A").upper()}')
        lines.append('')

        scores = report_data.get('scores', {})
        lines.append('QUALITY SCORES:')
        lines.append(f'  Overall Score  : {scores.get("overall", 0)}/100  (Grade: {scores.get("grade", "N/A")})')
        lines.append(f'  Security       : {scores.get("security", 0)}/100')
        lines.append(f'  Code Quality   : {scores.get("quality", 0)}/100')
        lines.append(f'  Complexity     : {scores.get("complexity", 0)}/100')
        lines.append(f'  Maintainability: {scores.get("maintainability", 0)}/100')
        lines.append('')

        lines.append('ISSUES:')
        for issue in report_data.get('issues', []):
            lines.append(f'  [{issue.get("severity", "?").upper():8}] Line {issue.get("line", "?"):4} - {issue.get("message", "")}')
        lines.append('')

        lines.append('VULNERABILITIES:')
        for vuln in report_data.get('vulnerabilities_list', []):
            lines.append(f'  [{vuln.get("severity", "?").upper():8}] Line {vuln.get("line", "?"):4} - {vuln.get("category", "")}')
            lines.append(f'             Fix: {vuln.get("recommendation", "")}')
        lines.append('')

        lines.append('=' * 70)
        lines.append('END OF REPORT')
        lines.append('=' * 70)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        return output_path

    def _rate(self, score: float) -> str:
        if score >= 90:
            return 'Excellent ✓'
        elif score >= 75:
            return 'Good'
        elif score >= 60:
            return 'Fair'
        elif score >= 40:
            return 'Poor'
        else:
            return 'Critical !'
