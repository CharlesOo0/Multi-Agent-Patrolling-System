import json
import pandas as pd
import streamlit as st
import plotly.express as px
import os

st.set_page_config(page_title="Stats", layout="wide", initial_sidebar_state="expanded")

st.title("Simulation Stats")

left, right = st.columns(2)

# Prefer loading saved JSONs from `src/streamlit/saves` if present.
with left:
    base_dir = os.path.dirname(__file__)
    saves_dir = os.path.join(base_dir, "saves")
    saved_files = []
    if os.path.exists(saves_dir):
        saved_files = sorted(
            [f for f in os.listdir(saves_dir) if f.lower().endswith(".json")]
        )

    all_data = {}

    if saved_files:
        st.info(f"Found {len(saved_files)} saved JSON file(s) in `{saves_dir}`")
        selected = st.multiselect(
            "Select saved JSON files to load", saved_files, default=saved_files[-1]
        )
        for name in selected:
            path = os.path.join(saves_dir, name)
            try:
                with open(path, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                all_data[name] = data
            except Exception as e:
                st.error(f"Failed to load {name}: {e}")

    # Allow uploading additional files as a fallback or supplement
    uploaded_files = st.file_uploader(
        "Ouploader des JSON additionnels (optionnel)",
        type=["json"],
        accept_multiple_files=True,
    )
    if uploaded_files:
        for uploaded in uploaded_files:
            try:
                data = json.load(uploaded)
                all_data[uploaded.name] = data
            except Exception as e:
                st.error(f"Failed to parse uploaded file {uploaded.name}: {e}")

    if not all_data:
        st.info("No results available. Add JSON files to src/streamlit/saves or upload JSONs.")
        st.stop()

with right:
    # General information comparison
    st.subheader("General Information")
    general_df = pd.DataFrame(
        [
            {
                "File": name,
                "Algorithm": data.get("general_information", {}).get("algorithm", "?"),
                "Steps": data.get("general_information", {}).get("steps", 0),
                "Events": data.get("general_information", {}).get("events", 0),
                "Map Shape": str(
                    tuple(data.get("general_information", {}).get("map_shape", (0, 0)))
                ),
            }
            for name, data in all_data.items()
        ]
    )
    st.dataframe(general_df, width="stretch")

# Histories
st.subheader("Histories Comparison")

left, right = st.columns(2)

# Left column: average and maximum idleness
with left:
    # Average Idleness
    df_avg_all = []
    for name, data in all_data.items():
        avg = data.get("average_idleness_history", []) or []
        if avg:
            df_avg_all.append(
                pd.DataFrame(
                    {"step": range(len(avg)), "average_idleness": avg, "file": name}
                )
            )

    if df_avg_all:
        df_avg_combined = pd.concat(df_avg_all, ignore_index=True)
        fig_avg = px.line(
            df_avg_combined,
            x="step",
            y="average_idleness",
            color="file",
            title="Average Idleness",
        )
        st.plotly_chart(fig_avg, width="stretch")

    # Maximum Idleness
    df_max_all = []
    for name, data in all_data.items():
        maxi = data.get("maximum_idleness_history", []) or []
        if maxi:
            df_max_all.append(
                pd.DataFrame(
                    {"step": range(len(maxi)), "maximum_idleness": maxi, "file": name}
                )
            )

    if df_max_all:
        df_max_combined = pd.concat(df_max_all, ignore_index=True)
        fig_max = px.line(
            df_max_combined,
            x="step",
            y="maximum_idleness",
            color="file",
            title="Maximum Idleness",
        )
        st.plotly_chart(fig_max, width="stretch")

# Right column: coverage metrics
with right:
    # Coverage by Agent (Total)
    df_coverage_all = []
    for name, data in all_data.items():
        by_agent = data.get("coverage_by_agent_history", []) or []
        if by_agent:
            try:
                df_agents = pd.DataFrame(by_agent).T
            except ValueError:
                max_len = max(len(step) for step in by_agent)
                df_agents = pd.DataFrame(
                    [list(step) + [None] * (max_len - len(step)) for step in by_agent],
                    columns=[f"agent_{i}" for i in range(max_len)],
                )
            df_agents["step"] = range(len(df_agents))
            total_coverage = df_agents.drop(columns=["step"]).sum(axis=1)
            df_coverage_all.append(
                pd.DataFrame(
                    {
                        "step": range(len(total_coverage)),
                        "total_coverage": total_coverage,
                        "file": name,
                    }
                )
            )

    if df_coverage_all:
        df_coverage_combined = pd.concat(df_coverage_all, ignore_index=True)
        fig_coverage = px.line(
            df_coverage_combined,
            x="step",
            y="total_coverage",
            color="file",
            title="Total Coverage",
        )
        st.plotly_chart(fig_coverage, width="stretch")

    # Agents Work
    df_work_all = []
    for name, data in all_data.items():
        agentswork = data.get("agentswork_history", []) or []
        if agentswork:
            max_len = max((len(col) for col in agentswork), default=0)
            total_work = [
                sum(
                    agentswork[i][step] if step < len(agentswork[i]) else 0
                    for i in range(len(agentswork))
                )
                for step in range(max_len)
            ]
            df_work_all.append(
                pd.DataFrame(
                    {
                        "step": range(len(total_work)),
                        "total_work": total_work,
                        "file": name,
                    }
                )
            )

    if df_work_all:
        df_work_combined = pd.concat(df_work_all, ignore_index=True)
        fig_work = px.line(
            df_work_combined,
            x="step",
            y="total_work",
            color="file",
            title="Total Agents Work",
        )
        st.plotly_chart(fig_work, width="stretch")

# Individual file details
st.subheader("Individual File Details")
selected_file = st.selectbox("Select file to view details", list(all_data.keys()))

if selected_file:
    data = all_data[selected_file]
    by_agent = data.get("coverage_by_agent_history", []) or []
    agentswork = data.get("agentswork_history", []) or []

    left, right = st.columns(2)

    with left:
        if by_agent:
            try:
                df_agents = pd.DataFrame(by_agent).T
            except ValueError:
                max_len = max(len(step) for step in by_agent)
                df_agents = pd.DataFrame(
                    [list(step) + [None] * (max_len - len(step)) for step in by_agent],
                    columns=[f"agent_{i}" for i in range(max_len)],
                )
            df_agents["step"] = range(len(df_agents))
            agent_cols = [c for c in df_agents.columns if c != "step"]
            df_melt = df_agents.melt(
                id_vars="step",
                value_vars=agent_cols,
                var_name="agent",
                value_name="coverage",
            )
            fig_agents = px.line(
                df_melt,
                x="step",
                y="coverage",
                color="agent",
                title=f"Coverage by Agent - {selected_file}",
            )
            st.plotly_chart(fig_agents, width="stretch")

    with right:
        if agentswork:
            max_len = max((len(col) for col in agentswork), default=0)
            col_data = {
                f"agent_{i}": list(col) + [None] * (max_len - len(col))
                for i, col in enumerate(agentswork)
            }
            df_agentswork = pd.DataFrame(col_data)
            df_agentswork["step"] = range(max_len)
            fig_agentswork = px.line(
                df_agentswork.melt(id_vars="step", var_name="agent", value_name="work"),
                x="step",
                y="work",
                color="agent",
                title=f"Agents Work History - {selected_file}",
            )
            st.plotly_chart(fig_agentswork, width="stretch")

# Show raw JSON if needed
with st.expander("Raw JSON"):
    selected_json = st.selectbox(
        "Select file", list(all_data.keys()), key="json_select"
    )
    st.json(all_data[selected_json])
