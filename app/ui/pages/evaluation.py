"""
Evaluation page — Run benchmark datasets and view results.

Preserved from the original chronic_agent/evaluation module.
"""
import json
import streamlit as st
import random
from datetime import datetime, timedelta


def page_evaluation():
    st.markdown('<div class="section-header">🔬 评估工具</div>', unsafe_allow_html=True)
    st.caption(
        "研究级评估模块。可生成合成基准数据并运行自动化评估，"
        "测试饮食风险标注、健康数据解析和临床摘要生成的准确性。"
    )

    tab_gen, tab_run = st.tabs(["📊 生成基准数据", "▶️ 运行评估"])

    # ── Tab 1: Generate Benchmark Data ───────────────────
    with tab_gen:
        st.subheader("合成基准数据生成")
        st.markdown("""
        生成模拟中国大陆 T2DM+高血压场景的合成评估数据。
        包含：
        - **Digest 评估样本** — 模拟 14 天纵向事件用于摘要评估
        - **Meal 评估样本** — 模拟中国饮食风险标注
        - **Parsing 评估样本** — 模拟中文临床语句解析
        """)

        digest_count = st.slider("Digest 样本数量", 1, 20, 5)

        if st.button("📊 生成数据", type="primary", use_container_width=True):
            with st.spinner("正在生成合成数据..."):
                data = _generate_benchmark_data(digest_count)

            st.success(f"✅ 已生成 {len(data.get('digest_samples', []))} digest + "
                       f"{len(data.get('meal_samples', []))} meal + "
                       f"{len(data.get('parsing_samples', []))} parsing 样本")

            st.session_state.benchmark_data = data

            # Show data preview
            with st.expander("📋 数据预览"):
                st.json(data)

            # Download
            json_str = json.dumps(data, ensure_ascii=False, indent=2)
            st.download_button(
                "📥 下载 benchmark_data.json",
                data=json_str,
                file_name="benchmark_data.json",
                mime="application/json",
                use_container_width=True,
            )

    # ── Tab 2: Run Evaluation ────────────────────────────
    with tab_run:
        st.subheader("运行评估")

        data = st.session_state.get("benchmark_data")

        # Allow upload
        uploaded = st.file_uploader("上传 benchmark_data.json (或使用已生成的数据)", type=["json"])
        if uploaded:
            data = json.load(uploaded)
            st.session_state.benchmark_data = data
            st.success("✅ 数据已加载")

        if not data:
            st.info("请先生成或上传基准数据。")
            return

        if st.button("▶️ 运行 Meal 评估", type="primary", use_container_width=True):
            with st.spinner("评估中..."):
                results = _evaluate_meals(data)

            total = len(results)
            passed = sum(1 for r in results if r["passed"])
            avg_score = sum(r["score"] for r in results) / total if total else 0

            st.markdown("### 📊 评估结果")
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("总样本数", total)
            with m2:
                st.metric("通过", f"{passed}/{total}")
            with m3:
                st.metric("平均分", f"{avg_score:.2f}")

            st.divider()

            for r in results:
                icon = "✅" if r["passed"] else "❌"
                with st.expander(f"{icon} {r['sample_id']} — Score: {r['score']:.2f}"):
                    st.json(r["details"])


# ── Synthetic Data Generator ─────────────────────────────

def _generate_benchmark_data(digest_count: int = 5) -> dict:
    """Generate synthetic benchmark data."""
    digest_samples = []
    for i in range(digest_count):
        base_date = datetime.utcnow()
        events = []
        sys_bp = []

        for days_ago in range(14):
            dt = base_date - timedelta(days=days_ago)
            sys = random.randint(130, 160)
            dia = random.randint(80, 100)
            sys_bp.append(sys)
            events.append({"type": "blood_pressure", "num1": sys, "num2": dia, "occurred_at": dt.isoformat()})

            if random.random() > 0.5:
                fg = round(random.uniform(6.0, 9.5), 1)
                events.append({"type": "fasting_glucose", "num1": fg, "occurred_at": dt.isoformat()})

        avg_sys = sum(sys_bp) / len(sys_bp)
        flags = ["高血压"] if avg_sys >= 140 else []

        names = ["张三", "李四", "王五", "赵六", "陈七"]
        digest_samples.append({
            "id": f"digest_synth_{i}",
            "patient_context": {
                "name": f"{random.choice(names)}_{i}",
                "gender": random.choice(["男", "女"]),
                "age": random.randint(45, 75),
                "diagnosis_summary": "2型糖尿病，高血压三级",
            },
            "input_events": events,
            "expected_trend_sys_bp_min": avg_sys - 5,
            "expected_trend_sys_bp_max": avg_sys + 5,
            "expected_flags": flags,
            "must_include_evidence": ["bp_trend"],
        })

    meal_samples = [
        {
            "id": "meal_1",
            "patient_context": {"diagnosis_summary": "2型糖尿病"},
            "input_text": "晚饭喝了全糖奶茶，还吃了两碗米饭",
            "expected_tags": ["高糖饮食", "高碳水"],
            "forbidden_tags": [],
        },
        {
            "id": "meal_2",
            "patient_context": {"diagnosis_summary": "高血压"},
            "input_text": "中午吃了一份很咸的腊肉炒饭，加了腐乳",
            "expected_tags": ["高盐"],
            "forbidden_tags": [],
        },
        {
            "id": "meal_3",
            "patient_context": {},
            "input_text": "早上吃了水煮蛋，一杯无糖豆浆，半截玉米",
            "expected_tags": [],
            "forbidden_tags": ["高糖饮食", "高碳水"],
        },
    ]

    parsing_samples = [
        {
            "id": "parse_1",
            "patient_context": {},
            "input_text": "今天早餐后吃了二甲双胍 500mg，感觉还好",
            "expected_medications": [{"medicine_name": "二甲双胍", "dose": "500mg"}],
        },
        {
            "id": "parse_2",
            "patient_context": {},
            "input_text": "早上血压 148/92，有点头晕",
            "expected_health_metrics": [{"type": "blood_pressure", "num1": 148.0, "num2": 92.0}],
        },
    ]

    return {
        "digest_samples": digest_samples,
        "meal_samples": meal_samples,
        "parsing_samples": parsing_samples,
    }


def _evaluate_meals(data: dict) -> list[dict]:
    """Run meal risk evaluation using the parser."""
    from app.services.parser import detect_meal_risks

    results = []
    for sample in data.get("meal_samples", []):
        extracted_tags = detect_meal_risks(sample["input_text"])

        # Check expected tags are found
        expected = sample.get("expected_tags", [])
        forbidden = sample.get("forbidden_tags", [])

        has_expected = all(any(e in t for t in extracted_tags) for e in expected) if expected else True
        no_forbidden = not any(any(f in t for t in extracted_tags) for f in forbidden)

        score = 1.0 if (has_expected and no_forbidden) else 0.0

        results.append({
            "sample_id": sample["id"],
            "passed": has_expected and no_forbidden,
            "score": score,
            "details": {
                "extracted": extracted_tags,
                "expected": expected,
                "forbidden": forbidden,
            },
        })
    return results
