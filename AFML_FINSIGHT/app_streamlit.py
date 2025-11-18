"""Streamlit frontend for FinSight pipeline."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List
import sys

# Ensure project root is on sys.path when running via `streamlit run AFML_FINSIGHT/app_streamlit.py`
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import plotly.io as pio
import streamlit as st

from AFML_FINSIGHT.evaluation.runner import evaluate_pipeline_run
from AFML_FINSIGHT.pipeline.orchestrator import FinSightPipeline
from AFML_FINSIGHT.tools.symbols import resolve_ticker


st.set_page_config(page_title="FinSight Research Studio", layout="wide", page_icon="📊")
st.title("📊 FinSight Research Studio")

with st.sidebar:
    st.header("Run Configuration")
    company = st.text_input("Company Name", value="NVIDIA")
    analysis_goal = st.text_area(
        "Analysis Goal",
        value="Assess the company's financial strength, market positioning, and growth outlook.",
        height=120,
    )
    fred_series_input = st.text_input(
        "FRED Series (label=ID, comma separated)", value="gdp=GDP, unemployment=UNRATE"
    )
    enable_visualization = st.checkbox("Generate price visualization", value=True)
    log_to_file = st.checkbox("Record variable memory log", value=False)

    run_button = st.button("Run FinSight Pipeline", type="primary")


@st.cache_data(show_spinner=False)
def parse_fred_series(text: str) -> Dict[str, str]:
    pairs = [item.strip() for item in text.split(",") if item.strip()]
    mapping: Dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            continue
        label, series_id = pair.split("=", 1)
        mapping[label.strip()] = series_id.strip()
    return mapping


if run_button:
    if not company:
        st.error("Please provide a company name.")
    else:
        # Resolve ticker from company name
        try:
            ticker = resolve_ticker(company)
            st.caption(f"Resolved ticker: {ticker}")
        except Exception as e:
            st.error(f"Could not resolve ticker for '{company}': {e}")
            st.stop()

        fred_series = parse_fred_series(fred_series_input)
        fred_series = fred_series or None

        with st.spinner("Running FinSight pipeline. This may take a few minutes..."):
            log_path = Path("logs/vars.jsonl") if log_to_file else None
            if log_path:
                log_path.parent.mkdir(parents=True, exist_ok=True)
            pipeline = FinSightPipeline(log_path=log_path)

            viz_spec = viz_goal = None
            if enable_visualization:
                viz_spec = {"type": "line", "y": ["Close"], "title": f"{ticker} Price Performance"}
                viz_goal = f"Produce a professional stock trend visualization for {ticker}."

            artifacts = pipeline.run(
                company_name=company,
                ticker=ticker,
                analysis_goal=analysis_goal,
                fred_series_ids=fred_series,
                visualization_spec=viz_spec,
                visualization_goal=viz_goal,
            )
            scores = evaluate_pipeline_run(
                pipeline,
                artifacts,
            )

        st.success("Pipeline run complete.")

        variable_space = pipeline.orchestrator.variable_space
        memo_uid = artifacts.get("memo_uid")
        if memo_uid:
            memo_payload = variable_space.get(memo_uid).value
            memo_markdown = memo_payload.get("markdown") if isinstance(memo_payload, dict) else str(memo_payload)
            st.subheader("Investment Memo")
            st.markdown(memo_markdown)

        if enable_visualization and artifacts.get("visualization_uid"):
            viz_payload = variable_space.get(artifacts["visualization_uid"]).value
            iterations: List[Dict[str, str]] = viz_payload.get("iterations", []) if isinstance(viz_payload, dict) else []
            if iterations:
                st.subheader("Visualization Refinement")
                for iteration in iterations:
                    fig_json = iteration.get("figure_json")
                    feedback = iteration.get("feedback")
                    iter_key = f"viz_iter_{iteration.get('iteration', 'n')}"
                    if fig_json:
                        fig = pio.from_json(fig_json)
                        st.plotly_chart(fig, use_container_width=True, key=iter_key)
                    if feedback:
                        st.info(f"Iteration {iteration['iteration']}: {feedback}", icon="ℹ️")

        st.subheader("Evaluation Scores")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Factual Accuracy", scores["factual_accuracy_score"])
            st.json(scores["factual_accuracy"])
        with col2:
            st.metric("Information Effectiveness", scores["information_effectiveness_score"])
            st.json(scores["information_effectiveness"])
        with col3:
            st.metric("Presentation Quality", scores["presentation_quality_score"])
            st.json(scores["presentation_quality"])

        with st.expander("Raw Artifacts", expanded=False):
            st.json(artifacts)
        with st.expander("Variable Snapshot", expanded=False):
            st.text(json.dumps(variable_space.snapshot(), indent=2, default=str))
        if log_to_file:
            st.info("Variable events recorded to logs/vars.jsonl")
else:
    st.write("Configure parameters in the sidebar and click **Run FinSight Pipeline** to generate a report.")
