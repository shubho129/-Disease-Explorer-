import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from typing import Tuple

# --------------------------------------------------
# 🚀 CONFIGURATION
# --------------------------------------------------
st.set_page_config(
    page_title="🩺 Disease Explorer (Advanced)",
    page_icon="🦠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------
# 🎨 GLOBAL THEME / CUSTOM CSS
# --------------------------------------------------

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');

    html, body, [class*="st"]  {
        font-family: 'Poppins', sans-serif;
    }

    .stApp {
        background: linear-gradient(135deg, #f0f4f8 0%, #d9e2ec 100%);
    }

    section[data-testid="stSidebar"], section[data-testid="stSidebar"] > div:first-child {
        background-color: #e3f2fd;
        border-right: 1px solid #bbdefb;
    }

    h1, h2, h3, h4 {
        color: #003366;
    }

    .stDataFrame thead tr th {
        background-color: #0d47a1;
        color: white;
    }

    button[kind="secondary"], div[data-testid="stDownloadButton"] > button {
        background-color: #1565c0 !important;
        color: white !important;
        border-radius: 8px;
    }

    .stDataFrame tbody tr:hover {
        background-color: rgba(13, 71, 161, 0.08);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------
# 🗂️ DATA LOADING
# --------------------------------------------------
@st.cache_data(show_spinner=False)
def load_data(path: str = "Diseases_Symptoms.csv") -> pd.DataFrame:
    """Load the CSV dataset."""
    return pd.read_csv(path)

# Load dataset
DATA_PATH = "Diseases_Symptoms.csv"
df = load_data(DATA_PATH)

# --------------------------------------------------
# 🖼️ HEADER
# --------------------------------------------------
st.title("🦠 Disease Explorer")
st.markdown(
    "<span style='color:#333333;'>Discover diseases, symptoms & treatments — with instant search, interactive analytics, and easy CSV export.</span>",
    unsafe_allow_html=True,
)

# --------------------------------------------------
# 🔍 SIDEBAR FILTERS
# --------------------------------------------------
with st.sidebar:
    st.header("🔍 Filters")
    search_term = st.text_input("Search by Name or Symptom")
    contagious_filter = st.selectbox("Contagious", ["All", "Yes", "No"], index=0)
    chronic_filter = st.selectbox("Chronic", ["All", "Yes", "No"], index=0)
    top_n = st.slider("Max rows to display", 10, 500, 100, step=10)

# --------------------------------------------------
# 🔎 DATA FILTERING FUNCTION
# --------------------------------------------------

def apply_filters(dataframe: pd.DataFrame) -> pd.DataFrame:
    filtered = dataframe.copy()

    # Text search (case-insensitive)
    if search_term:
        mask = (
            filtered["Name"].str.contains(search_term, case=False, na=False)
            | filtered["Symptoms"].str.contains(search_term, case=False, na=False)
        )
        filtered = filtered[mask]

    # Boolean filters
    if contagious_filter != "All":
        filtered = filtered[filtered["Contagious"] == (contagious_filter == "Yes")]

    if chronic_filter != "All":
        filtered = filtered[filtered["Chronic"] == (chronic_filter == "Yes")]

    return filtered.head(top_n)

filtered_df = apply_filters(df)

# --------------------------------------------------
# 📑 MAIN TABS
# --------------------------------------------------
explorer_tab, insights_tab = st.tabs(["🔍 Explorer", "📊 Insights"])

# --------------------------------------------------
# 🔍 EXPLORER TAB
# --------------------------------------------------
with explorer_tab:
    # --- Overview & Download ---
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"📋 {len(filtered_df):,} disease(s) shown (max {top_n})")
    with col2:
        @st.cache_data
        def convert_df_to_csv(dataframe: pd.DataFrame) -> bytes:
            return dataframe.to_csv(index=False).encode("utf-8")

        csv_bytes = convert_df_to_csv(filtered_df)
        st.download_button(
            "📥 Download CSV",
            data=csv_bytes,
            file_name="filtered_diseases.csv",
            mime="text/csv",
        )

    st.dataframe(
        filtered_df,
        use_container_width=True,
        height=420,
    )

    # --- Detailed View ---
    if not filtered_df.empty:
        st.markdown("---")
        st.subheader("🔬 Disease Details")
        selected_name = st.selectbox(
            "Select a disease to see full details",
            options=filtered_df["Name"].unique(),
        )
        detail = filtered_df[filtered_df["Name"] == selected_name].iloc[0]

        def badge(flag: bool) -> str:
            color = "#d32f2f" if flag else "#388e3c"
            txt = "Yes" if flag else "No"
            return f"<span style='background:{color};color:white;padding:4px 8px;border-radius:6px;font-size:0.8rem'>{txt}</span>"

        st.markdown(f"### 🧾 {detail['Name']}")
        st.markdown(f"**📝 Symptoms:** {detail['Symptoms']}")
        st.markdown(
            f"**💊 Treatments:** {detail['Treatments'] if pd.notnull(detail['Treatments']) else 'N/A'}"
        )
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"**🆔 Disease Code:** {detail['Disease_Code']}")
        c2.markdown(f"**Contagious:** {badge(detail['Contagious'])}", unsafe_allow_html=True)
        c3.markdown(f"**Chronic:** {badge(detail['Chronic'])}", unsafe_allow_html=True)
    else:
        st.info("No diseases match your filters. Try adjusting them.")

# --------------------------------------------------
# 📊 INSIGHTS TAB
# --------------------------------------------------
with insights_tab:
    st.subheader("📊 Dataset Insights")

    # --- Metrics ---
    total_cnt = len(df)
    contagious_cnt = df["Contagious"].sum()
    chronic_cnt = df["Chronic"].sum()

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Diseases", f"{total_cnt}")
    m2.metric("Contagious", f"{contagious_cnt}", delta=f"{contagious_cnt/total_cnt:.1%}")
    m3.metric("Chronic", f"{chronic_cnt}", delta=f"{chronic_cnt/total_cnt:.1%}")

    st.markdown("---")

    # --- Pie Charts ---
    def draw_pie(values: Tuple[int, int], labels: Tuple[str, str], title: str):
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
        ax.axis("equal")
        ax.set_title(title)
        st.pyplot(fig)

    cpie1, cpie2 = st.columns(2)
    with cpie1:
        draw_pie(
            (contagious_cnt, total_cnt - contagious_cnt),
            ("Contagious", "Non-contagious"),
            "Contagious Breakdown",
        )
    with cpie2:
        draw_pie(
            (chronic_cnt, total_cnt - chronic_cnt),
            ("Chronic", "Non-chronic"),
            "Chronic Breakdown",
        )

    st.markdown("---")
    st.markdown("### 📈 Contagious vs. Chronic Cross-tab")
    cross_tab = pd.crosstab(df["Contagious"], df["Chronic"], margins=True)
    st.dataframe(cross_tab, use_container_width=True)

# --------------------------------------------------
# 📢 FOOTER
# --------------------------------------------------
st.markdown(
    """
    ---
    <div style='text-align:center;'>
        Built with ❤️ by <strong>Shubhankar Pal</strong> • Disease Explorer Advanced 🌐
    </div>
    """,
    unsafe_allow_html=True,
)