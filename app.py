import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os

# ─── PAGE CONFIG ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Mumbai Real Estate Intelligence | Aditya Bute",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CUSTOM CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    h1 { color: #1B3A6B !important; }
    h2 { color: #1B3A6B !important; border-bottom: 2px solid #E8A838;
         padding-bottom: 8px; }
    h3 { color: #1B3A6B !important; }
    [data-testid="metric-container"] {
        background: white;
        border: 1px solid #e0e0e0;
        border-left: 4px solid #E8A838;
        border-radius: 4px;
        padding: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f4f8;
        border-radius: 4px 4px 0 0;
        color: #1B3A6B;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1B3A6B !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# ─── COLOR CONSTANTS ────────────────────────────────────────────────────────
NAVY  = "#1B3A6B"
GOLD  = "#E8A838"
GREEN = "#2ECC71"
RED   = "#E74C3C"

# ─── COLUMN NAME CONSTANTS ──────────────────────────────────────────────────
PRICE_COL = "price_inr"       
AREA_COL  = "area_sqft"       
PSF_COL   = "price_per_sqft"  

# ─── LOAD & CACHE DATA ──────────────────────────────────────────────────────
@st.cache_data
def load_data():
    paths = [
        'data/cleaned_listings.csv',
        'cleaned_listings.csv',
        os.path.join(os.path.dirname(__file__), 'data', 'cleaned_listings.csv')
    ]
    for p in paths:
        if os.path.exists(p):
            df = pd.read_csv(p, low_memory=False)
            # Normalise column names: lowercase, replace spaces and brackets
            df.columns = (
                df.columns
                .str.lower()
                .str.strip()
                .str.replace(' ', '_', regex=False)
                .str.replace('(', '', regex=False)
                .str.replace(')', '', regex=False)
            )
            
            # Map locality_clean to locality for script compatibility
            if 'locality_clean' in df.columns and 'locality' not in df.columns:
                df.rename(columns={'locality_clean': 'locality'}, inplace=True)
                
            return df
    return None

df_raw = load_data()

if df_raw is None:
    st.error("❌ Cannot find cleaned_listings.csv. Ensure it is in the data/ folder of this repository.")
    st.stop()

# ─── SIDEBAR FILTERS ────────────────────────────────────────────────────────
st.sidebar.markdown("## 🔍 Dashboard Filters")
st.sidebar.markdown("---")

all_cities = sorted(df_raw['city'].dropna().unique().tolist())
selected_cities = st.sidebar.multiselect(
    "🏙️ City", all_cities, default=all_cities
)

all_bhk = sorted(df_raw['bhk'].dropna().unique().tolist())
selected_bhk = st.sidebar.multiselect(
    "🛏️ BHK Type", all_bhk, default=all_bhk
)

all_furnishing = sorted(df_raw['furnishing'].dropna().unique().tolist())
selected_furnishing = st.sidebar.multiselect(
    "🛋️ Furnishing", all_furnishing, default=all_furnishing
)

min_price = int(df_raw[PRICE_COL].min())
max_price = int(df_raw[PRICE_COL].quantile(0.99))  # 99th percentile avoids extreme outlier skew

price_range = st.sidebar.slider(
    "💰 Price Range (₹)",
    min_value=min_price,
    max_value=max_price,
    value=(min_price, max_price)
)

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Dataset:** {len(df_raw):,} total listings")
st.sidebar.markdown("**Source:** MagicBricks / Kaggle · 2024")
st.sidebar.markdown(
    "[![GitHub](https://img.shields.io/badge/GitHub-Source_Code-1B3A6B?logo=github)]"
    "(https://github.com/AdityaBute/Mumbai-Real-Estate-Dashboard)"
)

# ─── APPLY FILTERS ──────────────────────────────────────────────────────────
df = df_raw.copy()

if selected_cities:
    df = df[df['city'].isin(selected_cities)]
if selected_bhk:
    df = df[df['bhk'].isin(selected_bhk)]
if selected_furnishing:
    df = df[df['furnishing'].isin(selected_furnishing)]

df = df[
    (df[PRICE_COL] >= price_range[0]) &
    (df[PRICE_COL] <= price_range[1])
]

# ─── MAIN HEADER ────────────────────────────────────────────────────────────
st.title("🏙️ Mumbai Real Estate Price Intelligence Dashboard")
st.markdown(
    f"Interactive analysis of **{len(df):,} listings** filtered from {len(df_raw):,} total · "
    f"Source: MagicBricks / Kaggle · Built by **Aditya Bute**"
)
st.markdown("---")

# ─── GLOBAL KPI METRICS ─────────────────────────────────────────────────────
if len(df) == 0:
    st.warning("⚠️ No listings match your current filters. Please adjust the sidebar.")
    st.stop()

c1, c2, c3, c4 = st.columns(4)

avg_price_cr     = df[PRICE_COL].mean() / 1e7
avg_psf          = df[PSF_COL].mean()
most_listed_city = df['city'].value_counts().idxmax()
total_filtered   = len(df)

c1.metric("🏘️ Total Listings",    f"{total_filtered:,}")
c2.metric("💰 Avg Price",         f"₹{avg_price_cr:.2f} Cr")
c3.metric("📐 Avg Price / Sqft",  f"₹{avg_psf:,.0f}")
c4.metric("🏆 Most Listed City",  most_listed_city)

st.markdown("---")

# ─── TABS ───────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "📊  City Overview",
    "📍  Locality Intelligence",
    "🔍  Property Explorer"
])

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1 — CITY OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════
with tab1:
    st.header("City Overview")

    col_a, col_b = st.columns(2)

    with col_a:
        # Donut: BHK Configuration
        bhk_counts = df['bhk'].value_counts().reset_index()
        bhk_counts.columns = ['BHK Type', 'Count']

        fig_donut = px.pie(
            bhk_counts,
            names='BHK Type',
            values='Count',
            hole=0.42,
            title="Properties by BHK Configuration",
            color_discrete_sequence=px.colors.sequential.Blues_r
        )
        fig_donut.update_layout(
            title_font_color=NAVY, title_font_size=15,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2)
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with col_b:
        # Bar: Avg Price by BHK
        avg_bhk = (
            df.groupby('bhk')[PRICE_COL]
            .mean()
            .reset_index()
        )
        avg_bhk.columns = ['BHK Type', 'Avg Price INR']
        avg_bhk['Avg Price (Cr)'] = (avg_bhk['Avg Price INR'] / 1e7).round(2)
        avg_bhk = avg_bhk.sort_values('Avg Price (Cr)', ascending=True)

        fig_bhk = px.bar(
            avg_bhk,
            x='Avg Price (Cr)', y='BHK Type',
            orientation='h',
            title="Average Price by BHK Type (₹ Crores)",
            color='Avg Price (Cr)',
            color_continuous_scale=[[0, '#93b7d6'], [1, NAVY]],
            text='Avg Price (Cr)'
        )
        fig_bhk.update_traces(texttemplate='₹%{text:.2f} Cr', textposition='outside')
        fig_bhk.update_layout(
            title_font_color=NAVY, title_font_size=15,
            coloraxis_showscale=False, xaxis_title="Avg Price (₹ Cr)"
        )
        st.plotly_chart(fig_bhk, use_container_width=True)

    # Treemap: Top 20 localities
    loc_vol = df['locality'].value_counts().head(20).reset_index()
    loc_vol.columns = ['Locality', 'Listings']

    fig_tree = px.treemap(
        loc_vol,
        path=['Locality'],
        values='Listings',
        title="Top 20 Localities by Listing Volume",
        color='Listings',
        color_continuous_scale=[[0, '#d0e4f5'], [1, NAVY]]
    )
    fig_tree.update_layout(
        title_font_color=NAVY, title_font_size=15,
        margin=dict(t=50, l=0, r=0, b=0)
    )
    st.plotly_chart(fig_tree, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 2 — LOCALITY INTELLIGENCE
# ═══════════════════════════════════════════════════════════════════════════
with tab2:
    st.header("Locality Intelligence")

    # Build locality stats table
    overall_avg_psf = df[PSF_COL].mean()

    loc_stats = (
        df.groupby('locality')
        .agg(
            Avg_Price_INR   = (PRICE_COL, 'mean'),
            Total_Listings  = (PRICE_COL, 'count'),
            Avg_PSF         = (PSF_COL,   'mean'),
            Avg_Area        = (AREA_COL,  'mean')
        )
        .reset_index()
    )
    loc_stats.rename(columns={'locality': 'Locality'}, inplace=True)
    loc_stats['Avg Price (Cr)']        = (loc_stats['Avg_Price_INR'] / 1e7).round(2)
    loc_stats['Avg Price/Sqft']        = loc_stats['Avg_PSF'].round(0).astype(int)
    loc_stats['Avg Area (sqft)']       = loc_stats['Avg_Area'].round(0).astype(int)
    loc_stats['Price Premium Index']   = (
        (loc_stats['Avg_PSF'] - overall_avg_psf) / overall_avg_psf * 100
    ).round(1)

    col_x, col_y = st.columns(2)

    with col_x:
        # Top 15 localities by Avg Price/Sqft (min 10 listings)
        top15 = (
            loc_stats[loc_stats['Total_Listings'] >= 10]
            .nlargest(15, 'Avg Price/Sqft')
            .sort_values('Avg Price/Sqft')
        )

        fig_loc_bar = px.bar(
            top15,
            x='Avg Price/Sqft', y='Locality',
            orientation='h',
            title="Top 15 Localities — Avg Price per Sqft (₹)",
            color='Avg Price/Sqft',
            color_continuous_scale=[[0, '#93b7d6'], [1, NAVY]],
            text='Avg Price/Sqft'
        )
        fig_loc_bar.update_traces(texttemplate='₹%{text:,}', textposition='outside')
        fig_loc_bar.update_layout(
            title_font_color=NAVY, title_font_size=14,
            coloraxis_showscale=False, xaxis_title="Avg Price per Sqft (₹)"
        )
        st.plotly_chart(fig_loc_bar, use_container_width=True)

    with col_y:
        # Bubble scatter: Avg Price vs Avg Area (min 50 listings for meaningful bubbles)
        scatter_data = loc_stats[loc_stats['Total_Listings'] >= 50].copy()

        fig_bubble = px.scatter(
            scatter_data,
            x='Avg Price (Cr)',
            y='Avg Area (sqft)',
            size='Total_Listings',
            hover_name='Locality',
            hover_data={
                'Avg Price/Sqft': True,
                'Total_Listings': True,
                'Price Premium Index': True
            },
            title="Locality: Avg Price vs Avg Property Size",
            color='Avg Price/Sqft',
            color_continuous_scale=[[0, GREEN], [0.5, GOLD], [1, RED]]
        )
        fig_bubble.update_layout(
            title_font_color=NAVY, title_font_size=14,
            xaxis_title="Avg Price (₹ Cr)",
            yaxis_title="Avg Area (sqft)"
        )
        st.plotly_chart(fig_bubble, use_container_width=True)

    # Best Value / Premium KPI cards
    meaningful = loc_stats[
        (loc_stats['Total_Listings'] >= 50) &
        (loc_stats['Locality'] != 'Unknown')
    ]

    if len(meaningful) > 0:
        best_row    = meaningful.loc[meaningful['Avg Price/Sqft'].idxmin()]
        premium_row = meaningful.loc[meaningful['Avg Price/Sqft'].idxmax()]

        kc1, kc2 = st.columns(2)
        kc1.metric(
            "🏷️ Best Value Area",
            best_row['Locality'],
            f"₹{best_row['Avg Price/Sqft']:,}/sqft"
        )
        kc2.metric(
            "⭐ Premium Area",
            premium_row['Locality'],
            f"₹{premium_row['Avg Price/Sqft']:,}/sqft"
        )

    # Locality comparison table with conditional formatting
    st.subheader("📋 Locality Market Intelligence")
    st.caption("Sorted by Avg Price/Sqft descending. Showing localities with 10+ listings.")

    display_table = (
        loc_stats[loc_stats['Total_Listings'] >= 10]
        [['Locality', 'Avg Price (Cr)', 'Total_Listings', 'Avg Price/Sqft', 'Price Premium Index']]
        .rename(columns={'Total_Listings': 'Total Listings'})
        .sort_values('Avg Price/Sqft', ascending=False)
        .reset_index(drop=True)
    )

    st.dataframe(
        display_table.style.background_gradient(
            subset=['Price Premium Index'],
            cmap='RdYlGn_r'
        ).format({
            'Avg Price (Cr)':      '₹{:.2f} Cr',
            'Avg Price/Sqft':      '₹{:,}',
            'Price Premium Index': '{:+.1f}%'
        }),
        use_container_width=True,
        hide_index=True
    )


# ═══════════════════════════════════════════════════════════════════════════
# TAB 3 — PROPERTY EXPLORER
# ═══════════════════════════════════════════════════════════════════════════
with tab3:
    st.header("Property Explorer")

    col_p, col_q = st.columns(2)

    with col_p:
        # Price Distribution Histogram (bucketed)
        price_bins   = [0, 2500000, 5000000, 7500000, 10000000,
                        15000000, 20000000, 30000000, 50000000, float('inf')]
        bucket_labels = [
            '<₹25L', '₹25L–50L', '₹50L–75L', '₹75L–1Cr',
            '₹1–1.5Cr', '₹1.5–2Cr', '₹2–3Cr', '₹3–5Cr', '>₹5Cr'
        ]

        df_hist = df.copy()
        df_hist['Price Bucket'] = pd.cut(
            df_hist[PRICE_COL], bins=price_bins, labels=bucket_labels
        )
        bucket_counts = (
            df_hist['Price Bucket']
            .value_counts()
            .reindex(bucket_labels)
            .reset_index()
        )
        bucket_counts.columns = ['Price Range', 'Count']

        fig_hist = px.bar(
            bucket_counts,
            x='Price Range', y='Count',
            title="Price Distribution Across Mumbai",
            color='Count',
            color_continuous_scale=[[0, '#93b7d6'], [1, NAVY]],
            text='Count'
        )
        fig_hist.update_traces(texttemplate='%{text:,}', textposition='outside')
        fig_hist.update_layout(
            title_font_color=NAVY, title_font_size=14,
            coloraxis_showscale=False,
            xaxis_tickangle=-30,
            xaxis_title="Price Range",
            yaxis_title="Number of Properties"
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    with col_q:
        # Gauge: Avg price vs ₹1.5 Cr benchmark
        avg_cr_filtered = df[PRICE_COL].mean() / 1e7
        benchmark_cr    = 1.5

        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=round(avg_cr_filtered, 2),
            delta={
                'reference': benchmark_cr,
                'valueformat': '.2f',
                'increasing': {'color': RED},
                'decreasing': {'color': GREEN}
            },
            title={'text': "Avg Price vs ₹1.5 Cr Benchmark", 'font': {'color': NAVY, 'size': 14}},
            number={'suffix': " Cr", 'valueformat': '.2f', 'font': {'color': NAVY}},
            gauge={
                'axis': {'range': [0, 5], 'tickcolor': NAVY},
                'bar': {'color': NAVY},
                'bgcolor': 'white',
                'bordercolor': '#e0e0e0',
                'steps': [
                    {'range': [0,   1.5], 'color': '#d4edda'},
                    {'range': [1.5, 3.0], 'color': '#fff3cd'},
                    {'range': [3.0, 5.0], 'color': '#f8d7da'}
                ],
                'threshold': {
                    'line': {'color': GOLD, 'width': 4},
                    'thickness': 0.75,
                    'value': benchmark_cr
                }
            }
        ))
        fig_gauge.update_layout(height=320, margin=dict(t=60, b=20))
        st.plotly_chart(fig_gauge, use_container_width=True)

    # Matrix: BHK × Furnishing (pivot table)
    st.subheader("📊 Avg Price (₹ Cr) — BHK Type × Furnishing Status")
    st.caption("Click any column header to sort. Each cell shows the average price for that combination.")

    if len(df) > 0:
        pivot = df.pivot_table(
            values=PRICE_COL,
            index='bhk',
            columns='furnishing',
            aggfunc='mean'
        ) / 1e7

        pivot = pivot.round(2)
        pivot.index.name = 'BHK Type'

        st.dataframe(
            pivot.style
            .background_gradient(cmap='Blues')
            .format('₹{:.2f} Cr'),
            use_container_width=True
        )

    # Scatter: Area vs Price by BHK
    st.subheader("🔵 Property Size vs Price by BHK Type")
    st.caption("Each dot is one property. Use the sidebar filters to narrow down.")

    sample = df.sample(min(6000, len(df)), random_state=42) if len(df) > 6000 else df

    fig_scatter3 = px.scatter(
        sample,
        x=AREA_COL,
        y=PRICE_COL,
        color='bhk',
        opacity=0.45,
        title="Area (sqft) vs Price (INR) — colored by BHK type",
        labels={
            AREA_COL:  'Area (sqft)',
            PRICE_COL: 'Price (INR)'
        },
        hover_data=['locality', 'city', 'furnishing'],
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig_scatter3.update_layout(
        title_font_color=NAVY, title_font_size=14,
        legend_title="BHK Type"
    )
    st.plotly_chart(fig_scatter3, use_container_width=True)


# ─── FOOTER ─────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "**Aditya Bute** · Final-year CS Engineering (2026) · "
    "[GitHub](https://github.com/AdityaBute/Mumbai-Real-Estate-Dashboard) · "
    "Data: MagicBricks / Kaggle · Dashboard built with Streamlit + Plotly"
)