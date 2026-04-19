import logging
import os
from datetime import datetime

import pandas as pd

logger = logging.getLogger(__name__)

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


class ReportGenerator:
    def __init__(self, output_dir=None):
        self.output_dir = output_dir or os.path.join(_BASE_DIR, 'reports')
        os.makedirs(self.output_dir, exist_ok=True)
        self.experiments = []

    def add_experiment(self, name: str, config: dict, metrics: list):
        self.experiments.append({
            'name':      name,
            'config':    config,
            'metrics':   metrics,
            'timestamp': datetime.now(),
        })

    # ── HTML ─────────────────────────────────────────────────────────────────

    def generate_html_report(self, output_file='report.html') -> str:
        path = os.path.join(self.output_dir, output_file)
        with open(path, 'w') as f:
            f.write(self._build_html())
        logger.info('HTML report saved to %s', path)
        return path

    def _build_html(self) -> str:
        generated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        rows = ''
        for exp in self.experiments:
            if exp['metrics']:
                m = exp['metrics'][-1]
                rows += f'''
                <div class="metric">
                    <div class="metric-value">{m.get("accuracy", 0):.2%}</div>
                    <div class="metric-label">{exp["name"]} — Final Accuracy</div>
                </div>'''

        detail = ''
        for exp in self.experiments:
            detail += f'<h3>{exp["name"]}</h3><p>Config: {exp["config"]}</p>'
            detail += '<table><tr><th>Round</th><th>Accuracy</th><th>Precision</th><th>Recall</th><th>F1</th><th>ε Spent</th></tr>'
            for m in exp['metrics']:
                detail += (
                    f'<tr><td>{m.get("round","?")}</td>'
                    f'<td>{m.get("accuracy",0):.4f}</td>'
                    f'<td>{m.get("precision",0):.4f}</td>'
                    f'<td>{m.get("recall",0):.4f}</td>'
                    f'<td>{m.get("f1",0):.4f}</td>'
                    f'<td>{m.get("epsilon_spent","—")}</td></tr>'
                )
            detail += '</table>'

        return f'''<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Byzantine-Robust Identity Framework — Report</title>
  <style>
    body   {{ font-family: Inter, Arial, sans-serif; margin: 40px; background: #0d1117; color: #e6edf3; }}
    h1     {{ color: #58a6ff; border-bottom: 2px solid #30363d; padding-bottom: 10px; }}
    h2,h3  {{ color: #8b949e; }}
    table  {{ width: 100%; border-collapse: collapse; margin: 16px 0; }}
    th     {{ background: #161b22; color: #58a6ff; padding: 10px; border: 1px solid #30363d; }}
    td     {{ padding: 8px 10px; border: 1px solid #30363d; }}
    tr:nth-child(even) {{ background: #161b22; }}
    .metric       {{ display: inline-block; margin: 10px 16px 10px 0; padding: 16px 24px;
                     background: #161b22; border: 1px solid #30363d; border-radius: 8px; }}
    .metric-value {{ font-size: 28px; font-weight: 700; color: #3fb950; }}
    .metric-label {{ font-size: 11px; color: #8b949e; margin-top: 4px; }}
    .section      {{ background: #161b22; border-left: 4px solid #58a6ff;
                     padding: 20px; border-radius: 6px; margin: 20px 0; }}
  </style>
</head>
<body>
<h1>Byzantine-Robust Identity Framework</h1>
<p><strong>Generated:</strong> {generated}</p>

<h2>Summary</h2>
<div>{rows}</div>

<div class="section">
  <h2>Architecture</h2>
  <ul>
    <li><strong>FL Model:</strong> MLP (64→32) with FedKrum aggregation</li>
    <li><strong>Byzantine Defence:</strong> Krum algorithm (selects most trustworthy gradient update)</li>
    <li><strong>Privacy:</strong> Gradient clipping + Laplace noise (ε-DP per round)</li>
    <li><strong>Blockchain:</strong> IdentityRegistry.sol — reputation slashing &amp; rewards</li>
    <li><strong>Dataset:</strong> NSL-KDD (binary: normal vs attack)</li>
  </ul>
</div>

<h2>Detailed Results</h2>
{detail}

<div class="section">
  <h2>Conclusion</h2>
  <p>
    The FedKrum framework successfully demonstrates Byzantine-robust federated learning
    with formal (ε, 0)-DP guarantees per round and blockchain-backed reputation tracking.
    Krum aggregation filters poisoned gradient updates, maintaining model accuracy
    even when one office acts maliciously.
  </p>
</div>
</body>
</html>'''

    # ── PDF ──────────────────────────────────────────────────────────────────

    def generate_pdf_report(self, output_file='report.pdf') -> str:
        if not HAS_REPORTLAB:
            logger.warning('reportlab not installed — generating HTML instead.')
            return self.generate_html_report(output_file.replace('.pdf', '.html'))

        path = os.path.join(self.output_dir, output_file)
        doc  = SimpleDocTemplate(path, pagesize=letter)
        styles = getSampleStyleSheet()
        story  = [Paragraph('Byzantine-Robust Identity Framework', styles['Title']),
                  Spacer(1, 20)]

        if self.experiments:
            story.append(Paragraph('Experiment Summary', styles['Heading2']))
            data = [['Experiment', 'Final Accuracy', 'Final F1', 'ε Spent']]
            for exp in self.experiments:
                if exp['metrics']:
                    m = exp['metrics'][-1]
                    data.append([
                        exp['name'],
                        f"{m.get('accuracy', 0):.4f}",
                        f"{m.get('f1', 0):.4f}",
                        str(m.get('epsilon_spent', '—')),
                    ])
            t = Table(data)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f2937')),
                ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
                ('ALIGN',      (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID',       (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            story.append(t)

        doc.build(story)
        logger.info('PDF report saved to %s', path)
        return path


def generate_from_logs(logs_dir=None) -> str:
    logs_dir = logs_dir or os.path.join(_BASE_DIR, 'logs')
    gen = ReportGenerator()

    metrics_path = os.path.join(logs_dir, 'round_metrics.csv')
    if os.path.exists(metrics_path):
        df = pd.read_csv(metrics_path)
        gen.add_experiment('Federated Learning', {'n_offices': 5, 'num_rounds': len(df)},
                           df.to_dict('records'))

    return gen.generate_html_report()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    generate_from_logs()
