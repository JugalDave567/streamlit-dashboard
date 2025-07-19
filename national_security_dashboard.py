import math
import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
from PIL import Image


st.set_page_config("National Security Training Analytics", "🛡️", layout="wide")

FILE, SHEET = "Training Data VMAP_Forces.xlsx", "Data"
RENAME = {
    "Name of the Training Program": "Training_Program",
    "School": "School", "Year": "Year", "Name": "Name",
    "Designation": "Designation", "State/Central": "State",
    "Email": "Email", "Contact Number": "Contact_Number",
    "Gender": "Gender", "Participation type": "Participation_Type",
    "Training number": "Training_Number", "Country": "Country",
    "Number of Hours": "Hours_Completed",
}

@st.cache_data
def load_df():
    df = pd.read_excel(FILE, sheet_name=SHEET, engine="openpyxl", keep_default_na=True)
    df.columns = df.columns.str.strip()
    df.rename(columns=RENAME, inplace=True)
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    return df

df = load_df()
# ──────── DISPLAY RRU LOGO AT TOP ────────
try:
    logo = Image.open("rru_logo.png")
    st.image(logo, width=150)
except FileNotFoundError:
    st.info("📁 `rru_logo.png` not found. Please place it in the app directory.")

# ───────── SEARCH BY NAME + 90 HOURS FILTER ─────────
st.sidebar.markdown("### 🔍 Participant Filters")

# Checkbox to show only participants who completed 90+ hours
only_90_plus = st.sidebar.checkbox("Show only participants with ≥ 90 hours", value=False)

# Filter based on 90 hours condition
eligible_df = df.groupby("Name")["Hours_Completed"].sum().reset_index()
eligible_df = eligible_df[eligible_df["Hours_Completed"] >= 90] if only_90_plus else eligible_df

# Update name options accordingly
name_options = sorted(eligible_df["Name"].unique())
search_name = st.sidebar.selectbox("Select Name", options=[""] + list(name_options))

# Filter main df if a name is selected
if search_name:
    df = df[df["Name"] == search_name]

# If a name is selected, filter the DataFrame
if search_name:
    df = df[df["Name"] == search_name]

    # ────── PARTICIPANT PROFILE ──────
    st.markdown("## 👤 Participant Profile")
    participant = df.iloc[0]
    st.markdown(f"""
    - **Name**: {participant['Name']}
    - **Designation**: {participant['Designation']}
    - **Email**: {participant['Email']}
    - **Phone**: {participant['Contact_Number']}
    - **Gender**: {participant['Gender']}
    - **Total Hours Completed**: {df['Hours_Completed'].sum()} hrs
    """)

    # ────── CERTIFICATE IF HOURS >= 90 ──────
    if df['Hours_Completed'].sum() >= 90:
        st.success("✅ Eligible for Certificate of Completion")

        cert_name = participant['Name']
        trainings = ", ".join(df['Training_Program'].unique())

        st.markdown(f"""
        ### 🎓 Certificate of Completion

        This is to certify that **{cert_name}** has successfully completed training(s) at **Rashtriya Raksha University**.

        - **Training(s)**: {trainings}
        - **Total Duration**: {df['Hours_Completed'].sum()} Hours
        """)

        # Optionally: Display RRU logo (assumes `rru_logo.png` exists)
        try:
            logo = Image.open("rru_logo.png")
            st.image(logo, width=150)
        except:
            st.info("RRU logo image not found. Upload `rru_logo.png` to see it here.")



# ───────── SESSION STATE ─────────
st.session_state.setdefault("auto", True)
st.session_state.setdefault("idx", 0)
st.session_state.setdefault("selected_pts", [])

# ───────── SIDEBAR FILTERS ─────────
st.sidebar.header("Filters")
df["Year"] = df["Year"].fillna(-1)
df["School"] = df["School"].fillna("Unknown")
df["State"] = df["State"].fillna("Unknown")

all_years = sorted(df["Year"].astype(int).unique())
select_all_years = st.sidebar.checkbox("Select All Years", value=True)
yrs = all_years if select_all_years else st.sidebar.multiselect("Year", all_years, default=all_years)

all_schools = sorted(df["School"].unique())
select_all_schools = st.sidebar.checkbox("Select All Schools", value=True)
sch = all_schools if select_all_schools else st.sidebar.multiselect("School", all_schools, default=all_schools)

all_states = sorted(df["State"].unique())
select_all_states = st.sidebar.checkbox("Select All State/Central", value=True)
states = all_states if select_all_states else st.sidebar.multiselect("State/Central", all_states, default=all_states)

# ───────── FILTERED DATA ─────────
base = df[df["Year"].isin(yrs) & df["School"].isin(sch) & df["State"].isin(states)]
pts = sorted(base["Participation_Type"].dropna().unique())
if not pts:
    st.warning("No data for these filters.")
    st.stop()

N = len(pts)

# ───────── AUTO ROTATE ─────────
if st.session_state.auto and st_autorefresh(interval=5000, key="rot") > 0:
    st.session_state.idx = (st.session_state.idx + 1) % N
    st.session_state.selected_pts = [pts[st.session_state.idx]]

query_params = st.query_params
clicked_pt = query_params.get("pt")
if clicked_pt:
    st.session_state.auto = False
    if clicked_pt in st.session_state.selected_pts:
        st.session_state.selected_pts.remove(clicked_pt)
    else:
        st.session_state.selected_pts.append(clicked_pt)

# ───────── HEADER CONTROLS ─────────
st.title("🛡️ National Security Training Analytics")
prev_b, auto_b, next_b = st.columns([1, 2, 1])
if prev_b.button("⟲ Prev"):
    st.session_state.idx = (st.session_state.idx - 1) % N
    st.session_state.auto = False
    st.session_state.selected_pts = [pts[st.session_state.idx]]
if next_b.button("Next ⟳"):
    st.session_state.idx = (st.session_state.idx + 1) % N
    st.session_state.auto = False
    st.session_state.selected_pts = [pts[st.session_state.idx]]
st.session_state.auto = auto_b.checkbox("Auto‑rotate", st.session_state.auto)

# ───────── PARTICIPATION TYPES ─────────
select_all_pts = st.checkbox("Select All Participation Types", value=False)
if select_all_pts:
    selected_pts = pts
else:
    selected_pts = st.multiselect("Select Participation Types", pts, default=st.session_state.selected_pts)
st.session_state.selected_pts = selected_pts
st.markdown(f"### Currently showing **{', '.join(selected_pts) if selected_pts else 'None'}**")

# ───────── KPI METRICS ─────────
st.sidebar.markdown("### Metric Type for KPIs")
metric_types = ["Count", "Distinct Count", "Sum", "Average"]
metric_kpis = {
    "Sessions": st.sidebar.selectbox("Training Sessions", metric_types, index=1, key="metric_sessions"),
    "Hours": st.sidebar.selectbox("Total Hours", metric_types, index=2, key="metric_hours"),
    "Participants": st.sidebar.selectbox("Participants", metric_types, index=0, key="metric_participants")
}

data = base[base["Participation_Type"].isin(selected_pts)]

def metric_value(series, mode):
    if mode == "Count":
        return len(series)
    elif mode == "Distinct Count":
        return series.nunique()
    elif mode == "Sum":
        return series.sum(skipna=True)
    elif mode == "Average":
        return series.mean(skipna=True)
    return len(series)

female_count = data[data["Gender"].str.lower() == "female"].shape[0]
male_count = data[data["Gender"].str.lower() == "male"].shape[0]

# ───────── KPI CARDS STYLE ─────────
st.markdown("""
<style>
.card-container {
    display: flex;
    gap: 20px;
    flex-wrap: wrap;
}
.card {
    flex: 1;
    min-width: 180px;
    background: #f9f9f9;
    border-radius: 12px;
    box-shadow: 0 1px 6px rgba(0,0,0,0.1);
    padding: 20px;
    text-align: center;
    transition: all 0.3s ease;
}
.card:hover {
    background: #e6f0ff;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    transform: translateY(-5px);
}
.card h1 {
    margin: 0;
    font-size: 26px;
    color: #0a2b49;
}
.card h2 {
    margin: 0;
    font-size: 14px;
    color: #666;
}
.card .icon {
    font-size: 40px;
    margin-bottom: 10px;
    color: #4a90e2;
}
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="card-container">
  <div class="card"><div class="icon">📋</div><h1>{metric_value(data['Training_Number'], metric_kpis["Sessions"]):,}</h1><h2>{metric_kpis["Sessions"]} Sessions</h2></div>
  <div class="card"><div class="icon">⏱️</div><h1>{int(metric_value(data['Hours_Completed'], metric_kpis["Hours"])):,}</h1><h2>{metric_kpis["Hours"]} Hours</h2></div>
  <div class="card"><div class="icon">👥</div><h1>{metric_value(data['Name'], metric_kpis["Participants"]):,}</h1><h2>{metric_kpis["Participants"]} Participants</h2></div>
  <div class="card"><div class="icon">👩</div><h1>{female_count:,}</h1><h2>Female Participants</h2></div>
  <div class="card"><div class="icon">👨</div><h1>{male_count:,}</h1><h2>Male Participants</h2></div>
</div>
""", unsafe_allow_html=True)

# ───────── WHEEL SVG ─────────
col1, col2 = st.columns(2)
with col1:
    SCALE = 1.0
    wheel_px = 500
    R, rx, ry = [int(v * SCALE) for v in (250, 100, 50)]
    font_px = int(17 * SCALE)
    hub_out, hub_mid, hub_in = [int(v * SCALE) for v in (150, 100, 60)]
    view = 800
    olive, saffron, active = "#556B2F", "#D35400", "#2980B9"
    navy, steel = "#002147", "#B0BEC5"
    svg = [f'<svg viewBox="-{view//2} -{view//2} {view} {view}" width="{wheel_px}" height="{wheel_px}" id="wheel">']
    step = 360 / N
    for i, pt in enumerate(pts):
        ang = -90 + i * step
        cx = R * math.cos(math.radians(ang))
        cy = R * math.sin(math.radians(ang))
        fill = active if pt in selected_pts else (saffron if pt == pts[st.session_state.idx] else olive)
        svg.append(
            f'<a href="?pt={pt}">' 
            f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx}" ry="{ry}" fill="{fill}" transform="rotate({ang:.1f},{cx:.1f},{cy:.1f})" />'
            f'<text x="{cx:.1f}" y="{cy:.1f}" font-size="{font_px}" text-anchor="middle" dominant-baseline="middle" fill="white" transform="rotate({ang:.1f},{cx:.1f},{cy:.1f})">{pt}</text>'
            f'</a>'
        )
    svg.append(
        '<a href="?manual=1">'
        f'<circle cx="0" cy="0" r="{hub_out}" fill="{navy}" />'
        f'<circle cx="0" cy="0" r="{hub_mid}" fill="{steel}" />'
        f'<circle cx="0" cy="0" r="{hub_in}" fill="{navy}" />'
        '</a></svg>'
    )
    st.markdown("""
    <style>
      #wheel { animation: spin 60s linear infinite; }
      @keyframes spin { from {transform: rotate(0deg);} to {transform: rotate(360deg);} }
      a:hover ellipse { filter: brightness(1.25); cursor: pointer; }
    </style>
    """, unsafe_allow_html=True)
    st.markdown("".join(svg), unsafe_allow_html=True)

# ───────── BAR & MAP ─────────
with col2:
    if data.empty:
        st.warning("No data to display.")
    else:
        st.markdown("### 📊 Yearly Comparison by School")
        chart_metric = st.selectbox("Chart Metric", ["Sessions", "Participants", "Hours"], index=0)
        
        if chart_metric == "Sessions":
            grp = data.groupby(["School", "Year"])["Training_Number"].nunique().reset_index(name="Value")
        elif chart_metric == "Participants":
            grp = data.groupby(["School", "Year"])["Name"].count().reset_index(name="Value")
        elif chart_metric == "Hours":
            grp = data.groupby(["School", "Year"])["Hours_Completed"].sum().reset_index(name="Value")

        fig = px.bar(grp, x="School", y="Value", color="Year",
                     barmode="group",
                     title=f"{chart_metric} by School & Year",
                     labels={"Value": chart_metric})
        st.plotly_chart(fig, use_container_width=True)

st.markdown("### Geographic Spread of Participants (State/Central)")
if not data.empty:
    state_df = data["State"].value_counts().reset_index()
    state_df.columns = ["State", "Count"]
    fig_map = px.choropleth(
        state_df,
        locations="State",
        locationmode="geojson-id",
        color="Count",
        title="Participant Distribution by State",
        color_continuous_scale="Blues"
    )
    st.plotly_chart(fig_map, use_container_width=True)
else:
    st.info("No data for map view.")

with st.expander("Show raw data"):
    st.dataframe(data)