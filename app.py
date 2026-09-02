"""
Weather Data Analyzer - Streamlit Dashboard
Interactive analytics, statistical charts, automated insights, and KPI metrics.
"""

import os
import streamlit as st
import pandas as pd
import weather_analysis as wa

# Streamlit Page Configuration
st.set_page_config(
    page_title="Weather Data Analyzer",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Glassmorphism, gradients, clean metric cards)
st.markdown("""
<style>
    /* Global Styles */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Header hero container */
    .hero-container {
        background: linear-gradient(135deg, #1d3557 0%, #457b9d 50%, #a8dadc 100%);
        border-radius: 16px;
        padding: 26px 32px;
        margin-bottom: 24px;
        color: white;
        box-shadow: 0 10px 25px rgba(0,0,0,0.12);
    }
    
    .hero-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .hero-subtitle {
        font-size: 1.05rem;
        font-weight: 300;
        opacity: 0.92;
        margin-top: 6px;
        margin-bottom: 0;
    }

    /* Metric Cards */
    .metric-card {
        background: white;
        border-radius: 14px;
        padding: 18px 20px;
        border: 1px solid #EAEAEA;
        box-shadow: 0 4px 12px rgba(0,0,0,0.04);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        position: relative;
        overflow: hidden;
    }
    
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.08);
    }

    .metric-label {
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #6C757D;
        margin-bottom: 4px;
    }

    .metric-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #1D3557;
        margin: 0;
        line-height: 1.2;
    }

    .metric-footer {
        font-size: 0.8rem;
        color: #8D99AE;
        margin-top: 6px;
    }

    .card-border-temp { border-left: 5px solid #E76F51; }
    .card-border-rain { border-left: 5px solid #3A86FF; }
    .card-border-hum { border-left: 5px solid #00B4D8; }
    .card-border-wind { border-left: 5px solid #8338EC; }

    /* Insight Card */
    .insight-box {
        background: #F8F9FA;
        border: 1px solid #E9ECEF;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 14px;
        display: flex;
        gap: 16px;
        align-items: flex-start;
        box-shadow: 0 2px 6px rgba(0,0,0,0.02);
    }

    .insight-icon {
        font-size: 1.8rem;
        line-height: 1;
        padding: 6px;
        background: white;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }

    .insight-content h4 {
        margin: 0 0 4px 0;
        font-size: 1.05rem;
        color: #1D3557;
        font-weight: 600;
    }

    .insight-content p {
        margin: 0;
        color: #495057;
        font-size: 0.92rem;
        line-height: 1.45;
    }

    .badge-pill {
        display: inline-block;
        padding: 3px 10px;
        font-size: 0.75rem;
        font-weight: 600;
        border-radius: 50px;
        background-color: #E2EAFC;
        color: #1D3557;
        margin-bottom: 4px;
    }

    /* Tab and section styling */
    .section-title {
        font-size: 1.35rem;
        font-weight: 700;
        color: #1D3557;
        margin-top: 10px;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
</style>
""", unsafe_allow_html=True)


# =====================================================================
# State & Data Loading
# =====================================================================
DEFAULT_DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "weather_data.csv")

st.sidebar.markdown("## 🌤️ Weather Analyzer")
st.sidebar.caption("Historical Meteorological Intelligence & Visual Analytics")

data_source_mode = st.sidebar.radio(
    "Data Source Mode",
    ["Use Sample Weather Dataset", "Upload Custom CSV File"],
    index=0
)

uploaded_file = None
if data_source_mode == "Upload Custom CSV File":
    uploaded_file = st.sidebar.file_uploader(
        "Upload Weather CSV",
        type=["csv"],
        help="Upload a CSV with Date, Temperature, Humidity, Precipitation, and WindSpeed columns."
    )

# Load dataset
try:
    if data_source_mode == "Upload Custom CSV File" and uploaded_file is not None:
        raw_df, cleaning_report = wa.load_and_clean_data(uploaded_file)
        data_name = uploaded_file.name
    else:
        if os.path.exists(DEFAULT_DATA_PATH):
            raw_df, cleaning_report = wa.load_and_clean_data(DEFAULT_DATA_PATH)
            data_name = "weather_data.csv (Default Sample)"
        else:
            st.error("Default sample dataset not found. Please upload a CSV.")
            st.stop()
except Exception as e:
    st.error(f"Error loading and processing dataset: {e}")
    st.stop()

# =====================================================================
# Sidebar Navigation & Filters
# =====================================================================
st.sidebar.markdown("---")
st.sidebar.markdown("### 🗂️ Navigation")
page = st.sidebar.radio(
    "Select Section",
    [
        "Dashboard Overview",
        "Temperature Analysis",
        "Rainfall Analysis",
        "Humidity Analysis",
        "Weather Insights",
        "Data Visualization"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Filters")

df_filtered = raw_df.copy()

# Filter by Year if available
if "Year" in df_filtered.columns:
    available_years = sorted(df_filtered["Year"].unique().tolist())
    selected_years = st.sidebar.multiselect(
        "Filter by Year",
        options=available_years,
        default=available_years,
        help="Select one or more years to analyze."
    )
    if selected_years:
        df_filtered = df_filtered[df_filtered["Year"].isin(selected_years)]
    else:
        st.sidebar.warning("Please select at least one year.")

# Filter by Month if available
if "Month" in df_filtered.columns:
    month_map = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
        7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
    }
    avail_month_nums = sorted(df_filtered["Month"].unique().tolist())
    selected_months = st.sidebar.multiselect(
        "Filter by Month",
        options=avail_month_nums,
        format_func=lambda m: month_map.get(m, str(m)),
        default=avail_month_nums
    )
    if selected_months:
        df_filtered = df_filtered[df_filtered["Month"].isin(selected_months)]
    else:
        st.sidebar.warning("Please select at least one month.")

if df_filtered.empty:
    st.warning("⚠️ No data records match the selected filters. Please adjust your selections in the sidebar.")
    st.stop()

# Re-compute stats on filtered slice
stats = wa.calculate_weather_stats(df_filtered)
monthly_analysis = wa.calculate_monthly_analysis(df_filtered)
insights = wa.generate_smart_insights(df_filtered)

# =====================================================================
# Main Header Banner
# =====================================================================
st.markdown(f"""
<div class="hero-container">
    <h1 class="hero-title">🌤️ Weather Data Analyzer</h1>
    <p class="hero-subtitle">
        Analyzing <b>{len(df_filtered):,}</b> records from <b>{data_name}</b> | 
        {df_filtered['Date'].min().strftime('%d %b %Y') if 'Date' in df_filtered.columns else ''} – 
        {df_filtered['Date'].max().strftime('%d %b %Y') if 'Date' in df_filtered.columns else ''}
    </p>
</div>
""", unsafe_allow_html=True)


# =====================================================================
# SECTION 1: Dashboard Overview
# =====================================================================
if page == "Dashboard Overview":
    st.markdown('<div class="section-title">📊 Executive Meteorological Summary</div>', unsafe_allow_html=True)
    
    # 4 Key KPI Metric Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_t = stats.get('avg_temp', 'N/A')
        max_t = stats.get('max_temp', 'N/A')
        min_t = stats.get('min_temp', 'N/A')
        st.markdown(f"""
        <div class="metric-card card-border-temp">
            <div class="metric-label">Average Temperature</div>
            <div class="metric-value">{avg_t}°C</div>
            <div class="metric-footer">Min: {min_t}°C | Max: {max_t}°C</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        tot_rain = stats.get('total_precipitation', 'N/A')
        rainy_pct = stats.get('rainy_days_pct', 0)
        rainy_count = stats.get('rainy_days_count', 0)
        st.markdown(f"""
        <div class="metric-card card-border-rain">
            <div class="metric-label">Total Rainfall</div>
            <div class="metric-value">{tot_rain} mm</div>
            <div class="metric-footer">{rainy_count} wet days ({rainy_pct}% frequency)</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        avg_h = stats.get('avg_humidity', 'N/A')
        min_h = stats.get('min_humidity', 'N/A')
        max_h = stats.get('max_humidity', 'N/A')
        st.markdown(f"""
        <div class="metric-card card-border-hum">
            <div class="metric-label">Average Humidity</div>
            <div class="metric-value">{avg_h}%</div>
            <div class="metric-footer">Range: {min_h}% to {max_h}%</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        avg_w = stats.get('avg_wind_speed', 'N/A')
        max_w = stats.get('max_wind_speed', 'N/A')
        st.markdown(f"""
        <div class="metric-card card-border-wind">
            <div class="metric-label">Average Wind Speed</div>
            <div class="metric-value">{avg_w} km/h</div>
            <div class="metric-footer">Peak Gust: {max_w} km/h</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Notable Weather Records Grid
    st.markdown('<div class="section-title">🏆 All-Time Extreme Records</div>', unsafe_allow_html=True)
    rcol1, rcol2, rcol3, rcol4 = st.columns(4)
    
    with rcol1:
        hd = stats.get("hottest_day", {})
        st.info(f"🔥 **Hottest Day**\n\n**{hd.get('temp', 'N/A')}°C**\n\n📅 {hd.get('date', 'N/A')}\n\n🏷️ {hd.get('condition', '')}")
    with rcol2:
        cd = stats.get("coldest_day", {})
        st.info(f"❄️ **Coldest Day**\n\n**{cd.get('temp', 'N/A')}°C**\n\n📅 {cd.get('date', 'N/A')}\n\n🏷️ {cd.get('condition', '')}")
    with rcol3:
        rd = stats.get("rainiest_day", {})
        st.info(f"🌧️ **Rainiest Day**\n\n**{rd.get('rainfall', 'N/A')} mm**\n\n📅 {rd.get('date', 'N/A')}\n\n🏷️ {rd.get('condition', '')}")
    with rcol4:
        hmd = stats.get("most_humid_day", {})
        st.info(f"💧 **Most Humid Day**\n\n**{hmd.get('humidity', 'N/A')}%**\n\n📅 {hmd.get('date', 'N/A')}\n\n🌡️ {hmd.get('temp', 'N/A')}°C")

    # Snapshot Charts
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Temperature Progression**")
        st.pyplot(wa.plot_temperature_trend(df_filtered), use_container_width=True)
    with c2:
        st.markdown("**Monthly Rainfall Volume**")
        if "monthly_summary_df" in monthly_analysis:
            st.pyplot(wa.plot_monthly_rainfall(monthly_analysis["monthly_summary_df"]), use_container_width=True)

    # Dataset inspection preview
    st.markdown("---")
    st.markdown('<div class="section-title">📋 Dataset Inspection (First 5 Rows)</div>', unsafe_allow_html=True)
    st.dataframe(df_filtered.head(5), use_container_width=True)
    
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Filtered Records", f"{df_filtered.shape[0]:,}")
    col_b.metric("Total Columns", f"{df_filtered.shape[1]}")
    col_c.metric("Duplicates Handled", f"{cleaning_report['duplicates_removed']}")


# =====================================================================
# SECTION 2: Temperature Analysis
# =====================================================================
elif page == "Temperature Analysis":
    st.markdown('<div class="section-title">🌡️ Comprehensive Temperature Analysis</div>', unsafe_allow_html=True)
    
    t1, t2, t3 = st.columns(3)
    t1.metric("Average Temperature", f"{stats.get('avg_temp', 'N/A')}°C")
    t2.metric("Maximum Temperature", f"{stats.get('max_temp', 'N/A')}°C")
    t3.metric("Minimum Temperature", f"{stats.get('min_temp', 'N/A')}°C")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 📈 Temperature Trend Line Over Time")
    st.pyplot(wa.plot_temperature_trend(df_filtered), use_container_width=True)
    
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.markdown("#### 📊 Monthly Average Temperature")
        if "monthly_summary_df" in monthly_analysis:
            st.pyplot(wa.plot_monthly_avg_temp(monthly_analysis["monthly_summary_df"]), use_container_width=True)
    with col_chart2:
        st.markdown("#### 📉 Temperature Distribution & Density")
        st.pyplot(wa.plot_temp_distribution(df_filtered), use_container_width=True)

    if "hottest_month" in monthly_analysis and "coldest_month" in monthly_analysis:
        hm = monthly_analysis["hottest_month"]
        cm = monthly_analysis["coldest_month"]
        st.markdown("---")
        st.success(f"☀️ **Hottest Month**: **{hm['name']}** with an average temperature of **{hm['avg_temp']}°C**.")
        st.info(f"❄️ **Coldest Month**: **{cm['name']}** with an average temperature of **{cm['avg_temp']}°C**.")


# =====================================================================
# SECTION 3: Rainfall Analysis
# =====================================================================
elif page == "Rainfall Analysis":
    st.markdown('<div class="section-title">🌧️ Precipitation & Rainfall Dynamics</div>', unsafe_allow_html=True)

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Total Rainfall", f"{stats.get('total_precipitation', 'N/A')} mm")
    r2.metric("Daily Average Rainfall", f"{stats.get('avg_precipitation', 'N/A')} mm")
    r3.metric("Rainy Days Count", f"{stats.get('rainy_days_count', 'N/A')}")
    r4.metric("Rainy Day Frequency", f"{stats.get('rainy_days_pct', 'N/A')}%")

    st.markdown("<br>", unsafe_allow_html=True)
    if "monthly_summary_df" in monthly_analysis:
        st.markdown("#### 📊 Monthly Cumulative Precipitation")
        st.pyplot(wa.plot_monthly_rainfall(monthly_analysis["monthly_summary_df"]), use_container_width=True)

    col_lead, col_mon = st.columns([1.2, 1])
    with col_lead:
        st.markdown("#### 🏆 Top 10 Heaviest Rain Days")
        if "Precipitation_mm" in df_filtered.columns:
            rainy_top = (
                df_filtered[df_filtered["Precipitation_mm"] > 0]
                .sort_values("Precipitation_mm", ascending=False)
                [["Date", "Precipitation_mm", "Temperature_C", "Weather_Condition"]]
                .head(10)
                .reset_index(drop=True)
            )
            st.dataframe(rainy_top, use_container_width=True)
    with col_mon:
        st.markdown("#### 📅 Monthly Precipitation Table")
        if "monthly_summary_df" in monthly_analysis:
            month_p_table = monthly_analysis["monthly_summary_df"][["Month_Name", "Precipitation_mm"]].rename(
                columns={"Month_Name": "Month", "Precipitation_mm": "Rainfall (mm)"}
            )
            st.dataframe(month_p_table, use_container_width=True)


# =====================================================================
# SECTION 4: Humidity Analysis
# =====================================================================
elif page == "Humidity Analysis":
    st.markdown('<div class="section-title">💧 Humidity & Atmospheric Conditions</div>', unsafe_allow_html=True)

    h1, h2, h3, h4 = st.columns(4)
    h1.metric("Average Humidity", f"{stats.get('avg_humidity', 'N/A')}%")
    h2.metric("Maximum Humidity", f"{stats.get('max_humidity', 'N/A')}%")
    h3.metric("Minimum Humidity", f"{stats.get('min_humidity', 'N/A')}%")
    h4.metric("Average Wind Speed", f"{stats.get('avg_wind_speed', 'N/A')} km/h")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 📈 Humidity Trends Over Time")
    st.pyplot(wa.plot_humidity_trend(df_filtered), use_container_width=True)

    col_h1, col_h2 = st.columns(2)
    with col_h1:
        st.markdown("#### 🔄 Temperature vs. Humidity Relationship")
        st.pyplot(wa.plot_temp_vs_humidity(df_filtered), use_container_width=True)
    with col_h2:
        st.markdown("#### ☁️ Weather Condition Distribution")
        st.pyplot(wa.plot_weather_condition_pie(df_filtered), use_container_width=True)


# =====================================================================
# SECTION 5: Weather Insights
# =====================================================================
elif page == "Weather Insights":
    st.markdown('<div class="section-title">💡 Automated Smart Meteorological Insights</div>', unsafe_allow_html=True)
    st.caption("AI-driven narrative synthesis derived from patterns, statistical correlations, and seasonal records.")

    for ins in insights:
        st.markdown(f"""
        <div class="insight-box">
            <div class="insight-icon">{ins['icon']}</div>
            <div class="insight-content">
                <span class="badge-pill">{ins['category']}</span>
                <h4>{ins['headline']}</h4>
                <p>{ins['text']}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 🔬 Correlation Heatmap Between Weather Variables")
    st.pyplot(wa.plot_correlation_heatmap(df_filtered), use_container_width=True)


# =====================================================================
# SECTION 6: Data Visualization & Data Explorer
# =====================================================================
elif page == "Data Visualization":
    st.markdown('<div class="section-title">📊 Multi-Chart Visual Gallery & Data Explorer</div>', unsafe_allow_html=True)

    viz_tab1, viz_tab2 = st.tabs(["🖼️ All Charts Gallery", "🔍 Cleaned Data Explorer & Export"])

    with viz_tab1:
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("##### 1. Temperature Timeline")
            st.pyplot(wa.plot_temperature_trend(df_filtered), use_container_width=True)
            
            st.markdown("##### 3. Monthly Rainfall")
            if "monthly_summary_df" in monthly_analysis:
                st.pyplot(wa.plot_monthly_rainfall(monthly_analysis["monthly_summary_df"]), use_container_width=True)
                
            st.markdown("##### 5. Temperature Distribution (Histogram + KDE)")
            st.pyplot(wa.plot_temp_distribution(df_filtered), use_container_width=True)
            
            st.markdown("##### 7. Correlation Heatmap")
            st.pyplot(wa.plot_correlation_heatmap(df_filtered), use_container_width=True)

        with col_g2:
            st.markdown("##### 2. Monthly Average Temperature")
            if "monthly_summary_df" in monthly_analysis:
                st.pyplot(wa.plot_monthly_avg_temp(monthly_analysis["monthly_summary_df"]), use_container_width=True)
                
            st.markdown("##### 4. Humidity Trends")
            st.pyplot(wa.plot_humidity_trend(df_filtered), use_container_width=True)
            
            st.markdown("##### 6. Temperature vs. Humidity Regression")
            st.pyplot(wa.plot_temp_vs_humidity(df_filtered), use_container_width=True)
            
            st.markdown("##### 8. Weather Condition Donut Chart")
            st.pyplot(wa.plot_weather_condition_pie(df_filtered), use_container_width=True)

    with viz_tab2:
        st.markdown("#### 🧹 Data Cleaning Audit Report")
        cr1, cr2, cr3, cr4 = st.columns(4)
        cr1.metric("Initial Rows", cleaning_report["initial_rows"])
        cr2.metric("Duplicates Dropped", cleaning_report["duplicates_removed"])
        cr3.metric("Final Clean Rows", cleaning_report["final_rows"])
        cr4.metric("Remaining Null Values", cleaning_report["final_nulls"])

        st.markdown("#### 🗃️ Column Types & Attributes")
        col_summary = pd.DataFrame({
            "Column": df_filtered.columns,
            "Data Type": [str(t) for t in df_filtered.dtypes],
            "Non-Null Count": df_filtered.count().values,
            "Unique Values": df_filtered.nunique().values
        })
        st.dataframe(col_summary, use_container_width=True)

        st.markdown("#### 📄 Filtered Data Table")
        st.dataframe(df_filtered, use_container_width=True)

        # CSV Download Button
        csv_data = df_filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Cleaned Weather Data (CSV)",
            data=csv_data,
            file_name="cleaned_weather_data.csv",
            mime="text/csv"
        )

# Footer
st.markdown("---")
st.caption("Weather Data Analyzer • Built with Python, Pandas, Matplotlib, Seaborn & Streamlit")
