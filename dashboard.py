import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(BASE_DIR))

def _path(relative):
    return os.path.join(BASE_DIR, relative)

# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title='MoI Identity Framework',
    page_icon='🛡️',
    layout='wide',
    initial_sidebar_state='expanded',
)

# ── Theme constants ───────────────────────────────────────────────────────────

CLR_BG        = '#0d1117'
CLR_SURFACE   = '#161b22'
CLR_BORDER    = '#30363d'
CLR_PRIMARY   = '#58a6ff'
CLR_SUCCESS   = '#3fb950'
CLR_WARNING   = '#d29922'
CLR_DANGER    = '#f85149'
CLR_TEXT      = '#e6edf3'
CLR_MUTED     = '#8b949e'

CHART_THEME = dict(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(color=CLR_TEXT, family='Inter, system-ui, sans-serif', size=12),
    xaxis=dict(gridcolor=CLR_BORDER, linecolor=CLR_BORDER, tickcolor=CLR_BORDER),
    yaxis=dict(gridcolor=CLR_BORDER, linecolor=CLR_BORDER, tickcolor=CLR_BORDER),
    legend=dict(bgcolor='rgba(0,0,0,0)', bordercolor=CLR_BORDER),
    margin=dict(l=0, r=0, t=36, b=0),
    title_font=dict(size=13, color=CLR_MUTED),
)

# ── Global CSS ────────────────────────────────────────────────────────────────

st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

  html, body, [class*="css"] {{
      font-family: 'Inter', system-ui, sans-serif;
      background-color: {CLR_BG};
      color: {CLR_TEXT};
  }}

  /* Hide Streamlit chrome */
  #MainMenu, footer, header {{ visibility: hidden; }}
  .block-container {{ padding: 1.5rem 2rem 2rem; }}

  /* Sidebar — always visible, never auto-collapses */
  [data-testid="stSidebar"] {{
      background-color: {CLR_SURFACE};
      border-right: 1px solid {CLR_BORDER};
      min-width: 260px !important;
      max-width: 260px !important;
      transform: none !important;
  }}
  [data-testid="stSidebar"] .block-container {{ padding: 1.5rem 1rem; }}
  [data-testid="collapsedControl"] {{ display: none !important; }}

  /* Tabs */
  .stTabs [data-baseweb="tab-list"] {{
      gap: 4px;
      background: {CLR_SURFACE};
      padding: 6px;
      border-radius: 10px;
      border: 1px solid {CLR_BORDER};
  }}
  .stTabs [data-baseweb="tab"] {{
      border-radius: 7px;
      padding: 8px 20px;
      color: {CLR_MUTED};
      font-size: 13px;
      font-weight: 500;
      background: transparent;
      border: none;
  }}
  .stTabs [aria-selected="true"] {{
      background: {CLR_PRIMARY} !important;
      color: #fff !important;
  }}
  .stTabs [data-baseweb="tab-panel"] {{ padding-top: 1.5rem; }}

  /* Metric cards */
  .metric-card {{
      background: {CLR_SURFACE};
      border: 1px solid {CLR_BORDER};
      border-radius: 10px;
      padding: 1.1rem 1.25rem;
  }}
  .metric-label {{
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: {CLR_MUTED};
      margin-bottom: 6px;
  }}
  .metric-value {{
      font-size: 26px;
      font-weight: 700;
      color: {CLR_TEXT};
      line-height: 1;
  }}
  .metric-sub {{
      font-size: 11px;
      color: {CLR_MUTED};
      margin-top: 4px;
  }}
  .metric-accent {{ color: {CLR_PRIMARY}; }}
  .metric-success {{ color: {CLR_SUCCESS}; }}
  .metric-danger  {{ color: {CLR_DANGER};  }}
  .metric-warning {{ color: {CLR_WARNING}; }}

  /* Section headers */
  .section-header {{
      font-size: 13px;
      font-weight: 600;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      color: {CLR_MUTED};
      margin-bottom: 12px;
      padding-bottom: 8px;
      border-bottom: 1px solid {CLR_BORDER};
  }}

  /* Chart wrapper */
  .chart-card {{
      background: {CLR_SURFACE};
      border: 1px solid {CLR_BORDER};
      border-radius: 10px;
      padding: 1rem 1.25rem;
  }}

  /* Status pill */
  .pill {{
      display: inline-block;
      padding: 2px 10px;
      border-radius: 20px;
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 0.04em;
  }}
  .pill-ok      {{ background: rgba(63,185,80,.15);  color: {CLR_SUCCESS}; }}
  .pill-warn    {{ background: rgba(210,153,34,.15); color: {CLR_WARNING}; }}
  .pill-danger  {{ background: rgba(248,81,73,.15);  color: {CLR_DANGER};  }}
  .pill-neutral {{ background: rgba(88,166,255,.12); color: {CLR_PRIMARY}; }}

  /* Sidebar status rows */
  .status-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 6px 0;
      border-bottom: 1px solid {CLR_BORDER};
      font-size: 12px;
  }}
  .status-label {{ color: {CLR_MUTED}; }}

  /* Dataframe tweaks */
  [data-testid="stDataFrame"] {{
      border: 1px solid {CLR_BORDER};
      border-radius: 8px;
      overflow: hidden;
  }}

  /* Empty state */
  .empty-state {{
      background: {CLR_SURFACE};
      border: 1px dashed {CLR_BORDER};
      border-radius: 10px;
      padding: 2.5rem;
      text-align: center;
      color: {CLR_MUTED};
      font-size: 13px;
  }}
  .empty-state-icon {{ font-size: 28px; margin-bottom: 8px; }}
</style>
""", unsafe_allow_html=True)


# ── Data loaders ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=30)
def load_round_metrics():
    p = _path('logs/round_metrics.csv')
    return pd.read_csv(p) if os.path.exists(p) else pd.DataFrame()

@st.cache_data(ttl=30)
def load_attack_log():
    p = _path('logs/attack_log.csv')
    return pd.read_csv(p) if os.path.exists(p) else pd.DataFrame()

@st.cache_data(ttl=30)
def load_reputation():
    p = _path('logs/blockchain_audit.csv')
    return pd.read_csv(p) if os.path.exists(p) else pd.DataFrame()

@st.cache_data(ttl=30)
def load_krum_scores():
    p = _path('logs/krum_scores.csv')
    return pd.read_csv(p) if os.path.exists(p) else pd.DataFrame()

@st.cache_data(ttl=30)
def load_baseline_metrics():
    p = _path('logs/baseline_metrics.csv')
    return pd.read_csv(p) if os.path.exists(p) else pd.DataFrame()

@st.cache_data(ttl=30)
def load_byzantine_metrics():
    p = _path('logs/byzantine_metrics.csv')
    return pd.read_csv(p) if os.path.exists(p) else pd.DataFrame()

@st.cache_data(ttl=30)
def load_privacy_budget():
    p = _path('logs/privacy_budget.csv')
    return pd.read_csv(p) if os.path.exists(p) else pd.DataFrame()

@st.cache_data(ttl=30)
def load_dp_sensitivity():
    p = _path('logs/dp_sensitivity.csv')
    return pd.read_csv(p) if os.path.exists(p) else pd.DataFrame()

@st.cache_data(ttl=30)
def load_simulation_logs():
    p = _path('logs/moi_simulation.log')
    if not os.path.exists(p):
        return pd.DataFrame()
    data = []
    with open(p, 'r') as f:
        for line in f:
            parts = line.strip().split(', ')
            entry = {}
            for part in parts:
                if '=' in part:
                    k, v = part.split('=', 1)
                    entry[k.strip()] = v.strip().strip('"')
            if entry:
                data.append(entry)
    return pd.DataFrame(data)


# ── Helpers ───────────────────────────────────────────────────────────────────

def metric_card(label, value, sub='', color_class=''):
    value_html = f'<div class="metric-value {color_class}">{value}</div>'
    sub_html   = f'<div class="metric-sub">{sub}</div>' if sub else ''
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        {value_html}
        {sub_html}
    </div>
    """, unsafe_allow_html=True)

def section_header(text):
    st.markdown(f'<div class="section-header">{text}</div>', unsafe_allow_html=True)

def empty_state(icon, message):
    st.markdown(f"""
    <div class="empty-state">
        <div class="empty-state-icon">{icon}</div>
        <div>{message}</div>
    </div>
    """, unsafe_allow_html=True)

def pill(text, kind='neutral'):
    st.markdown(f'<span class="pill pill-{kind}">{text}</span>', unsafe_allow_html=True)

def chart_container(fig):
    fig.update_layout(**CHART_THEME)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


# ── Load data ─────────────────────────────────────────────────────────────────

metrics_df   = load_round_metrics()
attack_df    = load_attack_log()
rep_df       = load_reputation()
krum_df      = load_krum_scores()
sim_df       = load_simulation_logs()
baseline_df  = load_baseline_metrics()
byzantine_df = load_byzantine_metrics()
budget_df    = load_privacy_budget()
dp_sens_df   = load_dp_sensitivity()

has_metrics   = not metrics_df.empty
has_attacks   = not attack_df.empty
has_rep       = not rep_df.empty
has_krum      = not krum_df.empty
has_sim       = not sim_df.empty
has_baseline  = not baseline_df.empty
has_byzantine = not byzantine_df.empty
has_budget    = not budget_df.empty
has_dp_sens   = not dp_sens_df.empty


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(f"""
    <div style="margin-bottom:1.5rem;">
        <div style="font-size:18px;font-weight:700;color:{CLR_TEXT};">🛡️ MoI Framework</div>
        <div style="font-size:11px;color:{CLR_MUTED};margin-top:2px;">Byzantine-Robust Identity System</div>
    </div>
    """, unsafe_allow_html=True)

    section_header('Data Status')

    def _status_row(label, ok, ok_label='Loaded', fail_label='No data'):
        badge = f'<span class="pill pill-ok">{ok_label}</span>' if ok else f'<span class="pill pill-warn">{fail_label}</span>'
        st.markdown(f'<div class="status-row"><span class="status-label">{label}</span>{badge}</div>', unsafe_allow_html=True)

    _status_row('FL Metrics',     has_metrics)
    _status_row('Baseline Run',   has_baseline)
    _status_row('Byzantine Run',  has_byzantine)
    _status_row('Attack Log',     has_attacks, ok_label='Attacks found', fail_label='Clean')
    _status_row('Privacy Budget', has_budget)
    _status_row('Reputation',     has_rep)
    _status_row('Krum Scores',    has_krum)
    _status_row('Simulation Log', has_sim)

    st.markdown('<br>', unsafe_allow_html=True)
    section_header('System Info')

    if has_metrics:
        rounds_done = len(metrics_df)
        best_acc    = metrics_df['accuracy'].max()
        st.markdown(f"""
        <div class="status-row"><span class="status-label">Rounds completed</span><span style="color:{CLR_TEXT};font-size:12px;">{rounds_done}</span></div>
        <div class="status-row"><span class="status-label">Best accuracy</span><span style="color:{CLR_SUCCESS};font-size:12px;">{best_acc*100:.1f}%</span></div>
        """, unsafe_allow_html=True)

    if has_attacks:
        st.markdown(f"""
        <div class="status-row"><span class="status-label">Attacks logged</span><span style="color:{CLR_DANGER};font-size:12px;">{len(attack_df)}</span></div>
        """, unsafe_allow_html=True)

    st.markdown('<br>', unsafe_allow_html=True)

    if st.button('Refresh Data', use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown(f"""
    <div style="position:absolute;bottom:1.5rem;left:1rem;right:1rem;font-size:10px;color:{CLR_MUTED};text-align:center;">
        v1.0 &nbsp;·&nbsp; {datetime.now().strftime('%H:%M')}
    </div>
    """, unsafe_allow_html=True)


# ── Main header ───────────────────────────────────────────────────────────────

st.markdown(f"""
<div style="margin-bottom:1.5rem;">
    <h1 style="font-size:22px;font-weight:700;color:{CLR_TEXT};margin:0;">Command Center</h1>
    <p style="font-size:13px;color:{CLR_MUTED};margin:4px 0 0;">
        Federated Learning · Byzantine Defense · Blockchain Reputation
    </p>
</div>
""", unsafe_allow_html=True)


# ── Tabs ──────────────────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    '📈  FL Performance',
    '⚔️  Comparison',
    '🛡️  Byzantine Defense',
    '🔗  Reputation',
    '📋  Audit Trail',
])


# ── Tab 1 · FL Performance ────────────────────────────────────────────────────

with tab1:
    if has_metrics:
        final_acc  = metrics_df['accuracy'].iloc[-1]
        final_f1   = metrics_df['f1'].iloc[-1]
        best_acc   = metrics_df['accuracy'].max()
        total_rnd  = len(metrics_df)
        delta_acc  = final_acc - metrics_df['accuracy'].iloc[0]

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            metric_card('Final Accuracy', f'{final_acc*100:.2f}%',
                        sub=f'Δ {delta_acc*100:+.2f}% from round 1',
                        color_class='metric-success' if final_acc > 0.85 else 'metric-warning')
        with c2:
            metric_card('Final F1 Score', f'{final_f1:.4f}', color_class='metric-accent')
        with c3:
            metric_card('Best Accuracy', f'{best_acc*100:.2f}%',
                        sub=f'Round {metrics_df["accuracy"].idxmax() + 1}',
                        color_class='metric-success')
        with c4:
            metric_card('Training Rounds', str(total_rnd),
                        sub='Completed successfully')

        st.markdown('<br>', unsafe_allow_html=True)

        col_l, col_r = st.columns(2)

        with col_l:
            section_header('Accuracy over Rounds')
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=metrics_df['round'], y=metrics_df['accuracy'],
                mode='lines+markers',
                line=dict(color=CLR_PRIMARY, width=2),
                marker=dict(size=5, color=CLR_PRIMARY),
                fill='tozeroy',
                fillcolor=f'rgba(88,166,255,0.08)',
                name='Accuracy',
            ))
            fig.update_layout(yaxis_range=[0, 1], yaxis_tickformat='.0%',
                              title='Accuracy per Round', **CHART_THEME)
            chart_container(fig)

        with col_r:
            section_header('Classification Metrics over Rounds')
            fig2 = go.Figure()
            palette = {'f1': CLR_PRIMARY, 'precision': CLR_SUCCESS, 'recall': CLR_WARNING}
            for col, color in palette.items():
                if col in metrics_df.columns:
                    fig2.add_trace(go.Scatter(
                        x=metrics_df['round'], y=metrics_df[col],
                        mode='lines+markers',
                        line=dict(color=color, width=2),
                        marker=dict(size=4),
                        name=col.capitalize(),
                    ))
            fig2.update_layout(yaxis_range=[0, 1], title='F1 · Precision · Recall', **CHART_THEME)
            chart_container(fig2)

        if 'winner' in metrics_df.columns:
            st.markdown('<br>', unsafe_allow_html=True)
            section_header('Krum Winner Selection per Round')
            fig3 = px.scatter(
                metrics_df, x='round', y='winner',
                color='accuracy',
                color_continuous_scale=[[0, CLR_DANGER], [0.5, CLR_WARNING], [1, CLR_SUCCESS]],
                size_max=10,
                labels={'winner': 'Selected Office', 'round': 'Round', 'accuracy': 'Accuracy'},
            )
            fig3.update_traces(marker=dict(size=10))
            fig3.update_layout(title='Office Selected as Krum Winner', **CHART_THEME)
            chart_container(fig3)

        if has_budget:
            st.markdown('<br>', unsafe_allow_html=True)
            section_header('Privacy Budget Summary')
            b = budget_df.iloc[0]
            bc1, bc2, bc3, bc4 = st.columns(4)
            with bc1:
                metric_card('ε per Round', str(b.get('epsilon_per_round', '—')), color_class='metric-accent')
            with bc2:
                metric_card('Total ε Spent', str(b.get('total_epsilon_spent', '—')),
                            sub='Sequential composition', color_class='metric-warning')
            with bc3:
                metric_card('Clip Norm', str(b.get('clip_norm', '—')), color_class='metric-accent')
            with bc4:
                metric_card('Rounds with DP', str(b.get('rounds_completed', '—')))

    else:
        st.markdown('<br>', unsafe_allow_html=True)
        empty_state('📊', 'No federated learning metrics found.<br>Run <code>python main.py --mode baseline</code> to generate data.')


# ── Tab 2 · Comparison ────────────────────────────────────────────────────────

with tab2:
    if has_baseline and has_byzantine:
        # Summary metrics row
        bl_final  = baseline_df['accuracy'].iloc[-1]
        bz_final  = byzantine_df['accuracy'].iloc[-1]
        bl_best   = baseline_df['accuracy'].max()
        bz_best   = byzantine_df['accuracy'].max()
        acc_drop  = bl_final - bz_final

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            metric_card('Baseline Accuracy', f'{bl_final*100:.2f}%',
                        sub='No attack', color_class='metric-success')
        with c2:
            metric_card('Byzantine Accuracy', f'{bz_final*100:.2f}%',
                        sub='Under attack', color_class='metric-danger' if bz_final < bl_final * 0.95 else 'metric-warning')
        with c3:
            metric_card('Accuracy Drop', f'{acc_drop*100:.2f}pp',
                        sub='Krum defence impact',
                        color_class='metric-success' if acc_drop < 0.05 else 'metric-danger')
        with c4:
            defended = 'YES' if acc_drop < 0.10 else 'PARTIAL'
            metric_card('Krum Defended', defended,
                        color_class='metric-success' if defended == 'YES' else 'metric-warning')

        st.markdown('<br>', unsafe_allow_html=True)
        section_header('Accuracy: Baseline vs Byzantine Attack')

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=baseline_df['round'], y=baseline_df['accuracy'],
            mode='lines+markers', name='Baseline (honest)',
            line=dict(color=CLR_SUCCESS, width=2), marker=dict(size=5),
            fill='tozeroy', fillcolor='rgba(63,185,80,0.06)',
        ))
        fig.add_trace(go.Scatter(
            x=byzantine_df['round'], y=byzantine_df['accuracy'],
            mode='lines+markers', name='Byzantine (office 4 attacks)',
            line=dict(color=CLR_DANGER, width=2, dash='dash'), marker=dict(size=5),
        ))
        fig.update_layout(yaxis_range=[0, 1], yaxis_tickformat='.0%',
                          title='Accuracy per Round — Baseline vs Byzantine', **CHART_THEME)
        chart_container(fig)

        col_l, col_r = st.columns(2)
        with col_l:
            section_header('F1 Score Comparison')
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=baseline_df['round'],  y=baseline_df['f1'],
                                      name='Baseline', line=dict(color=CLR_SUCCESS, width=2)))
            fig2.add_trace(go.Scatter(x=byzantine_df['round'], y=byzantine_df['f1'],
                                      name='Byzantine', line=dict(color=CLR_DANGER, width=2, dash='dash')))
            fig2.update_layout(title='F1 Score per Round', **CHART_THEME)
            chart_container(fig2)

        with col_r:
            if has_dp_sens:
                section_header('Privacy-Utility Tradeoff (ε vs Accuracy)')
                fig3 = go.Figure()
                fig3.add_trace(go.Scatter(
                    x=dp_sens_df['epsilon'], y=dp_sens_df['final_accuracy'],
                    mode='lines+markers', name='Accuracy',
                    line=dict(color=CLR_PRIMARY, width=2), marker=dict(size=8),
                ))
                fig3.add_trace(go.Scatter(
                    x=dp_sens_df['epsilon'], y=dp_sens_df['final_f1'],
                    mode='lines+markers', name='F1',
                    line=dict(color=CLR_WARNING, width=2), marker=dict(size=8),
                ))
                fig3.update_layout(
                    xaxis_title='Epsilon (ε) — higher = less private',
                    yaxis_title='Score', yaxis_range=[0, 1],
                    title='Privacy-Utility Tradeoff', **CHART_THEME,
                )
                chart_container(fig3)
            else:
                empty_state('📉', 'Run <code>python main.py --mode dp</code> to generate privacy-utility data.')

    else:
        empty_state('⚔️', 'Run both experiments to see the comparison.<br>'
                          '<code>python main.py --mode baseline</code><br>'
                          '<code>python main.py --mode byzantine</code>')


# ── Tab 3 · Byzantine Defense ─────────────────────────────────────────────────

with tab3:
    col_l, col_r = st.columns([1, 2])

    with col_l:
        section_header('Defense Status')
        if has_attacks:
            metric_card('Attacks Detected', str(len(attack_df)),
                        sub='Byzantine poisoning events', color_class='metric-danger')
        else:
            metric_card('Threat Level', 'CLEAR',
                        sub='No attacks in current logs', color_class='metric-success')

        if has_krum:
            st.markdown('<br>', unsafe_allow_html=True)
            section_header('Krum Score Table')
            krum_display = krum_df.copy()
            krum_display.columns = ['Office', 'Krum Score']
            krum_display['Krum Score'] = krum_display['Krum Score'].round(4)
            st.dataframe(krum_display, use_container_width=True, hide_index=True)

    with col_r:
        if has_krum:
            section_header('Krum Scores by Office')
            min_score = krum_df['krum_score'].min()
            colors = [CLR_SUCCESS if s == min_score else CLR_DANGER if s == krum_df['krum_score'].max() else CLR_PRIMARY
                      for s in krum_df['krum_score']]
            fig = go.Figure(go.Bar(
                x=krum_df['office'].astype(str),
                y=krum_df['krum_score'],
                marker_color=colors,
                text=krum_df['krum_score'].round(2),
                textposition='outside',
            ))
            fig.update_layout(
                title='Krum Scores — lower score = more trustworthy',
                xaxis_title='Office', yaxis_title='Score',
                **CHART_THEME,
            )
            chart_container(fig)
        else:
            empty_state('🔍', 'No Krum score data available.')

    if has_attacks:
        st.markdown('<br>', unsafe_allow_html=True)
        section_header('Attack Event Log')
        st.dataframe(attack_df, use_container_width=True, hide_index=True)


# ── Tab 4 · Reputation ────────────────────────────────────────────────────────

with tab4:
    if has_rep:
        action_counts = rep_df['action'].value_counts()
        c1, c2, c3 = st.columns(3)
        with c1:
            slashes = int(action_counts.get('SLASH', 0))
            metric_card('Slash Events', str(slashes),
                        sub='Malicious behaviour penalised',
                        color_class='metric-danger' if slashes else '')
        with c2:
            rewards = int(action_counts.get('REWARD', 0))
            metric_card('Reward Events', str(rewards),
                        sub='Honest contributions credited', color_class='metric-success')
        with c3:
            offices = rep_df['office_id'].nunique() if 'office_id' in rep_df.columns else '—'
            metric_card('Active Offices', str(offices), sub='Tracked on-chain')

        st.markdown('<br>', unsafe_allow_html=True)
        col_l, col_r = st.columns(2)

        with col_l:
            section_header('Action Distribution')
            fig = go.Figure(go.Bar(
                x=action_counts.index.tolist(),
                y=action_counts.values.tolist(),
                marker_color=[CLR_DANGER if a == 'SLASH' else CLR_SUCCESS for a in action_counts.index],
                text=action_counts.values.tolist(),
                textposition='outside',
            ))
            fig.update_layout(title='Slash vs Reward Events', xaxis_title='Action',
                              yaxis_title='Count', **CHART_THEME)
            chart_container(fig)

        with col_r:
            if 'office_id' in rep_df.columns:
                section_header('Activity by Office')
                office_counts = rep_df['office_id'].value_counts().sort_index()
                fig2 = go.Figure(go.Bar(
                    x=office_counts.index.astype(str).tolist(),
                    y=office_counts.values.tolist(),
                    marker_color=CLR_PRIMARY,
                    text=office_counts.values.tolist(),
                    textposition='outside',
                ))
                fig2.update_layout(title='Blockchain Events per Office',
                                   xaxis_title='Office', yaxis_title='Events', **CHART_THEME)
                chart_container(fig2)

        st.markdown('<br>', unsafe_allow_html=True)
        section_header('Recent Blockchain Events (last 20)')
        st.dataframe(rep_df.tail(20), use_container_width=True, hide_index=True)
    else:
        empty_state('🔗', 'No reputation data yet.<br>Run <code>python main.py --mode reputation</code> to populate.')


# ── Tab 5 · Audit Trail ───────────────────────────────────────────────────────

with tab5:
    if has_sim:
        if 'reputation' in sim_df.columns:
            sim_df['reputation'] = pd.to_numeric(sim_df['reputation'], errors='coerce')

        col_l, col_r = st.columns(2)

        with col_l:
            if 'reputation' in sim_df.columns and 'office' in sim_df.columns:
                section_header('Latest Reputation by Office')
                latest = sim_df.groupby('office').last().reset_index()
                bar_colors = [CLR_DANGER if v < 50 else CLR_WARNING if v < 75 else CLR_SUCCESS
                              for v in latest['reputation']]
                fig = go.Figure(go.Bar(
                    x=latest['office'].astype(str),
                    y=latest['reputation'],
                    marker_color=bar_colors,
                    text=latest['reputation'].round(1),
                    textposition='outside',
                ))
                fig.update_layout(yaxis_range=[0, 110], title='Reputation Score by Office',
                                  xaxis_title='Office', yaxis_title='Score', **CHART_THEME)
                chart_container(fig)

        with col_r:
            if 'status' in sim_df.columns:
                section_header('Office Status Distribution')
                status_counts = sim_df['status'].value_counts()
                status_colors = {
                    'honest': CLR_SUCCESS, 'banned': CLR_DANGER,
                    'warning': CLR_WARNING, 'active': CLR_PRIMARY,
                }
                colors = [status_colors.get(s.lower(), CLR_MUTED) for s in status_counts.index]
                fig2 = go.Figure(go.Pie(
                    labels=status_counts.index.tolist(),
                    values=status_counts.values.tolist(),
                    marker_colors=colors,
                    hole=0.45,
                    textinfo='label+percent',
                    textfont=dict(size=12, color=CLR_TEXT),
                ))
                fig2.update_layout(title='Status Distribution', **CHART_THEME)
                chart_container(fig2)

        st.markdown('<br>', unsafe_allow_html=True)
        section_header(f'Simulation Log — last 30 entries of {len(sim_df)} total')
        st.dataframe(sim_df.tail(30), use_container_width=True, hide_index=True)
    else:
        empty_state('📋', 'No simulation audit logs found.<br>Run <code>python main.py --mode full</code> to generate.')
