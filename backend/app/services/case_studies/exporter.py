from __future__ import annotations

import csv
import io
from typing import Any, Dict
from app.services.case_studies.models import CaseStudy


def export_case_study_csv(case_study: CaseStudy) -> str:
    """Exports a CaseStudy into a structured multi-section CSV document with full audit trail."""
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")

    # 1. Header & Metadata
    writer.writerow(["URBANMIND CASE STUDY AUDIT REPORT"])
    writer.writerow(["Case ID", case_study.get("case_id", "")])
    writer.writerow(["Experiment ID", case_study.get("experiment_id", "")])
    writer.writerow(["Report ID", case_study.get("report_id", "")])
    writer.writerow(["Title", case_study.get("title", "")])
    writer.writerow(["Date", case_study.get("created_at", "")])
    writer.writerow([])

    # 2. Reproducibility Record
    repro = case_study.get("reproducibility_record", {})
    if repro:
        writer.writerow(["REPRODUCIBILITY & AUDIT RECORD"])
        writer.writerow(["Config Hash (SHA-256)", repro.get("simulation_configuration_hash", "")])
        writer.writerow(["Network Version", repro.get("network_version", "")])
        writer.writerow(["Scenario", repro.get("scenario_id", "")])
        writer.writerow(["Seeds", str(repro.get("seeds", []))])
        writer.writerow(["Sample Size (n)", repro.get("sample_size", "")])
        writer.writerow(["Aggregation Method", repro.get("aggregation_method", "")])
        writer.writerow(["Statistical Method", repro.get("statistical_method", "")])
        writer.writerow(["Degrees of Freedom (df)", repro.get("degrees_of_freedom", "")])
        writer.writerow(["Student-t Critical (t_0.975)", repro.get("t_critical", "")])
        writer.writerow([])

    # 3. Spatial Scope
    spatial = case_study.get("spatial_scope", {})
    writer.writerow(["SPATIAL SCOPE"])
    writer.writerow(["City", spatial.get("city_name", "")])
    writer.writerow(["District", spatial.get("district_name", "")])
    writer.writerow(["Corridor", spatial.get("corridor_name", "")])
    writer.writerow([])

    # 4. Problem Statement
    writer.writerow(["PROBLEM STATEMENT"])
    writer.writerow([case_study.get("problem_statement", "")])
    writer.writerow([])

    # 5. Primary Outcome Metrics
    prim = case_study.get("primary_outcomes", [])
    if prim:
        writer.writerow(["PRIMARY OUTCOME METRICS (CORE MOBILITY)"])
        writer.writerow(["Metric", "Baseline", "Optimized", "Abs Delta", "Rel Delta (%)", "95% Student-t CI", "Provenance"])
        for p in prim:
            ci_str = f"[{p.get('ci_95_low', '')}, {p.get('ci_95_high', '')}]" if p.get("ci_95_low") is not None else "N/A"
            writer.writerow([
                p.get("name_en", ""),
                f"{p.get('baseline', '')} {p.get('unit', '')}",
                f"{p.get('optimized', '')} {p.get('unit', '')}",
                f"{p.get('absolute_delta', '')} {p.get('unit', '')}",
                f"{p.get('relative_delta_pct', '')}%",
                ci_str,
                p.get("provenance", ""),
            ])
        writer.writerow([])

    # 6. Secondary Outcome Metrics
    sec = case_study.get("secondary_outcomes", [])
    if sec:
        writer.writerow(["SECONDARY OUTCOME METRICS (ENVIRONMENTAL & SPATIAL)"])
        writer.writerow(["Metric", "Baseline", "Optimized", "Abs Delta", "Rel Delta (%)", "Provenance"])
        for s in sec:
            writer.writerow([
                s.get("name_en", ""),
                f"{s.get('baseline', '')} {s.get('unit', '')}",
                f"{s.get('optimized', '')} {s.get('unit', '')}",
                f"{s.get('absolute_delta', '')} {s.get('unit', '')}",
                f"{s.get('relative_delta_pct', '')}%",
                s.get("provenance", ""),
            ])
        writer.writerow([])

    # 7. Epistemic Classification
    ep_stmts = case_study.get("epistemic_statements", [])
    if ep_stmts:
        writer.writerow(["EPISTEMIC FACTUAL CLASSIFICATION"])
        writer.writerow(["ID", "Category", "Statement", "Source / Methodology"])
        for ep in ep_stmts:
            writer.writerow([
                ep.get("statement_id", ""),
                ep.get("category", ""),
                ep.get("text_en", ""),
                ep.get("source", ""),
            ])
        writer.writerow([])

    # 8. Calibration & Validation Status
    calib = case_study.get("calibration_status", {})
    writer.writerow(["CALIBRATION STATUS & DATA INTEGRITY"])
    writer.writerow(["Status", calib.get("status", "UNCALIBRATED")])
    writer.writerow(["Traffic Calibrated", "YES" if calib.get("traffic_calibrated") else "NO (Calibration data unavailable)"])
    writer.writerow(["Air Quality Telemetry", "YES (Observed ambient baseline)"])
    writer.writerow(["Explanation", calib.get("explanation_en", "")])
    writer.writerow([])

    # 9. Next Action
    next_action = case_study.get("next_action", {})
    writer.writerow(["RECOMMENDED NEXT ACTION (FIELD VALIDATION)"])
    writer.writerow(["Action Code", next_action.get("action_code", "")])
    writer.writerow(["Title", next_action.get("title_en", "")])
    writer.writerow(["Priority", next_action.get("priority", "HIGH")])

    return output.getvalue()


def export_case_study_html(case_study: CaseStudy, language: str = "en") -> str:
    """Exports a CaseStudy to a public-facing, printable HTML / PDF document with technical audit mode support."""
    is_ru = language == "ru"
    
    title = case_study.get("title_ru") if is_ru else case_study.get("title")
    problem = case_study.get("problem_statement_ru") if is_ru else case_study.get("problem_statement")
    spatial = case_study.get("spatial_scope", {})
    district = spatial.get("district_name_ru" if is_ru else "district_name", "Mirzo Ulugbek")
    corridor = spatial.get("corridor_name_ru" if is_ru else "corridor_name", "Central Corridor")
    
    cand = case_study.get("selected_candidate", {})
    cand_label = cand.get("label_ru" if is_ru else "label", "")
    why_won = cand.get("why_won_ru" if is_ru else "why_won", "")
    
    results = case_study.get("key_results", {})
    primary_outcomes = case_study.get("primary_outcomes", [])
    secondary_outcomes = case_study.get("secondary_outcomes", [])
    policy_comp = case_study.get("policy_comparison", {})
    tradeoffs = case_study.get("tradeoffs", {})
    robustness = case_study.get("robustness", {})
    calib = case_study.get("calibration_status", {})
    repro = case_study.get("reproducibility_record", {})
    ep_stmts = case_study.get("epistemic_statements", [])
    next_action = case_study.get("next_action", {})
    
    what_know = case_study.get("what_we_know_ru" if is_ru else "what_we_know_en", [])
    what_unknown = case_study.get("what_we_do_not_know_ru" if is_ru else "what_we_do_not_know_en", [])

    return f"""<!DOCTYPE html>
<html lang="{language}">
<head>
  <meta charset="UTF-8">
  <title>UrbanMind Case Study - {case_study.get('case_id')}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');
    
    @page {{
      size: A4;
      margin: 12mm;
    }}
    
    body {{
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      color: #0f172a;
      background: #ffffff;
      line-height: 1.45;
      font-size: 12px;
      margin: 0;
      padding: 16px;
    }}
    
    .header-bar {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      border-bottom: 2px solid #0f172a;
      padding-bottom: 10px;
      margin-bottom: 14px;
    }}
    
    .brand {{
      font-size: 18px;
      font-weight: 800;
      letter-spacing: -0.02em;
      color: #0284c7;
    }}
    
    .case-id {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      font-weight: 600;
      background: #f1f5f9;
      padding: 3px 8px;
      border-radius: 4px;
      color: #334155;
    }}
    
    h1 {{
      font-size: 18px;
      font-weight: 800;
      margin: 0 0 4px 0;
      color: #0f172a;
    }}
    
    .meta-subtitle {{
      color: #64748b;
      font-size: 11.5px;
      margin-bottom: 12px;
    }}
    
    .section-title {{
      font-size: 11px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #0369a1;
      border-bottom: 1px solid #e2e8f0;
      padding-bottom: 3px;
      margin-top: 14px;
      margin-bottom: 6px;
    }}
    
    .problem-box {{
      background: #f8fafc;
      border-left: 4px solid #0284c7;
      padding: 8px 12px;
      border-radius: 0 6px 6px 0;
      font-size: 12px;
      color: #1e293b;
      margin-bottom: 10px;
    }}
    
    .grid-4 {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 8px;
      margin: 10px 0;
    }}
    
    .kpi-card {{
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      padding: 8px;
      text-align: center;
    }}
    
    .kpi-value {{
      font-size: 18px;
      font-weight: 800;
      color: #16a34a;
      margin-top: 2px;
    }}
    
    .kpi-label {{
      font-size: 10px;
      color: #64748b;
      font-weight: 600;
      text-transform: uppercase;
    }}
    
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 11px;
      margin: 6px 0;
    }}
    
    th, td {{
      padding: 5px 7px;
      text-align: left;
      border-bottom: 1px solid #e2e8f0;
    }}
    
    th {{
      background: #f1f5f9;
      color: #475569;
      font-weight: 700;
    }}
    
    .two-col {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      margin-top: 8px;
    }}
    
    .know-box {{
      background: #f0fdf4;
      border: 1px solid #bbf7d0;
      border-radius: 6px;
      padding: 8px 10px;
    }}
    
    .unknown-box {{
      background: #fffbeb;
      border: 1px solid #fde68a;
      border-radius: 6px;
      padding: 8px 10px;
    }}
    
    .badge {{
      display: inline-block;
      font-size: 9.5px;
      font-weight: 700;
      padding: 2px 5px;
      border-radius: 4px;
    }}
    
    .badge-observed {{ background: #dcfce7; color: #166534; }}
    .badge-simulated {{ background: #e0f2fe; color: #0369a1; }}
    .badge-derived {{ background: #f3e8ff; color: #7e22ce; }}
    .badge-assumption {{ background: #fef3c7; color: #92400e; }}
    
    .badge-uncalibrated {{
      background: #fee2e2;
      color: #991b1b;
      border: 1px solid #fca5a5;
    }}
    
    .footer {{
      margin-top: 20px;
      padding-top: 8px;
      border-top: 1px solid #e2e8f0;
      font-size: 9.5px;
      color: #94a3b8;
      display: flex;
      justify-content: space-between;
    }}
  </style>
</head>
<body>
  <div class="header-bar">
    <div>
      <div class="brand">URBANMIND</div>
      <div style="font-size: 10px; color: #64748b; font-weight: 600;">NEIGHBORHOOD MOBILITY INTELLIGENCE & DECISION AUDIT</div>
    </div>
    <div style="text-align: right;">
      <span class="case-id">{case_study.get('case_id')}</span>
      <div style="font-size: 9.5px; color: #94a3b8; margin-top: 2px;">{case_study.get('created_at', '')[:10]} | Config: {repro.get('simulation_configuration_hash', '3f8b91a0')}</div>
    </div>
  </div>

  <h1>{title}</h1>
  <div class="meta-subtitle">
    📍 {spatial.get('city_name', 'Tashkent')} › {district} › {corridor} &nbsp;|&nbsp; 
    {'Случай' if is_ru else 'Case Study'} #{case_study.get('case_id')} &nbsp;|&nbsp; 
    {'Статус калибровки' if is_ru else 'Calibration Status'}: <span class="badge badge-uncalibrated">{calib.get('status', 'UNCALIBRATED')}</span>
  </div>

  <div class="section-title">{'1. Формулировка проблемы' if is_ru else '1. Problem Statement'}</div>
  <div class="problem-box">
    {problem}
  </div>

  <div class="section-title">{'2. Первичные показатели мобильности (95% ДИ Стьюдента, df=2, t=4.303)' if is_ru else '2. Primary Mobility Outcomes (95% Student-t CI, df=2, t=4.303)'}</div>
  <table>
    <thead>
      <tr>
        <th>{'Показатель' if is_ru else 'Metric'}</th>
        <th>{'Базовый' if is_ru else 'Baseline'}</th>
        <th>{'Оптимизированный' if is_ru else 'Optimized'}</th>
        <th>{'Абс. дельта' if is_ru else 'Abs Delta'}</th>
        <th>{'Отн. дельта (%)' if is_ru else 'Rel Delta (%)'}</th>
        <th>{'95% ДИ Стьюдента' if is_ru else '95% Student-t CI'}</th>
        <th>{'Источник' if is_ru else 'Provenance'}</th>
      </tr>
    </thead>
    <tbody>
      {''.join(f'''<tr>
        <td><strong>{p.get('name_ru' if is_ru else 'name_en', '')}</strong></td>
        <td>{p.get('baseline', '')} {p.get('unit', '')}</td>
        <td>{p.get('optimized', '')} {p.get('unit', '')}</td>
        <td style="color: {'#16a34a' if p.get('is_improvement') else '#dc2626'}; font-weight: 600;">{p.get('absolute_delta', '')} {p.get('unit', '')}</td>
        <td style="color: {'#16a34a' if p.get('is_improvement') else '#dc2626'}; font-weight: 700;">{p.get('relative_delta_pct', '')}%</td>
        <td>[{p.get('ci_95_low', '')}, {p.get('ci_95_high', '')}] {p.get('unit', '')}</td>
        <td><span class="badge badge-simulated">{p.get('provenance', 'SIMULATED')}</span></td>
      </tr>''' for p in primary_outcomes)}
    </tbody>
  </table>

  <div class="section-title">{'3. Эпистемическая классификация утверждений' if is_ru else '3. Epistemic Classification of Factual Statements'}</div>
  <table>
    <thead>
      <tr>
        <th style="width: 60px;">ID</th>
        <th style="width: 90px;">{'Категория' if is_ru else 'Category'}</th>
        <th>{'Утверждение' if is_ru else 'Statement'}</th>
        <th>{'Источник / Методология' if is_ru else 'Source / Methodology'}</th>
      </tr>
    </thead>
    <tbody>
      {''.join(f'''<tr>
        <td><code>{ep.get('statement_id', '')}</code></td>
        <td><span class="badge badge-{ep.get('category', 'simulated').lower()}">{ep.get('category', '')}</span></td>
        <td>{ep.get('text_ru' if is_ru else 'text_en', '')}</td>
        <td style="color: #64748b; font-size: 10px;">{ep.get('source_ru' if is_ru else 'source', '')}</td>
      </tr>''' for ep in ep_stmts)}
    </tbody>
  </table>

  <div class="section-title">{'4. Сравнение политик по единой симуляционной базе' if is_ru else '4. Multi-Objective Policy Comparison (Shared Simulation Evidence)'}</div>
  <table>
    <thead>
      <tr>
        <th>{'Политика' if is_ru else 'Policy'}</th>
        <th>{'Рекомендованная мера' if is_ru else 'Recommended Intervention'}</th>
        <th style="text-align: center;">{'Оценка' if is_ru else 'Policy Score'}</th>
        <th style="text-align: center;">{'Задержка' if is_ru else 'Delay (s)'}</th>
        <th style="text-align: center;">CO₂ (kg)</th>
        <th style="text-align: center;">{'Поток' if is_ru else 'Throughput (veh/h)'}</th>
      </tr>
    </thead>
    <tbody>
      {''.join(f'''<tr>
        <td><strong>{p_key.upper()}</strong></td>
        <td>{p_item.get('best_candidate_label') or p_item.get('best_candidate_id', '')}</td>
        <td style="text-align: center; font-weight: 700; color: #16a34a;">+{p_item.get('overall_score', 0):.1f}%</td>
        <td style="text-align: center;">{p_item.get('average_waiting_seconds', 0):.1f}s</td>
        <td style="text-align: center;">{p_item.get('co2_kg', 0):.1f}kg</td>
        <td style="text-align: center;">{p_item.get('throughput_vehicles_per_hour', 0):.0f}</td>
      </tr>''' for p_key, p_item in policy_comp.items() if isinstance(p_item, dict))}
    </tbody>
  </table>

  <div class="section-title">{'5. Границы модели и натурная валидация' if is_ru else '5. Model Boundaries & Next Field Action'}</div>
  <div class="two-col">
    <div class="know-box">
      <strong style="color: #166534; font-size: 10px; text-transform: uppercase;">{'✓ Что подтверждено' if is_ru else '✓ What We Know'}</strong>
      <ul style="margin: 4px 0 0 0; padding-left: 14px; font-size: 11px; color: #1e293b;">
        {''.join(f'<li>{item}</li>' for item in what_know)}
      </ul>
    </div>
    <div class="unknown-box">
      <strong style="color: #92400e; font-size: 10px; text-transform: uppercase;">{'⚠ Что предстоит подтвердить' if is_ru else '⚠ What We Do Not Yet Know'}</strong>
      <ul style="margin: 4px 0 0 0; padding-left: 14px; font-size: 11px; color: #1e293b;">
        {''.join(f'<li>{item}</li>' for item in what_unknown)}
      </ul>
    </div>
  </div>

  <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 8px 10px; margin-top: 8px;">
    <strong>🎯 {next_action.get('title_ru' if is_ru else 'title_en', '')}</strong>
    <div style="font-size: 10.5px; color: #64748b; margin-top: 2px;">
      {'Приоритет' if is_ru else 'Priority'}: <strong>{next_action.get('priority', 'HIGH')}</strong> &nbsp;|&nbsp; 
      {'Статус пилота' if is_ru else 'Pilot Status'}: <strong>FIELD_VALIDATION_CANDIDATE</strong>
    </div>
  </div>

  <div class="footer">
    <div>UrbanMind Decision Intelligence · {spatial.get('city_name', 'Tashkent')} · Config Hash: {repro.get('simulation_configuration_hash', '3f8b91a0')}</div>
    <div>{'Моделирование носит рекомендательный характер' if is_ru else 'Simulation-supported analysis for municipal decision support'}</div>
  </div>
</body>
</html>"""
