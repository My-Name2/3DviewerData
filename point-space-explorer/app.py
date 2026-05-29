import os
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


# -----------------------------
# Basic setup
# -----------------------------
st.set_page_config(
    page_title="3D / 4D Point Space Explorer",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
DATA_FILE = DATA_DIR / "point_space_data.csv"


DEFAULT_DATA = pd.DataFrame(
    {
        "ticker": ["AAPL", "MSFT", "GOOG", "META", "AMZN"],
        "consistencyscoreadjusted": [0.82, 0.77, 0.70, 0.74, 0.68],
        "mktcap": [3000000000000, 2800000000000, 2200000000000, 1200000000000, 1800000000000],
        "averagepositive": [0.55, 0.50, 0.48, 0.53, 0.46],
        "averagepositivecfos": [0.61, 0.58, 0.54, 0.57, 0.51],
    }
)


# -----------------------------
# Helpers
# -----------------------------
def load_data() -> pd.DataFrame:
    """Load saved CSV data, falling back to the starter data."""
    if DATA_FILE.exists():
        try:
            return pd.read_csv(DATA_FILE)
        except Exception:
            return DEFAULT_DATA.copy()
    return DEFAULT_DATA.copy()


def save_data(df: pd.DataFrame) -> None:
    """Save current dataframe to local CSV."""
    df.to_csv(DATA_FILE, index=False)


def coerce_numeric_columns(df: pd.DataFrame, id_cols=("ticker",)) -> pd.DataFrame:
    """Convert non-identifier columns to numeric when possible."""
    clean = df.copy()
    for col in clean.columns:
        if col not in id_cols:
            clean[col] = pd.to_numeric(clean[col], errors="coerce")
    return clean


def get_numeric_columns(df: pd.DataFrame) -> list[str]:
    return df.select_dtypes(include=[np.number]).columns.tolist()


def default_index(options: list[str], preferred: str, fallback: int = 0) -> int:
    if preferred in options:
        return options.index(preferred)
    return min(fallback, max(len(options) - 1, 0))


def add_log_column(df: pd.DataFrame, source_col: str, new_col: str) -> pd.DataFrame:
    out = df.copy()
    if source_col in out.columns:
        values = pd.to_numeric(out[source_col], errors="coerce")
        out[new_col] = np.log1p(values.clip(lower=0))
    return out


# -----------------------------
# UI
# -----------------------------
st.title("3D / 4D Point Space Explorer")
st.caption(
    "Paste/edit data like a mini Stata data editor, then map variables into a draggable Plotly 3D point cloud."
)

with st.sidebar:
    st.header("Data")
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

    st.markdown("---")
    st.header("Chart meaning")
    st.write("3D = X, Y, Z axes.")
    st.write("4D = use another variable as color.")
    st.write("5D = use another variable as bubble size.")

    st.markdown("---")
    st.header("Notes")
    st.write(
        "On Streamlit Cloud, local saved CSV changes may reset when the app restarts. "
        "For permanent multi-user storage, connect a database later."
    )


if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
else:
    df = load_data()

df = coerce_numeric_columns(df)

# Add a useful derived market-cap column if possible.
df = add_log_column(df, "mktcap", "log_mktcap")

st.subheader("Editable data table")

edited_df = st.data_editor(
    df,
    num_rows="dynamic",
    use_container_width=True,
    height=330,
)

edited_df = coerce_numeric_columns(edited_df)
edited_df = add_log_column(edited_df, "mktcap", "log_mktcap")

save_col, download_col, reset_col = st.columns([1, 1, 1])

with save_col:
    if st.button("Save current table to CSV", use_container_width=True):
        save_data(edited_df)
        st.success(f"Saved to {DATA_FILE}")

with download_col:
    st.download_button(
        "Download current table",
        data=edited_df.to_csv(index=False),
        file_name="point_space_data.csv",
        mime="text/csv",
        use_container_width=True,
    )

with reset_col:
    if st.button("Reset to starter data", use_container_width=True):
        save_data(DEFAULT_DATA)
        st.warning("Reset saved data. Refresh the app to reload starter data.")


numeric_cols = get_numeric_columns(edited_df)

if len(numeric_cols) < 3:
    st.warning("You need at least three numeric columns for a 3D chart.")
    st.stop()

st.subheader("3D / 4D chart controls")

controls = st.columns(5)

with controls[0]:
    x_col = st.selectbox(
        "X-axis",
        numeric_cols,
        index=default_index(numeric_cols, "averagepositive", 0),
    )

with controls[1]:
    y_col = st.selectbox(
        "Y-axis",
        numeric_cols,
        index=default_index(numeric_cols, "averagepositivecfos", 1),
    )

with controls[2]:
    z_col = st.selectbox(
        "Z-axis",
        numeric_cols,
        index=default_index(numeric_cols, "consistencyscoreadjusted", 2),
    )

with controls[3]:
    color_options = ["None"] + numeric_cols
    color_col = st.selectbox(
        "Color / 4th dimension",
        color_options,
        index=color_options.index("consistencyscoreadjusted")
        if "consistencyscoreadjusted" in color_options
        else 0,
    )

with controls[4]:
    size_options = ["None"] + numeric_cols
    size_col = st.selectbox(
        "Bubble size / optional 5th dimension",
        size_options,
        index=size_options.index("log_mktcap") if "log_mktcap" in size_options else 0,
    )

chart_options = st.columns(4)

with chart_options[0]:
    opacity = st.slider("Point opacity", 0.1, 1.0, 0.85, 0.05)

with chart_options[1]:
    base_size = st.slider("Base marker size", 2, 20, 7, 1)

with chart_options[2]:
    use_log_axes = st.checkbox("Log selected axes when possible", value=False)

with chart_options[3]:
    show_2d = st.checkbox("Also show 2D Substack-friendly chart", value=True)


plot_df = edited_df.dropna(subset=[x_col, y_col, z_col]).copy()

if plot_df.empty:
    st.warning("No rows are plottable after dropping missing X/Y/Z values.")
    st.stop()

# Plotly size values must be non-negative.
size_arg = None
if size_col != "None":
    size_values = pd.to_numeric(plot_df[size_col], errors="coerce").fillna(0).clip(lower=0)
    if size_values.max() > 0:
        plot_df["_plot_size"] = size_values
        size_arg = "_plot_size"

hover_cols = [col for col in plot_df.columns if not col.startswith("_")]

fig = px.scatter_3d(
    plot_df,
    x=x_col,
    y=y_col,
    z=z_col,
    color=None if color_col == "None" else color_col,
    size=size_arg,
    hover_name="ticker" if "ticker" in plot_df.columns else None,
    hover_data=hover_cols,
    title="3D / 4D Point Space",
)

fig.update_traces(marker=dict(opacity=opacity, sizemin=base_size))
fig.update_layout(
    height=780,
    margin=dict(l=0, r=0, b=0, t=40),
    scene=dict(
        xaxis_title=x_col,
        yaxis_title=y_col,
        zaxis_title=z_col,
    ),
)

if use_log_axes:
    # Plotly 3D axes support log type, but only when all values are positive.
    if (plot_df[x_col] > 0).all():
        fig.update_layout(scene_xaxis_type="log")
    if (plot_df[y_col] > 0).all():
        fig.update_layout(scene_yaxis_type="log")
    if (plot_df[z_col] > 0).all():
        fig.update_layout(scene_zaxis_type="log")

st.plotly_chart(fig, use_container_width=True)

html = fig.to_html(include_plotlyjs="cdn", full_html=True)
st.download_button(
    "Download interactive 3D chart as HTML",
    data=html,
    file_name="point_space_3d_chart.html",
    mime="text/html",
)

if show_2d:
    st.subheader("2D bubble chart for easier article screenshots")

    two_d_controls = st.columns(4)

    with two_d_controls[0]:
        x2_col = st.selectbox(
            "2D X-axis",
            numeric_cols,
            index=default_index(numeric_cols, x_col, 0),
            key="x2",
        )

    with two_d_controls[1]:
        y2_col = st.selectbox(
            "2D Y-axis",
            numeric_cols,
            index=default_index(numeric_cols, y_col, 1),
            key="y2",
        )

    with two_d_controls[2]:
        color2_options = ["None"] + numeric_cols
        color2_col = st.selectbox(
            "2D color",
            color2_options,
            index=color2_options.index(color_col) if color_col in color2_options else 0,
            key="color2",
        )

    with two_d_controls[3]:
        size2_options = ["None"] + numeric_cols
        size2_col = st.selectbox(
            "2D bubble size",
            size2_options,
            index=size2_options.index(size_col) if size_col in size2_options else 0,
            key="size2",
        )

    plot2_df = edited_df.dropna(subset=[x2_col, y2_col]).copy()

    size2_arg = None
    if size2_col != "None":
        size2_values = pd.to_numeric(plot2_df[size2_col], errors="coerce").fillna(0).clip(lower=0)
        if size2_values.max() > 0:
            plot2_df["_plot2_size"] = size2_values
            size2_arg = "_plot2_size"

    fig2 = px.scatter(
        plot2_df,
        x=x2_col,
        y=y2_col,
        color=None if color2_col == "None" else color2_col,
        size=size2_arg,
        hover_name="ticker" if "ticker" in plot2_df.columns else None,
        hover_data=[col for col in plot2_df.columns if not col.startswith("_")],
        title="2D Bubble View",
    )

    fig2.update_traces(marker=dict(opacity=opacity))
    fig2.update_layout(height=650)
    st.plotly_chart(fig2, use_container_width=True)

    html2 = fig2.to_html(include_plotlyjs="cdn", full_html=True)
    st.download_button(
        "Download interactive 2D chart as HTML",
        data=html2,
        file_name="point_space_2d_chart.html",
        mime="text/html",
    )

st.subheader("Quick cluster-style interpretation table")

group_col_candidates = [col for col in edited_df.columns if "cluster" in col.lower()]
if group_col_candidates:
    selected_group = st.selectbox("Group by", group_col_candidates)
    summary = edited_df.groupby(selected_group)[numeric_cols].mean(numeric_only=True).round(4)
    st.dataframe(summary, use_container_width=True)
else:
    st.info("Add a column like cluster4 if you want a cluster summary table.")
