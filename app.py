"""
🌦️ Weather & Food Cravings — Live Survey Dashboard
=====================================================
Reads responses from Google Sheets in real-time and
auto-refreshes charts + sentiment analysis.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from collections import Counter
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import gspread
from google.oauth2.service_account import Credentials
import time, json, os

# ── PAGE CONFIG ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="Weather & Food Cravings Dashboard",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── PALETTE ──────────────────────────────────────────────────────────
TEAL   = "#0D7377"
GOLD   = "#F5A623"
CORAL  = "#E8604C"
SKY    = "#0EA5E9"
GREEN  = "#22C55E"
PURPLE = "#8B5CF6"
RED    = "#EF4444"
NAVY   = "#1B2A4A"
PALETTE = [TEAL, GOLD, CORAL, SKY, GREEN, PURPLE]

# ── CUSTOM CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
  .main { background: #F4F7FB; }
  .block-container { padding-top: 1.5rem; }
  .metric-card {
    background: white; border-radius: 12px; padding: 20px 24px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    border-left: 5px solid #0D7377;
    margin-bottom: 12px;
  }
  .metric-val  { font-size: 2.4rem; font-weight: 800; color: #0D7377; }
  .metric-lbl  { font-size: 0.85rem; color: #64748B; margin-top: 2px; }
  .section-hdr {
    font-size: 1.25rem; font-weight: 700; color: #1B2A4A;
    border-left: 4px solid #0D7377; padding-left: 10px;
    margin: 24px 0 12px;
  }
  .quote-card {
    background: white; border-radius: 10px; padding: 14px 18px;
    border-left: 4px solid #0D7377;
    font-style: italic; color: #334155; font-size: 0.9rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    margin-bottom: 8px;
  }
  .live-badge {
    display: inline-block; background: #22C55E; color: white;
    border-radius: 20px; padding: 3px 12px; font-size: 0.75rem;
    font-weight: 700; letter-spacing: 0.5px;
  }
</style>
""", unsafe_allow_html=True)

# ── GOOGLE SHEETS CONNECTION ─────────────────────────────────────────
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

# @st.cache_resource
# def get_gsheet_client():

#     def fix_private_key(key: str) -> str:
#         key = key.replace("\\n", "\n")
#         lines = [l.strip() for l in key.strip().splitlines() if l.strip()]
#         header  = lines[0]
#         footer  = lines[-1]
#         b64body = "".join(lines[1:-1])
#         b64body = b64body.replace(" ", "").replace("\t", "")
#         wrapped = "\n".join(b64body[i:i+64] for i in range(0, len(b64body), 64))
#         return f"{header}\n{wrapped}\n{footer}\n"

#     if "gcp_service_account" in st.secrets:
#         info = dict(st.secrets["gcp_service_account"])
#         info["private_key"] = fix_private_key(info["private_key"])
#         creds = Credentials.from_service_account_info(info, scopes=SCOPES)

#     if os.path.exists("./credentials.json"):
#         # ✅ Read directly from file — no string manipulation needed
#         creds = Credentials.from_service_account_file(
#             "./credentials.json", scopes=SCOPES
#         )

#     else:
#         st.error("❌ No credentials found. Put credentials.json in the app folder.")
#         st.stop()

#     return gspread.authorize(creds)
# @st.cache_resource
# def get_gsheet_client():

#     if os.path.exists("credentials.json"):
#         creds = Credentials.from_service_account_file(
#             "credentials.json", scopes=SCOPES
#         )
#     else:
#         st.error("❌ credentials.json not found")
#         st.stop()

#     return gspread.authorize(creds)
# SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

@st.cache_resource
def get_gsheet_client():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=SCOPES
        )
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"❌ Error loading credentials: {e}")
        st.stop()


@st.cache_data(ttl=30)
def load_data(sheet_url: str) -> pd.DataFrame:
    client = get_gsheet_client()

    # Works with full URL or just the sheet ID
    if "spreadsheets/d/" in sheet_url:
        sheet_id = sheet_url.split("spreadsheets/d/")[1].split("/")[0]
    else:
        sheet_id = sheet_url.strip()

    sheet = client.open_by_key(sheet_id).sheet1
    data  = sheet.get_all_records()
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    df.columns = [
        "timestamp", "age_group", "role", "order_freq",
        "craving_freq", "rainy_cuisine", "rainy_fav",
        "cold_cuisine", "cold_fav", "hot_cuisine", "hot_fav",
        "weather_change_behavior", "bad_weather_order", "weather_influence"
    ]
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df
# ── HELPERS ──────────────────────────────────────────────────────────
LABEL_MAP = {
    "Indian (like curry, biryani)":          "Indian/Biryani",
    "Asian (like noodles, ramen, stir-fry)": "Asian/Noodles",
    "Italian(like pasta , pizza)":           "Italian/Pizza",
    "American (like burgers, fries)":        "American/Burgers",
    "Japanese (like sushi, ramen, tempura)": "Japanese",
    "Arab (like shawarma, kebab, hummus)":   "Arab",
}

def explode_choices(series) -> Counter:
    counter = Counter()
    for val in series.dropna():
        for part in str(val).split(","):
            part = part.strip()
            for k, v in LABEL_MAP.items():
                if k in part:
                    part = v
                    break
            skip = {"None","nan","","biryani)","stir-fry)","fries)","tempura)","hummus)"}
            if part and part not in skip:
                counter[part] += 1
    return counter

def run_sentiment(texts):
    analyzer = SentimentIntensityAnalyzer()
    rows = []
    for t in texts:
        s = analyzer.polarity_scores(t)
        label = ("Positive" if s["compound"] > 0.05
                 else "Negative" if s["compound"] < -0.05 else "Neutral")
        rows.append({"text": t, "compound": s["compound"], "sentiment": label})
    return pd.DataFrame(rows)

# ── SIDEBAR ──────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://em-content.zobj.net/source/microsoft/378/cloud-with-rain_1f327-fe0f.png", width=60)
    st.title("Dashboard Settings")

    sheet_url = st.text_input(
        "📋 Google Sheet URL",
        placeholder="https://docs.google.com/spreadsheets/d/...",
        help="Paste the URL of the Google Sheet linked to your form.",
    )
    refresh_interval = st.selectbox("🔄 Auto-refresh every", [30, 60, 120, 300], index=1)
    st.caption(f"Data cached for {refresh_interval}s")

    st.divider()
    st.markdown("### 🔐 Credentials")
    st.info("Put your `credentials.json` in the app folder **or** add secrets in Streamlit Cloud. See setup guide.")

    st.divider()
    st.markdown("### 📖 Quick Setup")
    st.markdown("""
1. Enable **Google Sheets API**
2. Create a **Service Account**
3. Share your Sheet with the service account email
4. Paste Sheet URL above
5. Run: `streamlit run app.py`
    """)

    if st.button("🔄 Force Refresh Now"):
        st.cache_data.clear()
        st.rerun()

# ── HEADER ───────────────────────────────────────────────────────────
col_h1, col_h2 = st.columns([6, 1])
with col_h1:
    st.markdown("# 🌦️ Weather & Food Cravings")
    st.markdown("**Live Survey Dashboard** — auto-refreshes from Google Forms")
with col_h2:
    st.markdown('<span class="live-badge">● LIVE</span>', unsafe_allow_html=True)
    st.caption(f"Refreshes every {refresh_interval}s")

st.divider()

# ── LOAD DATA ────────────────────────────────────────────────────────
if not sheet_url:
    st.info("👈 Paste your Google Sheet URL in the sidebar to get started.")
    st.markdown("""
    ### How this dashboard works
    | Step | Action |
    |------|--------|
    | 1 | Your Google Form collects responses |
    | 2 | Responses auto-save to a linked Google Sheet |
    | 3 | This dashboard reads the Sheet every 30s |
    | 4 | Charts and sentiment analysis update automatically |
    """)
    st.stop()

with st.spinner("Fetching latest responses..."):
    df = load_data(sheet_url)

if df.empty:
    st.warning("No responses found yet. Share your form and check back!")
    st.stop()

# ── KPI ROW ──────────────────────────────────────────────────────────
st.markdown('<div class="section-hdr">📊 Overview</div>', unsafe_allow_html=True)

aware_pct = int(
    df["craving_freq"].isin(["Often","Always","Occasionally"]).mean() * 100
)
comfort_pct = int(
    (df["weather_change_behavior"] == "Eat more comfort or indulgent foods").mean() * 100
)
latest_ts = df["timestamp"].max().strftime("%b %d, %H:%M") if not df["timestamp"].isna().all() else "—"

k1, k2, k3, k4, k5 = st.columns(5)
for col, val, lbl in zip(
    [k1, k2, k3, k4, k5],
    [len(df), f"{aware_pct}%", f"{comfort_pct}%",
     df["age_group"].mode()[0], latest_ts],
    ["Total Responses", "Notice Weather Cravings", "Seek Comfort Food",
     "Top Age Group", "Last Response"],
):
    col.markdown(
        f'<div class="metric-card"><div class="metric-val">{val}</div>'
        f'<div class="metric-lbl">{lbl}</div></div>',
        unsafe_allow_html=True,
    )

# ── TAB LAYOUT ───────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "👥 Demographics",
    "🍛 Cuisine Preferences",
    "🌡️ Behavior",
    "💬 Sentiment",
    "📈 Trends",
])

# ══ TAB 1 — DEMOGRAPHICS ════════════════════════════════════════════
with tab1:
    st.markdown('<div class="section-hdr">Respondent Demographics</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)

    with c1:
        age_counts = df["age_group"].value_counts().reset_index()
        age_counts.columns = ["Age Group", "Count"]
        fig = px.bar(age_counts, x="Count", y="Age Group", orientation="h",
                     color="Age Group", color_discrete_sequence=PALETTE,
                     title="Age Distribution")
        fig.update_layout(showlegend=False, plot_bgcolor="white",
                          paper_bgcolor="white", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        role_counts = df["role"].value_counts().reset_index()
        role_counts.columns = ["Role", "Count"]
        fig = px.pie(role_counts, values="Count", names="Role",
                     color_discrete_sequence=PALETTE, title="Respondent Role",
                     hole=0.45)
        fig.update_traces(textposition="outside", textinfo="percent+label")
        fig.update_layout(paper_bgcolor="white", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-hdr">Craving Frequency</div>', unsafe_allow_html=True)
    freq_order  = ["Always", "Often", "Occasionally", "Never"]
    freq_counts = df["craving_freq"].value_counts().reindex(freq_order).fillna(0).reset_index()
    freq_counts.columns = ["Frequency", "Count"]
    freq_counts["Pct"] = (freq_counts["Count"] / len(df) * 100).round(1)
    fig = px.bar(freq_counts, x="Frequency", y="Count",
                 color="Frequency", text="Pct",
                 color_discrete_sequence=[TEAL, SKY, GOLD, CORAL],
                 title="How Often Do Respondents Notice Weather-Based Cravings?")
    fig.update_traces(texttemplate="%{text}%", textposition="outside")
    fig.update_layout(showlegend=False, plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)

# ══ TAB 2 — CUISINE PREFERENCES ═════════════════════════════════════
with tab2:
    # st.markdown('<div class="section-hdr">Cuisine Choices by Weather</div>', unsafe_allow_html=True)

    top_cuisines = ["Indian/Biryani","Asian/Noodles","Italian/Pizza","American/Burgers","Japanese"]
    rainy_ct = explode_choices(df["rainy_cuisine"])
    cold_ct  = explode_choices(df["cold_cuisine"])
    hot_ct   = explode_choices(df["hot_cuisine"])

    # chart_df = pd.DataFrame({
    #     "Cuisine":      top_cuisines * 3,
    #     "Count":        [rainy_ct.get(c,0) for c in top_cuisines] +
    #                     [cold_ct.get(c,0)  for c in top_cuisines] +
    #                     [hot_ct.get(c,0)   for c in top_cuisines],
    #     "Weather":      ["🌧️ Rainy"]*5 + ["❄️ Cold"]*5 + ["☀️ Hot"]*5,
    # })
    # fig = px.bar(chart_df, x="Cuisine", y="Count", color="Weather",
    #              barmode="group", color_discrete_map={
    #                  "🌧️ Rainy": TEAL, "❄️ Cold": SKY, "☀️ Hot": GOLD},
    #              title="Cuisine Preferences by Weather Type (multi-select)")
    # fig.update_layout(plot_bgcolor="white", paper_bgcolor="white",
    #                   legend_title_text="Weather")
    # st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-hdr">Heatmap — Mentions by Weather</div>', unsafe_allow_html=True)
    hm_data = {}
    for weather, ct in [("Rainy 🌧️", rainy_ct), ("Cold ❄️", cold_ct), ("Hot ☀️", hot_ct)]:
        for cuisine, cnt in ct.items():
            hm_data.setdefault(cuisine, {})[weather] = cnt
    hm_df = pd.DataFrame(hm_data).T.fillna(0).astype(int)
    hm_df = hm_df.loc[hm_df.sum(axis=1).nlargest(8).index]

    fig = px.imshow(hm_df, text_auto=True, aspect="auto",
                    color_continuous_scale="YlOrRd",
                    title="Cuisine × Weather Heatmap")
    fig.update_layout(paper_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)

# ══ TAB 3 — BEHAVIOR ════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-hdr">Behavioral Response to Sudden Weather Change</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)

    with c1:
        beh_counts = df["weather_change_behavior"].value_counts().reset_index()
        beh_counts.columns = ["Behavior", "Count"]
        beh_counts["Pct"] = (beh_counts["Count"] / len(df) * 100).round(1)
        fig = px.bar(beh_counts, x="Pct", y="Behavior", orientation="h",
                     color="Behavior", text="Pct",
                     color_discrete_sequence=[CORAL, TEAL, GOLD],
                     title="When Weather Changes Suddenly...")
        fig.update_traces(texttemplate="%{text}%", textposition="outside")
        fig.update_layout(showlegend=False, plot_bgcolor="white",
                          paper_bgcolor="white", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        order_order  = ["Always","Often","Sometimes","Rarely","Never"]
        order_counts = df["bad_weather_order"].value_counts().reindex(order_order).fillna(0).reset_index()
        order_counts.columns = ["Frequency","Count"]
        fig = px.funnel(order_counts, x="Count", y="Frequency",
                        color_discrete_sequence=[CORAL, GOLD, TEAL, SKY, "#CBD5E1"],
                        title="Order Delivery in Bad Weather?")
        fig.update_layout(paper_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-hdr">Ordering Frequency in Bad Weather</div>', unsafe_allow_html=True)
    fig = px.bar(order_counts, x="Frequency", y="Count", text="Count",
                 color="Frequency",
                 color_discrete_map={
                     "Always":"#E8604C","Often":"#F5A623","Sometimes":"#14B8A6",
                     "Rarely":"#0D7377","Never":"#CBD5E1"},
                 title="How Often Do Respondents Order Food in Bad Weather?")
    fig.update_traces(textposition="outside")
    fig.update_layout(showlegend=False, plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)

# ══ TAB 4 — SENTIMENT ════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-hdr">Sentiment Analysis — Open-Ended Responses</div>', unsafe_allow_html=True)
    st.caption('Q: "How does the weather influence what you eat?" | Analyzed with VADER')

    texts   = df["weather_influence"].dropna().astype(str).tolist()
    sent_df = run_sentiment(texts)
    counts  = sent_df["sentiment"].value_counts()

    c1, c2, c3 = st.columns(3)
    for col, label, color, emoji in zip(
        [c1, c2, c3],
        ["Positive", "Neutral", "Negative"],
        [GREEN, GOLD, RED],
        ["😊", "😐", "😞"],
    ):
        n   = counts.get(label, 0)
        pct = int(n / len(sent_df) * 100) if len(sent_df) else 0
        col.markdown(
            f'<div class="metric-card" style="border-left-color:{color}">'
            f'<div class="metric-val" style="color:{color}">{emoji} {pct}%</div>'
            f'<div class="metric-lbl">{label} ({n} responses)</div></div>',
            unsafe_allow_html=True,
        )

    c1, c2 = st.columns(2)
    with c1:
        sent_counts = sent_df["sentiment"].value_counts().reset_index()
        sent_counts.columns = ["Sentiment","Count"]
        fig = px.pie(sent_counts, values="Count", names="Sentiment",
                     color="Sentiment",
                     color_discrete_map={"Positive":GREEN,"Neutral":GOLD,"Negative":RED},
                     hole=0.5, title="Sentiment Distribution")
        fig.update_traces(textposition="outside", textinfo="percent+label")
        fig.update_layout(paper_bgcolor="white", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        fig = px.histogram(sent_df, x="compound", nbins=20,
                           color_discrete_sequence=[TEAL],
                           title="VADER Compound Score Distribution")
        fig.add_vline(x=0.05,  line_dash="dash", line_color=GREEN,
                      annotation_text="Positive", annotation_position="top right")
        fig.add_vline(x=-0.05, line_dash="dash", line_color=RED,
                      annotation_text="Negative", annotation_position="top left")
        fig.add_vline(x=sent_df["compound"].mean(), line_color=GOLD, line_width=2,
                      annotation_text=f"Mean={sent_df['compound'].mean():.2f}")
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                          xaxis_title="Compound Score (−1=Negative, +1=Positive)")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-hdr">Sample Quotes</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    for col, label, color in zip([c1,c2,c3],
                                  ["Positive","Neutral","Negative"],
                                  [GREEN, GOLD, RED]):
        subset = sent_df[sent_df["sentiment"]==label].head(3)
        col.markdown(f"**{label}**")
        for _, row in subset.iterrows():
            col.markdown(
                f'<div class="quote-card" style="border-left-color:{color}">'
                f'"{row["text"]}"</div>',
                unsafe_allow_html=True,
            )

# ══ TAB 5 — TRENDS ══════════════════════════════════════════════════
with tab5:
    st.markdown('<div class="section-hdr">Response Trends Over Time</div>', unsafe_allow_html=True)

    if df["timestamp"].isna().all():
        st.warning("Timestamps not available.")
    else:
        df_ts = df.dropna(subset=["timestamp"]).copy()
        df_ts["date"] = df_ts["timestamp"].dt.date
        daily = df_ts.groupby("date").size().reset_index(name="responses")

        fig = px.line(daily, x="date", y="responses", markers=True,
                      color_discrete_sequence=[TEAL],
                      title="Daily Response Count")
        fig.update_traces(line_width=2.5, marker_size=8)
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                          xaxis_title="Date", yaxis_title="Responses")
        st.plotly_chart(fig, use_container_width=True)

        st.markdown('<div class="section-hdr">Cumulative Responses</div>', unsafe_allow_html=True)
        daily["cumulative"] = daily["responses"].cumsum()
        fig = px.area(daily, x="date", y="cumulative",
                      color_discrete_sequence=[TEAL],
                      title="Cumulative Responses Over Time")
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-hdr">Ordering Frequency by Age Group</div>', unsafe_allow_html=True)
    cross = pd.crosstab(df["age_group"], df["craving_freq"])
    fig = px.imshow(cross, text_auto=True, color_continuous_scale="Teal",
                    title="Craving Frequency × Age Group")
    fig.update_layout(paper_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)

# ── AUTO-REFRESH ─────────────────────────────────────────────────────
st.divider()
st.caption(f"⏱️ Auto-refreshes every {refresh_interval} seconds. Last loaded: {time.strftime('%H:%M:%S')}")
time.sleep(refresh_interval)
st.cache_data.clear()
st.rerun()
