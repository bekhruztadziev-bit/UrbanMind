from __future__ import annotations

import csv
import io
import json
from typing import Any, Dict
from app.services.reports.models import DecisionReport


def export_report_json(report: DecisionReport) -> str:
    """Exports the complete structured DecisionReport as formatted JSON."""
    return json.dumps(report, indent=2, ensure_ascii=False)


def export_report_csv(report: DecisionReport) -> str:
    """Exports the metric comparison table, robustness statistics, and executive summary as CSV."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Header / Meta
    writer.writerow(["URBANMIND DECISION REPORT", report.get("report_id", "")])
    writer.writerow(["Created At", report.get("created_at", "")])
    writer.writerow(["Experiment ID", report.get("experiment_id", "")])
    writer.writerow(["Scenario", report.get("scenario_id", "")])
    writer.writerow(["Policy", report.get("policy_id", "").upper()])
    spatial = report.get("spatial_scope", {})
    writer.writerow(["Spatial Scope", f"{spatial.get('city_name', 'Tashkent')} > {spatial.get('district_name', '')} > {spatial.get('corridor_name', '')}"])
    writer.writerow([])

    # 15-Second Decision Brief
    exec_summary = report.get("executive_summary", {})
    ev_status = report.get("evidence_status", {})
    calib_status = report.get("calibration_status", {})
    next_act = report.get("next_action", {})

    writer.writerow(["DECISION BRIEF"])
    writer.writerow(["Simulation-Supported Candidate", exec_summary.get("recommended_intervention", "")])
    writer.writerow(["Primary Delay Impact", exec_summary.get("primary_result", "")])
    writer.writerow(["Environmental Impact", exec_summary.get("environmental_result", "")])
    writer.writerow(["Main Trade-off", exec_summary.get("main_tradeoff", "")])
    writer.writerow(["Evidence Strength", f"{ev_status.get('level', 'MODERATE')} ({ev_status.get('score', 0)}/100)"])
    writer.writerow(["Calibration Status", calib_status.get("status", "UNCALIBRATED")])
    writer.writerow(["Recommended Next Action", next_act.get("title_en", "")])
    writer.writerow(["Next Action Rationale", next_act.get("rationale_en", "")])
    writer.writerow(["Recommendation Text", exec_summary.get("recommendation", "")])
    writer.writerow([])

    # Model vs Reality Classification
    mvr = report.get("model_vs_reality", {})
    writer.writerow(["MODEL VS REALITY DATA CLASSIFICATION"])
    writer.writerow(["Category", "Metric", "Source", "Value", "Calibration State"])
    for obs in mvr.get("observed_metrics", []):
        writer.writerow(["OBSERVED", obs.get("name_en", ""), obs.get("source", ""), obs.get("value", ""), obs.get("calibration_state", "")])
    for sim in mvr.get("simulated_metrics", []):
        writer.writerow(["SIMULATED", sim.get("name_en", ""), sim.get("source", ""), sim.get("value", ""), sim.get("calibration_state", "")])
    for der in mvr.get("derived_metrics", []):
        writer.writerow(["DERIVED", der.get("name_en", ""), der.get("source", ""), der.get("value", ""), der.get("calibration_state", "")])
    writer.writerow([])

    # Policy Audit
    policy_audit = report.get("policy_audit", {})
    writer.writerow(["POLICY AUDIT & OBJECTIVES"])
    writer.writerow(["Policy Name", policy_audit.get("policy_name", "")])
    writer.writerow(["Decision Objective", policy_audit.get("objective_question", "")])
    writer.writerow(["Why This Won", report.get("why_won") or policy_audit.get("why_won", "")])
    writer.writerow(["Composite Policy Score (%)", policy_audit.get("policy_score", 0)])
    writer.writerow(["Mobility Score (%)", policy_audit.get("mobility_score", 0)])
    writer.writerow(["Environment Score (%)", policy_audit.get("environment_score", 0)])
    writer.writerow(["Accessibility Score (%)", policy_audit.get("accessibility_score", 0)])
    writer.writerow(["Constraint Status", policy_audit.get("constraint_status", "")])
    for k, v in policy_audit.get("policy_weights", {}).items():
        writer.writerow([f"Weight: {k.capitalize()}", f"{int(v*100)}%"])
    writer.writerow([])

    # Policy Outcome Comparison (if available)
    policy_comp = report.get("policy_comparison") or {}
    if policy_comp:
        writer.writerow(["POLICY OUTCOME COMPARISON"])
        writer.writerow(["Policy", "Winner Candidate", "Overall Score (%)", "Delay (s)", "CO2 (kg)", "Throughput (veh/h)", "Why This Won"])
        for p_k, p_v in policy_comp.items():
            if isinstance(p_v, dict):
                writer.writerow([
                    p_v.get("policy_name", p_k.upper()),
                    p_v.get("best_candidate_label", ""),
                    p_v.get("overall_score", ""),
                    p_v.get("average_waiting_seconds", ""),
                    p_v.get("co2_kg", ""),
                    p_v.get("throughput_vehicles_per_hour", ""),
                    p_v.get("why_won", ""),
                ])
        writer.writerow([])


    # Metric Comparison
    writer.writerow(["METRIC COMPARISON (BASELINE VS OPTIMIZED)"])
    writer.writerow([
        "Metric Key",
        "Name (EN)",
        "Name (RU)",
        "Unit",
        "Baseline",
        "Optimized",
        "Absolute Change",
        "Percentage Change (%)",
        "Direction",
        "Is Improvement",
        "Provenance"
    ])

    for row in report.get("metric_comparison", []):
        writer.writerow([
            row.get("key", ""),
            row.get("name_en", ""),
            row.get("name_ru", ""),
            row.get("unit", ""),
            row.get("baseline", 0),
            row.get("optimized", 0),
            row.get("absolute_change", 0),
            row.get("percentage_change", 0),
            row.get("direction", ""),
            "YES" if row.get("is_improvement") else "NO",
            row.get("provenance", "")
        ])

    writer.writerow([])

    # Robustness
    robustness = report.get("robustness", {})
    writer.writerow(["ROBUSTNESS & STATISTICAL EVIDENCE"])
    writer.writerow(["Sample Count / Seeds", f"{robustness.get('sample_count', 0)} ({len(robustness.get('seeds', []))} seeds)"])
    writer.writerow(["Metric", "Mean", "Std Dev", "95% CI Low", "95% CI High", "Min", "Max"])
    for m_key, m_stats in robustness.get("stats", {}).items():
        writer.writerow([
            m_key,
            m_stats.get("mean", 0),
            m_stats.get("std_dev", 0),
            m_stats.get("ci_95_low", 0),
            m_stats.get("ci_95_high", 0),
            m_stats.get("min", 0),
            m_stats.get("max", 0),
        ])

    writer.writerow([])
    writer.writerow(["MUNICIPAL DISCLAIMER", report.get("municipal_disclaimer_en", "")])

    return output.getvalue()


def export_report_html(report: DecisionReport, language: str = "en") -> str:
    """
    Generates a standalone, beautifully styled municipal printable HTML document
    configured with @media print CSS for direct browser printing or PDF saving.
    """
    is_ru = language == "ru"
    exec_summary = report.get("executive_summary", {})
    ev_status = report.get("evidence_status", {})
    calib_status = report.get("calibration_status", {})
    next_action = report.get("next_action", {})
    mvr = report.get("model_vs_reality", {})
    policy_audit = report.get("policy_audit", {})
    metric_rows = report.get("metric_comparison", [])
    tradeoffs = report.get("tradeoffs", {})
    robustness = report.get("robustness", {})
    methodology = report.get("methodology", {})
    limitations = report.get("limitations", {})
    ai_analysis = report.get("ai_analysis")
    spatial = report.get("spatial_scope", {})

    report_id = report.get("report_id", "")
    created_at = report.get("created_at", "")[:10]

    title = "ОТЧЕТ О ПРИНЯТИИ РЕШЕНИЯ" if is_ru else "MUNICIPAL DECISION REPORT"
    subtitle = "Цифровой двойник и интеллектуальная оптимизация мобильности" if is_ru else "Urban Mobility Intelligence & Digital Twin Platform"
    
    rows_html = ""
    for r in metric_rows:
        name = r.get("name_ru" if is_ru else "name_en", r.get("key"))
        pct = r.get("percentage_change", 0)
        is_imp = r.get("is_improvement", False)
        color = "#16a34a" if is_imp else ("#dc2626" if abs(pct) > 0.1 else "#64748b")
        sign = "+" if pct > 0 else ""
        arrow = "↓" if r.get("direction") == "minimize" and is_imp else ("↑" if is_imp else "→")
        
        rows_html += f"""
        <tr>
            <td><strong>{name}</strong></td>
            <td>{r.get('baseline', 0)} {r.get('unit', '')}</td>
            <td>{r.get('optimized', 0)} {r.get('unit', '')}</td>
            <td style="color: {color}; font-weight: bold;">{arrow} {sign}{pct}%</td>
            <td><span class="badge {r.get('provenance', '').lower()}">{r.get('provenance', '')}</span></td>
        </tr>
        """

    weights_html = ""
    for k, v in policy_audit.get("policy_weights", {}).items():
        k_label = "Мобильность" if k == "mobility" and is_ru else ("Экология" if k == "environment" and is_ru else ("Доступность" if k == "accessibility" and is_ru else k.capitalize()))
        weights_html += f"<span><strong>{k_label}:</strong> {int(v*100)}%</span> &nbsp;|&nbsp; "

    # Trade-offs HTML
    improved_list = "".join(f"<li>🟢 {item.get('name_ru' if is_ru else 'name_en', item.get('name', ''))}: {item.get('change_pct', item.get('value', ''))}%</li>" for item in tradeoffs.get("improved", []))
    worsened_list = "".join(f"<li>🟡 {item.get('name_ru' if is_ru else 'name_en', item.get('name', ''))}: +{abs(item.get('change_pct', item.get('value', 0)))}%</li>" for item in tradeoffs.get("worsened", []))

    # Robustness HTML
    rob_stats_html = ""
    for k, s in robustness.get("stats", {}).items():
        k_name = next((m["name_ru" if is_ru else "name_en"] for m in metric_rows if m["key"] == k), k)
        rob_stats_html += f"""
        <tr>
            <td><strong>{k_name}</strong></td>
            <td>{s.get('mean', 0)}</td>
            <td>±{s.get('std_dev', 0)}</td>
            <td>[{s.get('ci_95_low', 0)}, {s.get('ci_95_high', 0)}]</td>
            <td>{s.get('min', 0)} / {s.get('max', 0)}</td>
        </tr>
        """

    # Model vs Reality HTML
    mvr_rows_html = ""
    for obs in mvr.get("observed_metrics", []):
        name = obs.get("name_ru" if is_ru else "name_en", "")
        mvr_rows_html += f"<tr><td><span class='badge observed'>OBSERVED</span></td><td><strong>{name}</strong></td><td>{obs.get('value', '')} {obs.get('unit', '')}</td><td>{obs.get('source', '')}</td><td>{obs.get('calibration_state', '')}</td></tr>"
    for sim in mvr.get("simulated_metrics", []):
        name = sim.get("name_ru" if is_ru else "name_en", "")
        mvr_rows_html += f"<tr><td><span class='badge simulated'>SIMULATED</span></td><td><strong>{name}</strong></td><td>{sim.get('value', '')} {sim.get('unit', '')}</td><td>{sim.get('source', '')}</td><td>{sim.get('calibration_state', '')}</td></tr>"
    for der in mvr.get("derived_metrics", []):
        name = der.get("name_ru" if is_ru else "name_en", "")
        mvr_rows_html += f"<tr><td><span class='badge estimated'>DERIVED</span></td><td><strong>{name}</strong></td><td>{der.get('value', '')} {der.get('unit', '')}</td><td>{der.get('source', '')}</td><td>{der.get('calibration_state', '')}</td></tr>"

    # Policy Comparison HTML
    policy_comp = report.get("policy_comparison") or {}
    policy_comp_html = ""
    if policy_comp:
        p_rows = ""
        for p_k, p_v in policy_comp.items():
            if isinstance(p_v, dict):
                p_name = p_v.get("policy_name_ru" if is_ru else "policy_name", p_k.upper())
                p_winner = p_v.get("best_candidate_label", "")
                p_score = float(p_v.get("overall_score", 0.0))
                p_delay = float(p_v.get("average_waiting_seconds", 0.0))
                p_co2 = float(p_v.get("co2_kg", 0.0))
                p_tp = float(p_v.get("throughput_vehicles_per_hour", 0.0))
                p_why = p_v.get("why_won_ru" if is_ru else "why_won_en", p_v.get("why_won", ""))
                p_rows += f"""
                <tr>
                    <td><strong>{p_v.get('icon', '🎯')} {p_name}</strong></td>
                    <td><span style="color: #0284c7; font-weight: 600;">{p_winner}</span></td>
                    <td style="font-weight: 700; color: {'#16a34a' if p_score >= 0 else '#dc2626'};">{p_score:+.1f}%</td>
                    <td>{p_delay:.1f}s</td>
                    <td>{p_co2:.1f}kg</td>
                    <td>{p_tp:.0f}</td>
                    <td style="font-size: 10px; color: #475569;">{p_why}</td>
                </tr>
                """
        policy_comp_html = f"""
        <div class="section-card">
            <h3>⚖️ {('Сравнение исходов по политикам (FLOW vs ECO vs BALANCED)' if is_ru else 'Policy Outcome Comparison (FLOW vs ECO vs BALANCED)')}</h3>
            <table>
                <thead>
                    <tr>
                        <th>{('Политика' if is_ru else 'Policy')}</th>
                        <th>{('Победитель' if is_ru else 'Winner Candidate')}</th>
                        <th>{('Оценка' if is_ru else 'Score')}</th>
                        <th>{('Задержка' if is_ru else 'Delay')}</th>
                        <th>CO₂</th>
                        <th>{('Поток' if is_ru else 'Throughput')}</th>
                        <th>{('Обоснование выбора' if is_ru else 'Selection Rationale')}</th>
                    </tr>
                </thead>
                <tbody>
                    {p_rows}
                </tbody>
            </table>
        </div>
        """

    # AI Analysis HTML
    ai_html = ""
    if ai_analysis:
        prov = ai_analysis.get("provenance", "AI ANALYSIS")
        summ = ai_analysis.get("summary", "")
        rec = ai_analysis.get("recommendation", "")
        ai_html = f"""
        <div class="section-card">
            <h3>🤖 {('ИИ-Интерпретация' if is_ru else 'Strategic AI Interpretation')} <span class="badge ai">{prov}</span></h3>
            <p style="margin-bottom: 8px;">{summ}</p>
            <p style="margin-bottom: 0;"><strong>{('Рекомендация:' if is_ru else 'Recommendation:')}</strong> {rec}</p>
        </div>
        """


    ev_badge_color = "#16a34a" if ev_status.get("level") == "HIGH" else ("#d97706" if ev_status.get("level") == "MODERATE" else "#dc2626")

    html = f"""<!DOCTYPE html>
<html lang="{language}">
<head>
    <meta charset="UTF-8">
    <title>UrbanMind Decision Report — {report_id}</title>
    <style>
        @page {{ size: A4; margin: 1.2cm; }}
        body {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
            color: #1e293b;
            line-height: 1.45;
            background: #fff;
            margin: 0;
            padding: 20px;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            border-bottom: 2px solid #0284c7;
            padding-bottom: 12px;
            margin-bottom: 16px;
        }}
        .brand {{ font-size: 22px; font-weight: 800; color: #0f172a; letter-spacing: 0.05em; }}
        .brand span {{ color: #0284c7; }}
        .doc-title {{ font-size: 13px; font-weight: 600; color: #64748b; text-transform: uppercase; }}
        .meta-box {{ text-align: right; font-size: 11px; color: #64748b; }}
        .breadcrumb {{ font-size: 12px; font-weight: 600; color: #0284c7; margin-bottom: 12px; }}
        .section-card {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 14px;
            margin-bottom: 14px;
            page-break-inside: avoid;
        }}
        .section-card h3 {{ margin-top: 0; font-size: 14px; color: #0f172a; border-bottom: 1px solid #cbd5e1; padding-bottom: 4px; margin-bottom: 8px; }}
        .kpi-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 10px; }}
        .kpi-box {{ background: #fff; border: 1px solid #e2e8f0; padding: 8px 10px; border-radius: 4px; }}
        .kpi-label {{ font-size: 10px; color: #64748b; text-transform: uppercase; }}
        .kpi-value {{ font-size: 15px; font-weight: 700; color: #0284c7; margin-top: 2px; }}
        .action-box {{
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            border-left: 4px solid #0284c7;
            padding: 10px 12px;
            border-radius: 4px;
            margin-top: 8px;
        }}
        .disclaimer-box {{
            background: #fffbeb;
            border: 1px solid #fef3c7;
            padding: 8px 10px;
            border-radius: 4px;
            font-size: 10px;
            color: #92400e;
            margin-top: 10px;
        }}
        table {{ width: 100%; border-collapse: collapse; font-size: 11px; margin-top: 6px; }}
        th, td {{ padding: 6px 8px; text-align: left; border-bottom: 1px solid #e2e8f0; }}
        th {{ background: #f1f5f9; color: #475569; font-weight: 600; }}
        .badge {{
            display: inline-block;
            padding: 2px 5px;
            border-radius: 4px;
            font-size: 9px;
            font-weight: 700;
            text-transform: uppercase;
        }}
        .badge.direct {{ background: #e0f2fe; color: #0369a1; }}
        .badge.simulated {{ background: #dcfce7; color: #15803d; }}
        .badge.estimated {{ background: #fef3c7; color: #b45309; }}
        .badge.observed {{ background: #e0e7ff; color: #4338ca; }}
        .badge.ai {{ background: #f3e8ff; color: #7e22ce; }}
        .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
        .footer {{
            margin-top: 24px;
            border-top: 1px solid #e2e8f0;
            padding-top: 8px;
            font-size: 10px;
            color: #94a3b8;
            display: flex;
            justify-content: space-between;
        }}
        @media print {{
            body {{ padding: 0; background: #fff; }}
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <div class="brand">URBAN<span>MIND</span></div>
            <div class="doc-title">{title}</div>
            <div style="font-size: 10px; color: #64748b;">{subtitle}</div>
        </div>
        <div class="meta-box">
            <div><strong>ID:</strong> {report_id}</div>
            <div><strong>{('Дата:' if is_ru else 'Date:')}</strong> {created_at}</div>
            <div><strong>{('Сценарий:' if is_ru else 'Scenario:')}</strong> {report.get('scenario_id', '').upper()}</div>
        </div>
    </div>

    <div class="breadcrumb">
        📍 {spatial.get('city_name', 'Tashkent')} › {spatial.get('district_name', 'Central District')} › {spatial.get('corridor_name', 'Central Corridor')}
    </div>

    <!-- 15-SECOND DECISION BRIEF -->
    <div class="section-card" style="border: 2px solid #0284c7;">
        <h3>⚡ {('Краткое резюме для принятия решения (Decision Brief)' if is_ru else 'Decision Brief (15-Second Overview)')}</h3>
        <p style="margin-bottom: 6px;"><strong>{('Кандидат для полевой валидации:' if is_ru else 'Simulation-Supported Candidate:')}</strong> <span style="color: #0284c7; font-weight: bold;">{exec_summary.get('recommended_intervention_ru' if is_ru else 'recommended_intervention', '')}</span></p>
        
        <div class="kpi-grid">
            <div class="kpi-box">
                <div class="kpi-label">{('Эффект задержки' if is_ru else 'Delay Impact')}</div>
                <div class="kpi-value">{exec_summary.get('primary_result_ru' if is_ru else 'primary_result', '')}</div>
            </div>
            <div class="kpi-box">
                <div class="kpi-label">{('Экологический эффект' if is_ru else 'Environmental Impact')}</div>
                <div class="kpi-value">{exec_summary.get('environmental_result_ru' if is_ru else 'environmental_result', '')}</div>
            </div>
            <div class="kpi-box">
                <div class="kpi-label">{('Сила доказательств' if is_ru else 'Evidence Strength')}</div>
                <div class="kpi-value" style="color: {ev_badge_color};">{ev_status.get('level', 'MODERATE')} ({ev_status.get('score', 0)}/100)</div>
            </div>
        </div>

        <p style="font-size: 11px; margin-bottom: 4px;"><strong>{('Компромисс:' if is_ru else 'Trade-off:')}</strong> {exec_summary.get('main_tradeoff_ru' if is_ru else 'main_tradeoff', '')}</p>
        <p style="font-size: 11px; margin-bottom: 4px;"><strong>{('Статус калибровки:' if is_ru else 'Calibration Status:')}</strong> <span style="font-weight: 700; color: #d97706;">{calib_status.get('status', 'UNCALIBRATED')}</span> ({('натурные детекторы не подключены' if is_ru else 'field traffic counts unavailable')})</p>

        <div class="action-box">
            <strong>🎯 {('Рекомендуемое следующее действие:' if is_ru else 'Recommended Next Action:')}</strong> {next_action.get('title_ru' if is_ru else 'title_en', '')}<br/>
            <span style="font-size: 10.5px; color: #334155;">{next_action.get('rationale_ru' if is_ru else 'rationale_en', '')}</span>
        </div>

        <div class="disclaimer-box">
            ⚖️ <strong>{('Правовая оговорка:' if is_ru else 'Municipal Disclaimer:')}</strong> {report.get('municipal_disclaimer_ru' if is_ru else 'municipal_disclaimer_en', '')}
        </div>
    </div>

    <!-- MODEL VS REALITY -->
    <div class="section-card">
        <h3>🔍 {('Классификация данных (Модель vs Реальность)' if is_ru else 'Model vs Reality Data Classification')}</h3>
        <table>
            <thead>
                <tr>
                    <th>{('Класс' if is_ru else 'Class')}</th>
                    <th>{('Параметр' if is_ru else 'Metric')}</th>
                    <th>{('Значение' if is_ru else 'Value')}</th>
                    <th>{('Источник' if is_ru else 'Source')}</th>
                    <th>{('Статус калибровки' if is_ru else 'State')}</th>
                </tr>
            </thead>
            <tbody>
                {mvr_rows_html}
            </tbody>
        </table>
    </div>

    <!-- POLICY AUDIT -->
    <div class="section-card">
        <h3>🎯 {('Аудит политики оптимизации' if is_ru else 'Optimization Policy & Verification')}</h3>
        <p style="margin-bottom: 6px;"><strong>{('Активная политика:' if is_ru else 'Active Policy:')}</strong> {policy_audit.get('policy_name_ru' if is_ru else 'policy_name', '')} | <strong>{('Статус ограничений:' if is_ru else 'Constraints:')}</strong> <span style="color: #16a34a; font-weight: bold;">{policy_audit.get('constraint_status', 'PASS')}</span></p>
        <p style="font-size: 11px; color: #475569; margin: 0;">{weights_html}</p>
    </div>

    {policy_comp_html}


    <!-- METRIC COMPARISON -->
    <div class="section-card">
        <h3>📊 {('Сравнение ключевых метрик (Базовый vs Оптимизированный)' if is_ru else 'Key Metrics Comparison (Baseline vs Optimized)')}</h3>
        <table>
            <thead>
                <tr>
                    <th>{('Метрика' if is_ru else 'Metric')}</th>
                    <th>{('Базовый' if is_ru else 'Baseline')}</th>
                    <th>{('Оптимизировано' if is_ru else 'Optimized')}</th>
                    <th>{('Эффект (Δ)' if is_ru else 'Effect (Δ)')}</th>
                    <th>{('Происхождение' if is_ru else 'Provenance')}</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>

    <div class="two-col">
        <div class="section-card">
            <h3>⚖️ {('Анализ компромиссов (Trade-offs)' if is_ru else 'Trade-off Breakdown')}</h3>
            <p style="font-size: 11px; margin-bottom: 6px;">{tradeoffs.get('verdict_ru' if is_ru else 'verdict_en', '')}</p>
            <ul style="font-size: 11px; padding-left: 16px; margin: 0;">
                {improved_list or "<li>Нет значимых улучшений</li>"}
                {worsened_list or "<li>Нет значимых ухудшений</li>"}
            </ul>
        </div>
        <div class="section-card">
            <h3>📈 {('Устойчивость симуляции (Robustness)' if is_ru else 'Statistical Evidence & Robustness')}</h3>
            <p style="font-size: 11px; margin-bottom: 6px;">{robustness.get('methodology_note_ru' if is_ru else 'methodology_note_en', '')}</p>
            <table>
                <thead>
                    <tr>
                        <th>{('Метрика' if is_ru else 'Metric')}</th>
                        <th>Mean</th>
                        <th>Std</th>
                        <th>95% CI</th>
                        <th>Min/Max</th>
                    </tr>
                </thead>
                <tbody>
                    {rob_stats_html}
                </tbody>
            </table>
        </div>
    </div>

    {ai_html}

    <div class="section-card">
        <h3>🔬 {('Методология и ограничения' if is_ru else 'Methodology & Modeling Assumptions')}</h3>
        <div style="font-size: 11px; display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
            <div>
                <p style="margin: 0 0 4px 0;"><strong>{('Движок:' if is_ru else 'Engine:')}</strong> {methodology.get('simulation_engine', '')}</p>
                <p style="margin: 0 0 4px 0;"><strong>{('Модель выбросов:' if is_ru else 'Emissions:')}</strong> {methodology.get('emission_model', '')}</p>
                <p style="margin: 0;"><strong>{('Длительность:' if is_ru else 'Steps:')}</strong> {methodology.get('duration_steps', 300)} ({methodology.get('warmup_steps', 0)} warmup)</p>
            </div>
            <div>
                <p style="margin: 0 0 4px 0;"><strong>{('Классы данных:' if is_ru else 'Data Classes:')}</strong> DIRECT (TraCI), SIMULATED (HBEFA), OBSERVED (Sensors), DERIVED (Indices)</p>
                <p style="margin: 0; color: #64748b;">
                    {('Откалибровано под геометрию Ташкента. Показания датчиков воздуха представляют фоновые натурные уровни.' if is_ru else 'Calibrated to Tashkent corridor geometry. Physical air sensors reflect ambient background levels.')}
                </p>
            </div>
        </div>
    </div>

    <div class="footer">
        <div>URBANMIND DECISION INTELLIGENCE PLATFORM — MUNICIPAL DIGITAL TWIN</div>
        <div>{report_id}</div>
    </div>
</body>
</html>
"""
    return html
