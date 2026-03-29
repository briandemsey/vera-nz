"""
VERA-NZ - Verification Engine for Results & Accountability
Streamlit Web Application for New Zealand Education Data

Analyzes NZ school data using Equity Index (EQI) to identify schools
where Māori and Pasifika students face barriers to achievement.

Data sourced from ArcGIS Feature Service (Eagle Technology / Ministry of Education).
Updated daily.
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# =============================================================================
# Configuration
# =============================================================================

st.set_page_config(
    page_title="VERA-NZ | Aotearoa Education Equity",
    page_icon="🇳🇿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# New Zealand Brand Colors
BLACK = "#000000"
WHITE = "#FFFFFF"
SILVER = "#C0C0C0"
NAVY = "#00247D"      # NZ Flag blue
RED = "#CC142B"       # NZ Flag red
GREEN = "#00843D"     # NZ green
CREAM = "#F8F8F5"

# Custom CSS
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;600;700&display=swap');

    .stApp {{
        background-color: {CREAM};
    }}

    section[data-testid="stSidebar"] {{
        background-color: {BLACK};
    }}
    section[data-testid="stSidebar"] .stMarkdown {{
        color: white;
    }}
    section[data-testid="stSidebar"] label {{
        color: white !important;
    }}
    section[data-testid="stSidebar"] .stRadio label,
    section[data-testid="stSidebar"] .stRadio label span,
    section[data-testid="stSidebar"] .stRadio label p,
    section[data-testid="stSidebar"] .stRadio label div {{
        color: white !important;
    }}

    h1, h2, h3 {{
        font-family: 'Public Sans', sans-serif;
        color: {BLACK};
    }}
    h1 {{
        border-bottom: 4px solid {SILVER};
        padding-bottom: 16px;
    }}

    .stat-card {{
        background: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border-left: 4px solid {BLACK};
        min-width: 0;
    }}
    .stat-card .value {{
        font-size: 1.8rem;
        font-weight: 700;
        color: {BLACK};
        white-space: nowrap;
    }}
    .stat-card .label {{
        font-size: 0.85rem;
        color: #666;
    }}

    .risk-high {{
        background-color: {RED};
        color: white;
        padding: 4px 12px;
        border-radius: 4px;
        font-weight: 600;
    }}
    .risk-medium {{
        background-color: #F47738;
        color: white;
        padding: 4px 12px;
        border-radius: 4px;
        font-weight: 600;
    }}
    .risk-low {{
        background-color: {GREEN};
        color: white;
        padding: 4px 12px;
        border-radius: 4px;
        font-weight: 600;
    }}

    .eqi-more {{ background-color: {RED}; color: white; padding: 2px 8px; border-radius: 4px; }}
    .eqi-moderate {{ background-color: #F47738; color: white; padding: 2px 8px; border-radius: 4px; }}
    .eqi-fewer {{ background-color: {GREEN}; color: white; padding: 2px 8px; border-radius: 4px; }}

    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# Data Functions - ArcGIS Feature Service (Eagle Technology / Ministry of Education)
# =============================================================================

# ArcGIS Feature Service endpoint (updated daily)
ARCGIS_ENDPOINT = "https://services.arcgis.com/XTtANUDT8Va4DLwI/arcgis/rest/services/Schools_Directory_New_Zealand/FeatureServer/0/query"


@st.cache_data(ttl=3600)
def fetch_nz_schools():
    """Fetch NZ schools from ArcGIS Feature Service (Ministry of Education data)."""
    try:
        # Query all open schools with key fields
        params = {
            "where": "Status='Open'",
            "outFields": "School_Id,Org_Name,Org_Type,Authority,Total,European,Māori,Pacific,Asian,MELAA,Other,International,Education_Region,Territorial_Authority,Latitude,Longitude,Decile,EQi_Index,Urban_Rural_Indicator",
            "f": "json",
            "resultRecordCount": 3000
        }

        response = requests.get(ARCGIS_ENDPOINT, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()

        if "features" in data:
            schools = [f["attributes"] for f in data["features"]]
            return schools
        else:
            st.error("Unexpected API response format")
            return []

    except Exception as e:
        st.error(f"Error fetching school data: {e}")
        return []


def safe_float(value, default=0.0):
    """Safely convert value to float."""
    try:
        if value is None or value == "" or value == "np" or value == "NA":
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value, default=0):
    """Safely convert value to int."""
    try:
        if value is None or value == "" or value == "np" or value == "NA":
            return default
        return int(float(value))
    except (ValueError, TypeError):
        return default


def get_eqi_band(eqi_value):
    """Determine EQI band based on value (344-569 range, grouped into 3 bands)."""
    if eqi_value is None or eqi_value == 0:
        return "Unknown"
    if eqi_value >= 490:  # More barriers
        return "More Barriers"
    elif eqi_value >= 430:  # Moderate barriers
        return "Moderate Barriers"
    else:  # Fewer barriers
        return "Fewer Barriers"


def compute_equity_risk(row):
    """
    Compute equity risk score for a school based on NZ factors.
    Higher score = more barriers to achievement.
    """
    # EQI is the primary equity measure (344-569 scale)
    eqi = safe_float(row.get("eqi", 0))

    # Māori and Pasifika percentages (key equity demographics)
    maori_pct = safe_float(row.get("maori_pct", 0))
    pasifika_pct = safe_float(row.get("pasifika_pct", 0))

    # Calculate risk score (0-100)
    # EQI contribution (normalized from 344-569 to 0-1)
    eqi_factor = max(0, min(1, (eqi - 344) / (569 - 344))) if eqi > 0 else 0

    # Demographics contribution
    demo_factor = min(1, (maori_pct + pasifika_pct) / 100)

    # Weighted combination
    risk = (eqi_factor * 0.6 + demo_factor * 0.4) * 100
    return round(risk, 2)


def prepare_dataframe(schools):
    """Convert school data to DataFrame with computed fields."""
    records = []

    for school in schools:
        # Handle field names from ArcGIS API
        school_name = school.get("Org_Name", "Unknown")
        school_id = school.get("School_Id", "")

        # Get enrollment totals
        total_roll = safe_int(school.get("Total", 0))

        # Skip schools with no enrollment
        if total_roll == 0:
            continue

        # Get raw demographic counts
        european = safe_int(school.get("European", 0))
        maori = safe_int(school.get("Māori", 0))
        pacific = safe_int(school.get("Pacific", 0))
        asian = safe_int(school.get("Asian", 0))

        # Calculate percentages
        maori_pct = round((maori / total_roll) * 100, 1) if total_roll > 0 else 0
        pasifika_pct = round((pacific / total_roll) * 100, 1) if total_roll > 0 else 0
        asian_pct = round((asian / total_roll) * 100, 1) if total_roll > 0 else 0
        european_pct = round((european / total_roll) * 100, 1) if total_roll > 0 else 0

        # Get location
        region = school.get("Education_Region", "Unknown")
        ta = school.get("Territorial_Authority", "Unknown")

        # Get school type
        school_type = school.get("Org_Type", "Unknown")
        authority = school.get("Authority", "State")

        # Get equity measures - EQi_Index is a string in the API
        eqi_str = school.get("EQi_Index", "0")
        eqi = safe_float(eqi_str)

        # Decile (legacy, may be null)
        decile_str = school.get("Decile", "0")
        decile = safe_int(decile_str) if decile_str else 0

        # Coordinates
        lat = safe_float(school.get("Latitude", 0))
        lng = safe_float(school.get("Longitude", 0))

        eqi_band = get_eqi_band(eqi)

        row = {
            "eqi": eqi,
            "maori_pct": maori_pct,
            "pasifika_pct": pasifika_pct,
        }
        risk_score = compute_equity_risk(row)

        records.append({
            "school_id": school_id,
            "school_name": school_name,
            "school_type": school_type,
            "authority": authority,
            "region": region,
            "ta": ta,
            "decile": decile,
            "eqi": eqi,
            "eqi_band": eqi_band,
            "total_roll": total_roll,
            "maori_pct": maori_pct,
            "pasifika_pct": pasifika_pct,
            "asian_pct": asian_pct,
            "european_pct": european_pct,
            "risk_score": risk_score,
            "latitude": lat,
            "longitude": lng
        })

    return pd.DataFrame(records)


# =============================================================================
# Sidebar
# =============================================================================

with st.sidebar:
    # Display Silver Fern flag from hosted URL
    st.markdown("""
        <div style="text-align: center; padding: 10px 0;">
            <img src="https://h-edu.solutions/assets/nz-silver-fern.svg" style="width: 100%; max-width: 200px; margin-bottom: 10px;" alt="Silver Fern Flag">
        </div>
    """, unsafe_allow_html=True)
    st.markdown(f"""
        <div style="text-align: center; padding: 10px 0;">
            <h2 style="color: white; margin: 10px 0;">VERA-NZ</h2>
            <p style="color: {SILVER}; font-size: 0.9rem;">Verification Engine for Results & Accountability</p>
            <p style="color: rgba(255,255,255,0.6); font-size: 0.8rem;">Aotearoa New Zealand</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    page = st.radio(
        "Navigate",
        ["📊 School Dashboard", "🔍 Equity Index Analysis", "🚩 Māori & Pasifika Focus", "🗺️ Regional View", "ℹ️ About VERA-NZ"],
        label_visibility="collapsed"
    )

    # Silver fern divider
    st.markdown(f"""
        <div style="
            height: 4px;
            background: linear-gradient(90deg, {SILVER}, #E8E8E8, {SILVER});
            margin: 30px 0 20px 0;
            border-radius: 2px;
        "></div>
    """, unsafe_allow_html=True)

    # Version and attribution
    st.markdown(f"""
        <p style="color: {SILVER}; font-size: 1.4rem; font-weight: 700; text-align: center; margin: 12px 0 6px 0;">
            VERA-NZ v0.2
        </p>
        <p style="color: white; font-size: 0.9rem; text-align: center; margin: 0 0 12px 0;">
            Live Data • Updated Daily
        </p>
        <p style="text-align: center;">
            <a href="https://www.educationcounts.govt.nz" target="_blank" style="
                color: {SILVER};
                font-size: 0.9rem;
                font-weight: 600;
                text-decoration: none;
                border-bottom: 2px solid {SILVER};
            ">Ministry of Education</a>
        </p>
    """, unsafe_allow_html=True)


# =============================================================================
# Load Data
# =============================================================================

schools_raw = fetch_nz_schools()
if schools_raw:
    df = prepare_dataframe(schools_raw)
else:
    st.error("Unable to load school data from API")
    st.stop()


# =============================================================================
# Page: School Dashboard
# =============================================================================

if page == "📊 School Dashboard":
    st.title("Aotearoa School Dashboard")
    st.caption("Live data from Ministry of Education • Updated daily")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        school_types = ["All"] + sorted(df["school_type"].dropna().unique().tolist())
        selected_type = st.selectbox("School Type", school_types)
    with col2:
        regions = ["All"] + sorted(df["region"].dropna().unique().tolist())
        selected_region = st.selectbox("Region", regions)
    with col3:
        eqi_bands = ["All", "More Barriers", "Moderate Barriers", "Fewer Barriers", "Unknown"]
        selected_eqi = st.selectbox("EQI Band", eqi_bands)

    # Filter data
    filtered = df.copy()
    if selected_type != "All":
        filtered = filtered[filtered["school_type"] == selected_type]
    if selected_region != "All":
        filtered = filtered[filtered["region"] == selected_region]
    if selected_eqi != "All":
        filtered = filtered[filtered["eqi_band"] == selected_eqi]

    # Summary stats
    st.markdown("### Overview")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
            <div class="stat-card">
                <div class="value">{len(filtered):,}</div>
                <div class="label">Schools</div>
            </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
            <div class="stat-card">
                <div class="value">{int(filtered['total_roll'].sum()):,}</div>
                <div class="label">Total Students</div>
            </div>
        """, unsafe_allow_html=True)
    with c3:
        avg_maori = filtered["maori_pct"].mean()
        st.markdown(f"""
            <div class="stat-card">
                <div class="value">{avg_maori:.1f}%</div>
                <div class="label">Avg Māori %</div>
            </div>
        """, unsafe_allow_html=True)
    with c4:
        high_barrier = len(filtered[filtered["eqi_band"] == "More Barriers"])
        st.markdown(f"""
            <div class="stat-card">
                <div class="value" style="color: {RED};">{high_barrier}</div>
                <div class="label">More Barriers Schools</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # EQI distribution chart
    st.markdown("### Equity Index Distribution")
    eqi_filtered = filtered[filtered["eqi"] > 0]
    if len(eqi_filtered) > 0:
        fig = px.histogram(
            eqi_filtered,
            x="eqi",
            nbins=30,
            color_discrete_sequence=[BLACK]
        )
        fig.update_layout(
            xaxis_title="Equity Index (344=fewer barriers, 569=more barriers)",
            yaxis_title="Number of Schools",
            showlegend=False
        )
        fig.add_vline(x=430, line_dash="dash", line_color=GREEN, annotation_text="Fewer/Moderate")
        fig.add_vline(x=490, line_dash="dash", line_color=RED, annotation_text="Moderate/More")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("EQI data not available in current filter selection.")

    # School table
    st.markdown("### Schools")
    display_cols = ["school_name", "school_type", "region", "eqi", "eqi_band", "total_roll", "maori_pct", "pasifika_pct", "risk_score"]
    st.dataframe(
        filtered[display_cols].sort_values("risk_score", ascending=False),
        use_container_width=True,
        hide_index=True
    )

    # Download
    csv = filtered.to_csv(index=False)
    st.download_button("Download CSV", csv, "vera_nz_schools.csv", "text/csv")


# =============================================================================
# Page: Equity Index Analysis
# =============================================================================

elif page == "🔍 Equity Index Analysis":
    st.title("Equity Index Analysis")
    st.caption("Live data from Ministry of Education • Updated daily")

    st.markdown("""
    The **Equity Index** replaced New Zealand's decile system in January 2023. It uses 37 factors
    per student to calculate a school index between 344 and 569:

    - **344-429:** Fewer barriers to achievement
    - **430-489:** Moderate barriers to achievement
    - **490-569:** More barriers to achievement

    Schools with higher EQI receive more equity funding to address systemic disadvantage.
    """)

    # EQI vs Demographics scatter
    st.markdown("### EQI vs Māori/Pasifika Concentration")

    plot_df = df[df["eqi"] > 0].copy()
    plot_df["maori_pasifika_pct"] = plot_df["maori_pct"] + plot_df["pasifika_pct"]

    if len(plot_df) > 0:
        fig = px.scatter(
            plot_df,
            x="maori_pasifika_pct",
            y="eqi",
            size="total_roll",
            color="eqi_band",
            color_discrete_map={
                "More Barriers": RED,
                "Moderate Barriers": "#F47738",
                "Fewer Barriers": GREEN
            },
            hover_name="school_name",
            hover_data=["region", "total_roll"]
        )
        fig.update_layout(
            xaxis_title="Māori + Pasifika %",
            yaxis_title="Equity Index"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("EQI data not available.")

    # EQI band breakdown
    st.markdown("### Schools by EQI Band")
    band_counts = df[df["eqi"] > 0].groupby("eqi_band").agg({
        "school_name": "count",
        "total_roll": "sum"
    }).reset_index()
    band_counts.columns = ["EQI Band", "Schools", "Students"]

    if len(band_counts) > 0:
        col1, col2 = st.columns(2)
        with col1:
            fig = px.pie(band_counts, values="Schools", names="EQI Band",
                        color="EQI Band",
                        color_discrete_map={
                            "More Barriers": RED,
                            "Moderate Barriers": "#F47738",
                            "Fewer Barriers": GREEN
                        })
            fig.update_layout(title="Schools by EQI Band")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.pie(band_counts, values="Students", names="EQI Band",
                        color="EQI Band",
                        color_discrete_map={
                            "More Barriers": RED,
                            "Moderate Barriers": "#F47738",
                            "Fewer Barriers": GREEN
                        })
            fig.update_layout(title="Students by EQI Band")
            st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# Page: Māori & Pasifika Focus
# =============================================================================

elif page == "🚩 Māori & Pasifika Focus":
    st.title("Māori & Pasifika Focus")
    st.caption("Live data from Ministry of Education • Updated daily")

    st.markdown(f"""
    **The Equity Crisis:** Despite having strong accountability infrastructure, New Zealand faces
    persistent achievement gaps:

    - **78%** of Māori students do not achieve University Entrance
    - **70%** of Pasifika students do not achieve University Entrance
    - Compare to **~25%** for Asian students and **~50%** for European/Pākehā

    VERA-NZ identifies WHERE these students are concentrated to inform intervention targeting.
    """)

    # Threshold sliders
    col1, col2 = st.columns(2)
    with col1:
        maori_threshold = st.slider("Māori % Threshold", 10, 80, 30)
    with col2:
        pasifika_threshold = st.slider("Pasifika % Threshold", 5, 50, 15)

    # Filter high concentration schools
    high_maori = df[df["maori_pct"] >= maori_threshold]
    high_pasifika = df[df["pasifika_pct"] >= pasifika_threshold]
    high_both = df[(df["maori_pct"] >= maori_threshold) | (df["pasifika_pct"] >= pasifika_threshold)]

    # Summary
    st.markdown("### Schools Meeting Criteria")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(f"High Māori (≥{maori_threshold}%)", len(high_maori))
    with c2:
        st.metric(f"High Pasifika (≥{pasifika_threshold}%)", len(high_pasifika))
    with c3:
        st.metric("Total Students in These Schools", f"{high_both['total_roll'].sum():,}")

    # Regional breakdown
    st.markdown("### Regional Distribution")
    if len(high_both) > 0:
        regional = high_both.groupby("region").agg({
            "school_name": "count",
            "total_roll": "sum",
            "maori_pct": "mean",
            "pasifika_pct": "mean"
        }).reset_index()
        regional.columns = ["Region", "Schools", "Students", "Avg Māori %", "Avg Pasifika %"]
        regional = regional.sort_values("Schools", ascending=False)

        fig = px.bar(
            regional.head(10),
            x="Region",
            y="Schools",
            color="Avg Māori %",
            color_continuous_scale=["green", "yellow", "red"]
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

        # Top schools table
        st.markdown("### Schools with Highest Māori/Pasifika Concentration")
        high_both_sorted = high_both.sort_values(["maori_pct", "pasifika_pct"], ascending=False)
        st.dataframe(
            high_both_sorted[["school_name", "region", "total_roll", "maori_pct", "pasifika_pct", "eqi", "eqi_band"]].head(30),
            use_container_width=True,
            hide_index=True
        )

        # Export
        csv = high_both.to_csv(index=False)
        st.download_button("Download High Priority Schools CSV", csv, "vera_nz_priority.csv", "text/csv")


# =============================================================================
# Page: Regional View
# =============================================================================

elif page == "🗺️ Regional View":
    st.title("Regional Analysis")
    st.caption("Live data from Ministry of Education • Updated daily")

    # Regional summary
    regional_summary = df.groupby("region").agg({
        "school_name": "count",
        "total_roll": "sum",
        "maori_pct": "mean",
        "pasifika_pct": "mean",
        "risk_score": "mean"
    }).reset_index()
    regional_summary.columns = ["Region", "Schools", "Students", "Avg Māori %", "Avg Pasifika %", "Avg Risk Score"]
    regional_summary = regional_summary.sort_values("Students", ascending=False)

    # Bar chart
    fig = px.bar(
        regional_summary,
        x="Region",
        y="Students",
        color="Avg Risk Score",
        color_continuous_scale=["green", "yellow", "red"]
    )
    fig.update_layout(xaxis_tickangle=-45, title="Students by Region (colored by avg risk)")
    st.plotly_chart(fig, use_container_width=True)

    # Table
    st.markdown("### Regional Summary")
    st.dataframe(regional_summary, use_container_width=True, hide_index=True)

    # Map (if coordinates available)
    map_df = df[(df["latitude"] != 0) & (df["longitude"] != 0)]
    if len(map_df) > 100:
        st.markdown("### School Locations")
        fig = px.scatter_mapbox(
            map_df,
            lat="latitude",
            lon="longitude",
            size="total_roll",
            color="risk_score",
            color_continuous_scale=["green", "yellow", "red"],
            hover_name="school_name",
            hover_data=["region", "maori_pct", "pasifika_pct"],
            zoom=4,
            center={"lat": -41.0, "lon": 174.0}
        )
        fig.update_layout(mapbox_style="open-street-map", height=600)
        st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# Page: About
# =============================================================================

elif page == "ℹ️ About VERA-NZ":
    st.title("About VERA-NZ")

    st.markdown(f"""
    ## Verification Engine for Results & Accountability

    **VERA-NZ** is an equity analysis tool for Aotearoa New Zealand's education system.
    It identifies schools where Māori and Pasifika students face the greatest barriers
    to achievement, enabling targeted intervention and resource allocation.

    ---

    ## Data Source

    VERA-NZ uses **live data** from the Ministry of Education via the
    [ArcGIS Feature Service](https://hub.arcgis.com/datasets/eaglegis::nz-schools-directory)
    maintained by Eagle Technology. Data is updated **daily**.

    **Fields include:**
    - School details (name, type, authority)
    - Enrollment by ethnicity (European, Māori, Pacific, Asian, MELAA, Other)
    - Equity Index (EQi) scores
    - Geographic location and region

    ---

    ## The Equity Index (EQI)

    In January 2023, New Zealand replaced the 10-level decile system with the **Equity Index**.
    The EQI uses 37 factors from Stats NZ's Integrated Data Infrastructure to measure
    socioeconomic barriers at the student level:

    | EQI Range | Band | Interpretation |
    |-----------|------|----------------|
    | 344-429 | Fewer Barriers | Lower socioeconomic disadvantage |
    | 430-489 | Moderate Barriers | Medium disadvantage levels |
    | 490-569 | More Barriers | Higher socioeconomic disadvantage |

    ---

    ## The Achievement Gap

    Despite strong policy infrastructure, persistent gaps remain:

    | Ethnicity | NCEA Level 3 + UE | Non-Attainment |
    |-----------|-------------------|----------------|
    | Asian | ~75% | ~25% |
    | European/Pākehā | ~50% | ~50% |
    | Pasifika | ~30% | **70%** |
    | Māori | ~22% | **78%** |

    VERA-NZ identifies WHERE these students are concentrated and whether interventions
    are reaching them.

    ---

    ## Additional Data Sources

    For NCEA achievement statistics, see:
    - [NZQA Secondary School Statistics](https://www2.nzqa.govt.nz/ncea/understanding-secondary-quals/secondary-school-stats/)

    ---

    <p style="color: #666; font-size: 0.9rem;">
        VERA-NZ v0.2 | Built by <a href="https://hallucinations.cloud" style="color: {BLACK};">Hallucinations.cloud</a> |
        An <a href="https://h-edu.solutions" style="color: {BLACK};">H-EDU.Solutions</a> Initiative
    </p>
    """, unsafe_allow_html=True)
