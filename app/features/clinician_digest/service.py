"""
app.features.clinician_digest.service — SOAP-structured clinical digest generation.

This is one of the most important research-grade features. Preserved in full.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.services.repositories import DigestRepository, MedicationRepository, SupportTraceRepository
from app.services.timeline import TimelineEngine


class ClinicianDigestService:
    def __init__(self, db: Session, patient_id: int):
        self.db = db
        self.patient_id = patient_id
        self.digest_repo = DigestRepository(db, patient_id)
        self.med_repo = MedicationRepository(db, patient_id)
        self.trace_repo = SupportTraceRepository(db, patient_id)
        self.timeline = TimelineEngine(db, patient_id)

    def generate(self, window_days: int | None = None) -> Any:
        settings = get_settings()
        days = window_days or settings.default_window_days
        until = datetime.utcnow()
        since = until - timedelta(days=days)

        events = self.timeline.extract_window(since, until)
        trends = self.timeline.extract_trend(since, until)

        # Track traces
        evidence_snippets = []
        for ev in events:
            if ev.is_anomaly:
                evidence_snippets.append({
                    "text": f"Anomaly on {ev.occurred_at.date()}: {ev.summary} (Source: {ev.provenance or 'Unknown'})",
                    "entity": ev.event_category,
                    "id": getattr(ev.raw_reference, "id", None),
                })

        symptoms = [e for e in events if e.event_category == "health" and e.event_type == "symptom"]
        symptom_counter = Counter(e.summary for e in symptoms if e.summary)
        active_meds = len(self.med_repo.list_active())

        bp_trend = trends.get("blood_pressure", {})
        fg_trend = trends.get("fasting_glucose", {})
        meal_risks = trends.get("meal_risks", 0)
        adherence_misses = trends.get("adherence_misses", 0)

        lines = [
            f"# 门诊前临床摘要（近 {days} 天）",
            "",
            "## 1. Subjective (主观症状与事件记录)",
            f"- 自述症状记录次数: {len(symptoms)}",
            f"- 主要症状分布: {'；'.join(f'{k}({v}次)' for k, v in symptom_counter.items()) if symptom_counter else '暂无明显症状记录'}",
            "",
            "## 2. Objective (客观监测与依从性)",
            f"- 血压记录次数: {bp_trend.get('count', 0)}",
            f"- 空腹血糖记录次数: {fg_trend.get('count', 0)}",
            f"- 饮食高风险事件数: {meal_risks}",
            f"- 漏服药次数: {adherence_misses}",
            f"- 当前医嘱药物种类: {active_meds}",
        ]

        if bp_trend.get("count", 0) > 0:
            lines.append(f"- 近期平均血压约: {bp_trend['avg_sys']:.1f}/{bp_trend['avg_dia']:.1f} mmHg")
        if fg_trend.get("count", 0) > 0:
            lines.append(f"- 近期平均空腹血糖: {fg_trend['avg']:.1f} mmol/L")

        lines += [
            "",
            "## 3. Assessment (病情评估与异常警示)",
            "- 基于时间轴数据的趋势分析:",
        ]

        flags = []
        if (bp_trend.get("avg_sys", 0) or 0) >= 140:
            flags.append("- 【警告】血压总体偏高，需排除未规律服药或生活方式影响。")
        if (fg_trend.get("avg", 0) or 0) >= 7.0:
            flags.append("- 【警告】空腹血糖异常，需评估降糖方案强度。")
        if adherence_misses > 2:
            flags.append("- 【警告】依从性风险: 患者近期存在多次漏服药记录，需干预。")
        if meal_risks > 2:
            flags.append("- 【警告】饮食风险: 近期多次高糖/高盐饮食行为，建议进行健康教育。")

        if not flags:
            lines.append("- 目前未发现重大短期恶化趋势。患者依从性处于可接受范围。")
        else:
            lines.extend(flags)

        lines += [
            "",
            "## 4. Plan (复诊计划建议)",
            "- 若指标波动持续，建议门诊调整用药剂量。",
            "- 自动生成的科普与提醒策略已下发。重点回顾漏服药原因。",
            "",
            "## 5. Evidence Traces (异常事件溯源证据)",
        ]

        for idx, es in enumerate(evidence_snippets):
            lines.append(f"- [{idx + 1}] {es['text']}")

        if not evidence_snippets:
            lines.append("- 没有显著异常事件记录。")

        lines += [
            "",
            "---",
            "**System Note & Limitations:**",
            "*本摘要由系统自动基于患者日常数据抽取生成，仅代表记录区间内的数值规律，未涵盖患者所有线下诊疗记录。不构成独立医疗决策方案。请门诊结合患者实际情况核实重要不良事件。*",
        ]

        markdown_output = "\n".join(lines)
        digest = self.digest_repo.save(days, markdown_output)

        # Save Support Traces for this digest
        for es in evidence_snippets:
            self.trace_repo.add(
                target_entity="digest",
                target_id=digest.id,
                source_entity=es["entity"],
                source_id=es["id"],
                evidence_snippet=es["text"],
            )

        return digest
