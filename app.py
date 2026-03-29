"""
VERA-NZ - Verification Engine for Results & Accountability
Streamlit Web Application for New Zealand Education Data

Analyzes NZ school data using Equity Index (EQI) to identify schools
where Māori and Pasifika students face barriers to achievement.
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import json

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
    }}
    .stat-card .value {{
        font-size: 2.5rem;
        font-weight: 700;
        color: {BLACK};
    }}
    .stat-card .label {{
        font-size: 0.9rem;
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
# Data Functions - NZ School Directory API
# =============================================================================

# CKAN API endpoint for data.govt.nz
CKAN_BASE = "https://catalogue.data.govt.nz/api/3/action/datastore_search_sql"
SCHOOL_RESOURCE_ID = "20b7c271-fd5a-4c9e-869b-481a0e2453cd"

@st.cache_data(ttl=3600)
def fetch_nz_schools():
    """Fetch NZ schools - uses sample data for demo, production will use Ministry API."""
    # Sample data representing real NZ schools across regions
    # Production version will connect to Ministry of Education API
    sample_schools = [
        # Auckland Region - High Māori/Pasifika concentration
        {"School_Id": "1", "Org_Name": "Māngere Central School", "School_Type": "Full Primary", "Region": "Auckland", "Territorial_Authority": "Auckland", "Decile": 1, "Equity_Index": 545, "Total": 450, "Maori": 35, "Pacific": 55, "Asian": 5, "European": 5, "Latitude": -36.9685, "Longitude": 174.7933},
        {"School_Id": "2", "Org_Name": "Ōtara South School", "School_Type": "Full Primary", "Region": "Auckland", "Territorial_Authority": "Auckland", "Decile": 1, "Equity_Index": 560, "Total": 380, "Maori": 25, "Pacific": 65, "Asian": 5, "European": 5, "Latitude": -36.9512, "Longitude": 174.8789},
        {"School_Id": "3", "Org_Name": "Glen Innes School", "School_Type": "Full Primary", "Region": "Auckland", "Territorial_Authority": "Auckland", "Decile": 2, "Equity_Index": 520, "Total": 290, "Maori": 40, "Pacific": 35, "Asian": 15, "European": 10, "Latitude": -36.8771, "Longitude": 174.8567},
        {"School_Id": "4", "Org_Name": "Pt England School", "School_Type": "Full Primary", "Region": "Auckland", "Territorial_Authority": "Auckland", "Decile": 1, "Equity_Index": 555, "Total": 520, "Maori": 45, "Pacific": 40, "Asian": 10, "European": 5, "Latitude": -36.8634, "Longitude": 174.8612},
        {"School_Id": "5", "Org_Name": "Kelston Primary School", "School_Type": "Full Primary", "Region": "Auckland", "Territorial_Authority": "Auckland", "Decile": 3, "Equity_Index": 485, "Total": 410, "Maori": 30, "Pacific": 45, "Asian": 15, "European": 10, "Latitude": -36.9089, "Longitude": 174.6534},
        {"School_Id": "6", "Org_Name": "Epsom Girls Grammar", "School_Type": "Secondary", "Region": "Auckland", "Territorial_Authority": "Auckland", "Decile": 9, "Equity_Index": 365, "Total": 2100, "Maori": 5, "Pacific": 3, "Asian": 45, "European": 47, "Latitude": -36.8901, "Longitude": 174.7712},
        {"School_Id": "7", "Org_Name": "Auckland Grammar School", "School_Type": "Secondary", "Region": "Auckland", "Territorial_Authority": "Auckland", "Decile": 9, "Equity_Index": 360, "Total": 2600, "Maori": 4, "Pacific": 2, "Asian": 50, "European": 44, "Latitude": -36.8712, "Longitude": 174.7623},

        # Wellington Region
        {"School_Id": "8", "Org_Name": "Porirua School", "School_Type": "Full Primary", "Region": "Wellington", "Territorial_Authority": "Porirua City", "Decile": 2, "Equity_Index": 525, "Total": 320, "Maori": 45, "Pacific": 35, "Asian": 5, "European": 15, "Latitude": -41.1345, "Longitude": 174.8401},
        {"School_Id": "9", "Org_Name": "Cannons Creek School", "School_Type": "Full Primary", "Region": "Wellington", "Territorial_Authority": "Porirua City", "Decile": 1, "Equity_Index": 558, "Total": 280, "Maori": 35, "Pacific": 55, "Asian": 3, "European": 7, "Latitude": -41.1234, "Longitude": 174.8567},
        {"School_Id": "10", "Org_Name": "Wellington College", "School_Type": "Secondary", "Region": "Wellington", "Territorial_Authority": "Wellington City", "Decile": 9, "Equity_Index": 370, "Total": 1800, "Maori": 8, "Pacific": 4, "Asian": 25, "European": 63, "Latitude": -41.2912, "Longitude": 174.7823},
        {"School_Id": "11", "Org_Name": "Naenae College", "School_Type": "Secondary", "Region": "Wellington", "Territorial_Authority": "Lower Hutt City", "Decile": 3, "Equity_Index": 495, "Total": 750, "Maori": 35, "Pacific": 30, "Asian": 10, "European": 25, "Latitude": -41.2145, "Longitude": 174.9412},

        # Waikato Region
        {"School_Id": "12", "Org_Name": "Fairfield College", "School_Type": "Secondary", "Region": "Waikato", "Territorial_Authority": "Hamilton City", "Decile": 3, "Equity_Index": 490, "Total": 980, "Maori": 40, "Pacific": 15, "Asian": 10, "European": 35, "Latitude": -37.8123, "Longitude": 175.2567},
        {"School_Id": "13", "Org_Name": "Melville Primary School", "School_Type": "Full Primary", "Region": "Waikato", "Territorial_Authority": "Hamilton City", "Decile": 2, "Equity_Index": 510, "Total": 340, "Maori": 55, "Pacific": 10, "Asian": 5, "European": 30, "Latitude": -37.8234, "Longitude": 175.2412},
        {"School_Id": "14", "Org_Name": "Hamilton Boys High School", "School_Type": "Secondary", "Region": "Waikato", "Territorial_Authority": "Hamilton City", "Decile": 6, "Equity_Index": 440, "Total": 1650, "Maori": 25, "Pacific": 8, "Asian": 15, "European": 52, "Latitude": -37.7912, "Longitude": 175.2789},

        # Bay of Plenty - High Māori concentration
        {"School_Id": "15", "Org_Name": "Rotorua Primary School", "School_Type": "Full Primary", "Region": "Bay of Plenty", "Territorial_Authority": "Rotorua District", "Decile": 2, "Equity_Index": 515, "Total": 290, "Maori": 70, "Pacific": 5, "Asian": 5, "European": 20, "Latitude": -38.1412, "Longitude": 176.2534},
        {"School_Id": "16", "Org_Name": "Western Heights Primary", "School_Type": "Full Primary", "Region": "Bay of Plenty", "Territorial_Authority": "Rotorua District", "Decile": 1, "Equity_Index": 550, "Total": 350, "Maori": 75, "Pacific": 5, "Asian": 3, "European": 17, "Latitude": -38.1534, "Longitude": 176.2312},
        {"School_Id": "17", "Org_Name": "Tauranga Intermediate", "School_Type": "Intermediate", "Region": "Bay of Plenty", "Territorial_Authority": "Tauranga City", "Decile": 7, "Equity_Index": 420, "Total": 680, "Maori": 20, "Pacific": 5, "Asian": 10, "European": 65, "Latitude": -37.6789, "Longitude": 176.1678},

        # Northland - High Māori concentration
        {"School_Id": "18", "Org_Name": "Kaikohe East School", "School_Type": "Full Primary", "Region": "Northland", "Territorial_Authority": "Far North District", "Decile": 1, "Equity_Index": 565, "Total": 180, "Maori": 85, "Pacific": 2, "Asian": 1, "European": 12, "Latitude": -35.4123, "Longitude": 173.7989},
        {"School_Id": "19", "Org_Name": "Moerewa School", "School_Type": "Full Primary", "Region": "Northland", "Territorial_Authority": "Far North District", "Decile": 1, "Equity_Index": 560, "Total": 150, "Maori": 90, "Pacific": 1, "Asian": 1, "European": 8, "Latitude": -35.3789, "Longitude": 173.8234},
        {"School_Id": "20", "Org_Name": "Whangārei Boys High School", "School_Type": "Secondary", "Region": "Northland", "Territorial_Authority": "Whangārei District", "Decile": 4, "Equity_Index": 475, "Total": 1200, "Maori": 45, "Pacific": 5, "Asian": 5, "European": 45, "Latitude": -35.7234, "Longitude": 174.3234},

        # Canterbury
        {"School_Id": "21", "Org_Name": "Linwood College", "School_Type": "Secondary", "Region": "Canterbury", "Territorial_Authority": "Christchurch City", "Decile": 3, "Equity_Index": 500, "Total": 650, "Maori": 25, "Pacific": 15, "Asian": 20, "European": 40, "Latitude": -43.5312, "Longitude": 172.6789},
        {"School_Id": "22", "Org_Name": "Hornby High School", "School_Type": "Secondary", "Region": "Canterbury", "Territorial_Authority": "Christchurch City", "Decile": 4, "Equity_Index": 470, "Total": 1100, "Maori": 20, "Pacific": 12, "Asian": 15, "European": 53, "Latitude": -43.5534, "Longitude": 172.5234},
        {"School_Id": "23", "Org_Name": "Christchurch Boys High School", "School_Type": "Secondary", "Region": "Canterbury", "Territorial_Authority": "Christchurch City", "Decile": 8, "Equity_Index": 385, "Total": 1400, "Maori": 10, "Pacific": 3, "Asian": 20, "European": 67, "Latitude": -43.5123, "Longitude": 172.6123},

        # Otago
        {"School_Id": "24", "Org_Name": "South Dunedin School", "School_Type": "Full Primary", "Region": "Otago", "Territorial_Authority": "Dunedin City", "Decile": 3, "Equity_Index": 485, "Total": 220, "Maori": 25, "Pacific": 10, "Asian": 5, "European": 60, "Latitude": -45.9012, "Longitude": 170.5012},
        {"School_Id": "25", "Org_Name": "Otago Boys High School", "School_Type": "Secondary", "Region": "Otago", "Territorial_Authority": "Dunedin City", "Decile": 8, "Equity_Index": 390, "Total": 950, "Maori": 12, "Pacific": 3, "Asian": 15, "European": 70, "Latitude": -45.8789, "Longitude": 170.5234},

        # Gisborne/East Coast - High Māori
        {"School_Id": "26", "Org_Name": "Te Karaka Area School", "School_Type": "Area School", "Region": "Gisborne", "Territorial_Authority": "Gisborne District", "Decile": 1, "Equity_Index": 555, "Total": 180, "Maori": 88, "Pacific": 1, "Asian": 1, "European": 10, "Latitude": -38.4789, "Longitude": 177.8567},
        {"School_Id": "27", "Org_Name": "Gisborne Girls High School", "School_Type": "Secondary", "Region": "Gisborne", "Territorial_Authority": "Gisborne District", "Decile": 4, "Equity_Index": 480, "Total": 750, "Maori": 55, "Pacific": 5, "Asian": 5, "European": 35, "Latitude": -38.6623, "Longitude": 178.0178},

        # Hawke's Bay
        {"School_Id": "28", "Org_Name": "Flaxmere Primary School", "School_Type": "Full Primary", "Region": "Hawke's Bay", "Territorial_Authority": "Hastings District", "Decile": 1, "Equity_Index": 548, "Total": 420, "Maori": 65, "Pacific": 15, "Asian": 3, "European": 17, "Latitude": -39.5789, "Longitude": 176.8412},
        {"School_Id": "29", "Org_Name": "Napier Boys High School", "School_Type": "Secondary", "Region": "Hawke's Bay", "Territorial_Authority": "Napier City", "Decile": 6, "Equity_Index": 435, "Total": 1100, "Maori": 30, "Pacific": 8, "Asian": 10, "European": 52, "Latitude": -39.4912, "Longitude": 176.9123},

        # Taranaki
        {"School_Id": "30", "Org_Name": "Waitara High School", "School_Type": "Secondary", "Region": "Taranaki", "Territorial_Authority": "New Plymouth District", "Decile": 3, "Equity_Index": 495, "Total": 450, "Maori": 55, "Pacific": 5, "Asian": 3, "European": 37, "Latitude": -38.9978, "Longitude": 174.2345},
    ]

    return sample_schools


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
    eqi = safe_float(row.get("Equity_Index", 0))

    # Māori and Pasifika percentages (key equity demographics)
    maori_pct = safe_float(row.get("Maori_Pct", 0))
    pasifika_pct = safe_float(row.get("Pacific_Pct", 0))

    # Decile (1-10, lower = more disadvantaged) - legacy measure
    decile = safe_int(row.get("Decile", 5))

    # Calculate risk score (0-100)
    # EQI contribution (normalized from 344-569 to 0-1)
    eqi_factor = max(0, min(1, (eqi - 344) / (569 - 344))) if eqi > 0 else 0

    # Demographics contribution
    demo_factor = min(1, (maori_pct + pasifika_pct) / 100)

    # Decile contribution (inverted - low decile = high risk)
    decile_factor = max(0, 1 - (decile / 10))

    # Weighted combination
    risk = (eqi_factor * 0.5 + demo_factor * 0.3 + decile_factor * 0.2) * 100
    return round(risk, 2)


def prepare_dataframe(schools):
    """Convert school data to DataFrame with computed fields."""
    records = []

    for school in schools:
        # Handle field names from sample data
        school_name = school.get("Org_Name", "Unknown")
        school_id = school.get("School_Id", "")

        # Get enrollment
        total_roll = safe_int(school.get("Total", 0))

        # Get demographics (already as percentages in sample data)
        maori_pct = safe_float(school.get("Maori", 0))
        pasifika_pct = safe_float(school.get("Pacific", 0))
        asian_pct = safe_float(school.get("Asian", 0))
        european_pct = safe_float(school.get("European", 0))

        # Get location
        region = school.get("Region", "Unknown")
        ta = school.get("Territorial_Authority", "Unknown")

        # Get school type
        school_type = school.get("School_Type", "Unknown")
        authority = school.get("Authority", "State")

        # Get equity measures
        decile = safe_int(school.get("Decile", 0))
        eqi = safe_float(school.get("Equity_Index", 0))

        # Coordinates
        lat = safe_float(school.get("Latitude", 0))
        lng = safe_float(school.get("Longitude", 0))

        # Build row for risk calculation
        row = {
            "Equity_Index": eqi,
            "Maori_Pct": maori_pct,
            "Pacific_Pct": pasifika_pct,
            "Decile": decile
        }

        risk_score = compute_equity_risk(row)
        eqi_band = get_eqi_band(eqi)

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
            VERA-NZ v0.1
        </p>
        <p style="color: white; font-size: 0.9rem; text-align: center; margin: 0 0 12px 0;">
            Verification Engine for<br>Results & Accountability
        </p>
        <p style="text-align: center;">
            <a href="https://data.govt.nz" target="_blank" style="
                color: {SILVER};
                font-size: 1rem;
                font-weight: 600;
                text-decoration: none;
                border-bottom: 2px solid {SILVER};
            ">data.govt.nz Open Data</a>
        </p>
    """, unsafe_allow_html=True)


# =============================================================================
# Load Data
# =============================================================================

schools_raw = fetch_nz_schools()
if schools_raw:
    df = prepare_dataframe(schools_raw)
else:
    st.error("Unable to load school data from data.govt.nz API")
    st.stop()


# =============================================================================
# Page: School Dashboard
# =============================================================================

if page == "📊 School Dashboard":
    st.title("Aotearoa School Dashboard")
    st.warning("**SAMPLE DATA** — This demonstration uses representative sample data. Production version will connect to the New Zealand Ministry of Education API.")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        school_types = ["All"] + sorted(df["school_type"].dropna().unique().tolist())
        selected_type = st.selectbox("School Type", school_types)
    with col2:
        regions = ["All"] + sorted(df["region"].dropna().unique().tolist())
        selected_region = st.selectbox("Region", regions)
    with col3:
        eqi_bands = ["All", "More Barriers", "Moderate Barriers", "Fewer Barriers"]
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
        st.info("EQI data not available in current dataset. Showing decile-based analysis.")

    # School table
    st.markdown("### Schools")
    display_cols = ["school_name", "school_type", "region", "decile", "eqi", "eqi_band", "total_roll", "maori_pct", "pasifika_pct", "risk_score"]
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
    st.title("Equity Index (EQI) Analysis")
    st.warning("**SAMPLE DATA** — Results shown use representative sample data for demonstration purposes.")

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
            hover_data=["region", "decile", "total_roll"]
        )
        fig.update_layout(
            xaxis_title="Māori + Pasifika %",
            yaxis_title="Equity Index"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("EQI data not available. The Ministry of Education provides EQI data separately.")

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
    st.title("Māori & Pasifika Achievement Focus")
    st.warning("**SAMPLE DATA** — Results shown use representative sample data for demonstration purposes.")

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
        high_both_sorted[["school_name", "region", "total_roll", "maori_pct", "pasifika_pct", "decile", "eqi_band"]].head(30),
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
    st.warning("**SAMPLE DATA** — Results shown use representative sample data for demonstration purposes.")

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

    ## Data Sources

    All data from **[data.govt.nz](https://data.govt.nz)**, New Zealand's open data portal:

    - **School Directory API:** School locations, types, contact details
    - **Roll Data:** Student enrollment by demographics
    - **Equity Index:** EQI bands and scores (when available)

    **Additional Sources (manual integration):**
    - NZQA NCEA statistics (CSV download)
    - Ministry of Education attendance data
    - Education Counts statistical tables

    ---

    ## Coming Soon

    - NCEA achievement data integration
    - Attendance correlation analysis
    - Oral-written delta detection (aligned with NCEA oral language requirements)
    - School-level intervention verification

    ---

    <p style="color: #666; font-size: 0.9rem;">
        VERA-NZ v0.1 | Built by <a href="https://hallucinations.cloud" style="color: {BLACK};">Hallucinations.cloud</a> |
        An <a href="https://h-edu.solutions" style="color: {BLACK};">H-EDU.Solutions</a> Initiative
    </p>
    """, unsafe_allow_html=True)
