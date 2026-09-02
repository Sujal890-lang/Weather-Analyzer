"""
Weather Data Analyzer - Core Analysis & Visualization Engine
Provides modular functions for data ingestion, intelligent cleaning,
statistical computations, monthly aggregations, smart insights, and plotting.
"""

from typing import Dict, Any, Tuple, Optional, List
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns

# Configure default visual style
sns.set_theme(style="whitegrid")
plt.rcParams.update({
    "font.sans-serif": "DejaVu Sans",
    "figure.autolayout": True,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "axes.labelsize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "figure.titlesize": 16
})

# Color Palettes
PALETTES = {
    "temp_warm": "#E76F51",
    "temp_cool": "#2A9D8F",
    "rain": "#3A86FF",
    "humidity": "#00B4D8",
    "wind": "#8338EC",
    "accent": "#F4A261",
    "dark": "#264653"
}

# Standard column aliases mapping
COLUMN_ALIASES = {
    "date": ["date", "datetime", "timestamp", "time", "record_date", "day"],
    "temperature": [
        "temperature_c", "temperature", "temp_c", "temp", "avg_temp",
        "mean_temp", "tavg", "temperature (c)", "temp(c)"
    ],
    "humidity": [
        "humidity_pct", "humidity", "relative_humidity", "rh", "hum",
        "humidity (%)", "humidity_percent"
    ],
    "precipitation": [
        "precipitation_mm", "precipitation", "rainfall_mm", "rainfall",
        "rain", "prcp", "rain_mm", "precipitation (mm)"
    ],
    "wind_speed": [
        "windspeed_kmh", "wind_speed", "windspeed", "wind_kph", "wind",
        "wind_speed_kmh", "wind (km/h)", "windspeed_mph"
    ],
    "pressure": [
        "pressure_hpa", "pressure", "barometer", "atm_pressure",
        "pressure (hpa)"
    ],
    "condition": [
        "weather_condition", "weather", "condition", "summary",
        "weather_type", "sky_condition"
    ]
}


def detect_column_mappings(df: pd.DataFrame) -> Dict[str, Optional[str]]:
    """
    Intelligently maps diverse CSV column names to standardized metric names.
    """
    cleaned_cols = {col: col.strip().lower().replace(" ", "_") for col in df.columns}
    mapping: Dict[str, Optional[str]] = {}

    for standard_name, aliases in COLUMN_ALIASES.items():
        matched_original = None
        for orig_col, clean_col in cleaned_cols.items():
            if clean_col in aliases:
                matched_original = orig_col
                break
            # Partial prefix/suffix match
            if any(alias in clean_col for alias in aliases):
                matched_original = orig_col
                break
        mapping[standard_name] = matched_original

    return mapping


def load_and_clean_data(file_source: Any) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Reads a CSV dataset, detects schema, cleans duplicates/nulls,
    and extracts temporal attributes (Year, Month, Month_Name, Day, Day_Name).
    
    Returns:
        Tuple containing the cleaned DataFrame and a cleaning report dictionary.
    """
    if isinstance(file_source, str):
        df_raw = pd.read_csv(file_source)
    else:
        df_raw = pd.read_csv(file_source)

    initial_shape = df_raw.shape
    raw_columns = list(df_raw.columns)
    initial_null_counts = df_raw.isnull().sum().to_dict()
    initial_duplicates = int(df_raw.duplicated().sum())

    # Map column headers
    col_map = detect_column_mappings(df_raw)
    
    # Create standardized working copy
    df = df_raw.copy()
    rename_dict = {}
    standard_columns = {
        "date": "Date",
        "temperature": "Temperature_C",
        "humidity": "Humidity_pct",
        "precipitation": "Precipitation_mm",
        "wind_speed": "WindSpeed_kmh",
        "pressure": "Pressure_hPa",
        "condition": "Weather_Condition"
    }

    for std_key, std_col in standard_columns.items():
        orig = col_map.get(std_key)
        if orig and orig in df.columns:
            rename_dict[orig] = std_col

    df = df.rename(columns=rename_dict)

    # 1. Deduplication
    df = df.drop_duplicates().reset_index(drop=True)

    # 2. Date conversion and temporal parsing
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        # Drop rows with unparseable dates
        df = df.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)
        df["Year"] = df["Date"].dt.year
        df["Month"] = df["Date"].dt.month
        df["Month_Name"] = df["Date"].dt.strftime("%b")
        df["Year_Month"] = df["Date"].dt.to_period("M").astype(str)
        df["Day"] = df["Date"].dt.day
        df["Day_Name"] = df["Date"].dt.strftime("%a")

    # 3. Numeric conversions & intelligent missing value imputation
    numeric_targets = ["Temperature_C", "Humidity_pct", "Precipitation_mm", "WindSpeed_kmh", "Pressure_hPa"]
    for num_col in numeric_targets:
        if num_col in df.columns:
            df[num_col] = pd.to_numeric(df[num_col], errors="coerce")
            if df[num_col].isnull().any():
                # For precipitation, default missing to 0.0
                if num_col == "Precipitation_mm":
                    df[num_col] = df[num_col].fillna(0.0)
                else:
                    # Linear interpolate or median fill
                    df[num_col] = df[num_col].interpolate(method="linear").bfill().ffill()

    # 4. Weather Condition handling
    if "Weather_Condition" in df.columns:
        df["Weather_Condition"] = df["Weather_Condition"].fillna("Unknown").astype(str).str.strip().str.title()

    cleaning_report = {
        "initial_rows": initial_shape[0],
        "initial_cols": initial_shape[1],
        "final_rows": df.shape[0],
        "final_cols": df.shape[1],
        "raw_columns": raw_columns,
        "mapped_columns": {k: v for k, v in col_map.items() if v is not None},
        "duplicates_removed": initial_duplicates,
        "initial_nulls": initial_null_counts,
        "final_nulls": int(df.isnull().sum().sum()),
        "has_date": "Date" in df.columns,
        "has_temp": "Temperature_C" in df.columns,
        "has_humidity": "Humidity_pct" in df.columns,
        "has_precip": "Precipitation_mm" in df.columns,
        "has_wind": "WindSpeed_kmh" in df.columns,
        "has_condition": "Weather_Condition" in df.columns
    }

    return df, cleaning_report


def calculate_weather_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes primary summary metrics and extreme records.
    """
    stats: Dict[str, Any] = {}

    # Temperature
    if "Temperature_C" in df.columns and not df["Temperature_C"].empty:
        stats["avg_temp"] = float(np.round(df["Temperature_C"].mean(), 1))
        stats["max_temp"] = float(np.round(df["Temperature_C"].max(), 1))
        stats["min_temp"] = float(np.round(df["Temperature_C"].min(), 1))
        
        hottest_idx = df["Temperature_C"].idxmax()
        coldest_idx = df["Temperature_C"].idxmin()
        
        hottest_row = df.loc[hottest_idx]
        coldest_row = df.loc[coldest_idx]
        
        stats["hottest_day"] = {
            "date": hottest_row["Date"].strftime("%Y-%m-%d") if "Date" in df.columns else f"Row {hottest_idx}",
            "temp": float(np.round(hottest_row["Temperature_C"], 1)),
            "condition": hottest_row.get("Weather_Condition", "N/A")
        }
        stats["coldest_day"] = {
            "date": coldest_row["Date"].strftime("%Y-%m-%d") if "Date" in df.columns else f"Row {coldest_idx}",
            "temp": float(np.round(coldest_row["Temperature_C"], 1)),
            "condition": coldest_row.get("Weather_Condition", "N/A")
        }

    # Humidity
    if "Humidity_pct" in df.columns and not df["Humidity_pct"].empty:
        stats["avg_humidity"] = float(np.round(df["Humidity_pct"].mean(), 1))
        stats["max_humidity"] = float(np.round(df["Humidity_pct"].max(), 1))
        stats["min_humidity"] = float(np.round(df["Humidity_pct"].min(), 1))
        
        most_humid_idx = df["Humidity_pct"].idxmax()
        most_humid_row = df.loc[most_humid_idx]
        stats["most_humid_day"] = {
            "date": most_humid_row["Date"].strftime("%Y-%m-%d") if "Date" in df.columns else f"Row {most_humid_idx}",
            "humidity": float(np.round(most_humid_row["Humidity_pct"], 1)),
            "temp": float(np.round(most_humid_row.get("Temperature_C", 0), 1))
        }

    # Precipitation
    if "Precipitation_mm" in df.columns and not df["Precipitation_mm"].empty:
        stats["total_precipitation"] = float(np.round(df["Precipitation_mm"].sum(), 1))
        stats["avg_precipitation"] = float(np.round(df["Precipitation_mm"].mean(), 2))
        stats["rainy_days_count"] = int((df["Precipitation_mm"] > 0).sum())
        stats["rainy_days_pct"] = float(np.round((stats["rainy_days_count"] / len(df)) * 100, 1))

        rainiest_idx = df["Precipitation_mm"].idxmax()
        rainiest_row = df.loc[rainiest_idx]
        stats["rainiest_day"] = {
            "date": rainiest_row["Date"].strftime("%Y-%m-%d") if "Date" in df.columns else f"Row {rainiest_idx}",
            "rainfall": float(np.round(rainiest_row["Precipitation_mm"], 1)),
            "condition": rainiest_row.get("Weather_Condition", "N/A")
        }

    # Wind Speed
    if "WindSpeed_kmh" in df.columns and not df["WindSpeed_kmh"].empty:
        stats["avg_wind_speed"] = float(np.round(df["WindSpeed_kmh"].mean(), 1))
        stats["max_wind_speed"] = float(np.round(df["WindSpeed_kmh"].max(), 1))

    # Pressure
    if "Pressure_hPa" in df.columns and not df["Pressure_hPa"].empty:
        stats["avg_pressure"] = float(np.round(df["Pressure_hPa"].mean(), 1))

    return stats


def calculate_monthly_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Aggregates weather attributes across calendar months and detects seasonal extremes.
    """
    if "Month" not in df.columns:
        return {}

    month_order = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
    ]

    agg_dict = {}
    if "Temperature_C" in df.columns:
        agg_dict["Temperature_C"] = "mean"
    if "Precipitation_mm" in df.columns:
        agg_dict["Precipitation_mm"] = "sum"
    if "Humidity_pct" in df.columns:
        agg_dict["Humidity_pct"] = "mean"
    if "WindSpeed_kmh" in df.columns:
        agg_dict["WindSpeed_kmh"] = "mean"

    monthly_summary = (
        df.groupby(["Month", "Month_Name"], as_index=False)
        .agg(agg_dict)
        .sort_values("Month")
        .reset_index(drop=True)
    )

    # Round aggregations
    for col in monthly_summary.columns:
        if col not in ["Month", "Month_Name"]:
            monthly_summary[col] = monthly_summary[col].round(1)

    result: Dict[str, Any] = {
        "monthly_summary_df": monthly_summary
    }

    if "Temperature_C" in monthly_summary.columns and not monthly_summary.empty:
        hottest_m_idx = monthly_summary["Temperature_C"].idxmax()
        coldest_m_idx = monthly_summary["Temperature_C"].idxmin()
        result["hottest_month"] = {
            "name": monthly_summary.loc[hottest_m_idx, "Month_Name"],
            "avg_temp": float(monthly_summary.loc[hottest_m_idx, "Temperature_C"])
        }
        result["coldest_month"] = {
            "name": monthly_summary.loc[coldest_m_idx, "Month_Name"],
            "avg_temp": float(monthly_summary.loc[coldest_m_idx, "Temperature_C"])
        }

    if "Precipitation_mm" in monthly_summary.columns and not monthly_summary.empty:
        wettest_m_idx = monthly_summary["Precipitation_mm"].idxmax()
        driest_m_idx = monthly_summary["Precipitation_mm"].idxmin()
        result["wettest_month"] = {
            "name": monthly_summary.loc[wettest_m_idx, "Month_Name"],
            "total_rainfall": float(monthly_summary.loc[wettest_m_idx, "Precipitation_mm"])
        }
        result["driest_month"] = {
            "name": monthly_summary.loc[driest_m_idx, "Month_Name"],
            "total_rainfall": float(monthly_summary.loc[driest_m_idx, "Precipitation_mm"])
        }

    return result


def generate_smart_insights(df: pd.DataFrame) -> List[Dict[str, str]]:
    """
    Derives natural language analytical insights from meteorological patterns,
    correlations, and anomalies.
    """
    insights: List[Dict[str, str]] = []
    stats = calculate_weather_stats(df)
    monthly = calculate_monthly_analysis(df)

    # 1. Hottest Day Insight
    if "hottest_day" in stats:
        hd = stats["hottest_day"]
        insights.append({
            "category": "Temperature Record",
            "icon": "🔥",
            "headline": f"Peak Heat Recorded on {hd['date']}",
            "text": f"The hottest recorded day reached a scorching {hd['temp']}°C ({hd['condition']})."
        })

    # 2. Coldest Day Insight
    if "coldest_day" in stats:
        cd = stats["coldest_day"]
        insights.append({
            "category": "Temperature Record",
            "icon": "❄️",
            "headline": f"Lowest Temperature on {cd['date']}",
            "text": f"The coldest day on record dropped to {cd['temp']}°C ({cd['condition']})."
        })

    # 3. Monthly Extreme Insights
    if "hottest_month" in monthly and "coldest_month" in monthly:
        hm = monthly["hottest_month"]
        cm = monthly["coldest_month"]
        insights.append({
            "category": "Seasonal Extremes",
            "icon": "🗓️",
            "headline": f"Warmest & Coldest Months",
            "text": f"{hm['name']} was the warmest month averaging {hm['avg_temp']}°C, whereas {cm['name']} experienced the lowest monthly average at {cm['avg_temp']}°C."
        })

    # 4. Rainiest Period Insight
    if "wettest_month" in monthly and "rainiest_day" in stats:
        wm = monthly["wettest_month"]
        rd = stats["rainiest_day"]
        insights.append({
            "category": "Precipitation Pattern",
            "icon": "🌧️",
            "headline": f"Monsoon Peak & Rainiest Day",
            "text": f"The month with the highest rainfall was {wm['name']} with {wm['total_rainfall']} mm total precipitation. The single rainiest day was {rd['date']} with {rd['rainfall']} mm."
        })

    # 5. Rainy Days Proportion
    if "rainy_days_count" in stats:
        insights.append({
            "category": "Precipitation Frequency",
            "icon": "☔",
            "headline": f"Rainfall Frequency ({stats['rainy_days_pct']}% of Days)",
            "text": f"Precipitation was recorded on {stats['rainy_days_count']} days, accumulating a total of {stats['total_precipitation']} mm."
        })

    # 6. Temperature & Humidity Correlation Insight
    if "Temperature_C" in df.columns and "Humidity_pct" in df.columns:
        corr = df["Temperature_C"].corr(df["Humidity_pct"])
        if not np.isnan(corr):
            strength = "strong" if abs(corr) >= 0.6 else "moderate" if abs(corr) >= 0.3 else "weak"
            direction = "negative" if corr < 0 else "positive"
            explanation = (
                "Warmer temperatures correspond with drier air."
                if corr < 0 else
                "Higher temperatures coincide with higher moisture levels."
            )
            insights.append({
                "category": "Correlation Dynamic",
                "icon": "🔄",
                "headline": f"{strength.capitalize()} {direction} Temp-Humidity Correlation (r = {corr:.2f})",
                "text": f"Humidity and temperature exhibit a {strength} {direction} correlation (Pearson r = {corr:.2f}). {explanation}"
            })

    # 7. Weather Condition Dominance
    if "Weather_Condition" in df.columns and not df["Weather_Condition"].empty:
        cond_counts = df["Weather_Condition"].value_counts()
        top_cond = cond_counts.index[0]
        top_count = cond_counts.iloc[0]
        top_pct = (top_count / len(df)) * 100
        insights.append({
            "category": "Predominant Sky Condition",
            "icon": "☀️",
            "headline": f"{top_cond} Dominates the Climate",
            "text": f"The most prevalent weather condition was '{top_cond}', occurring on {top_count} days ({top_pct:.1f}% of all recorded days)."
        })

    return insights


# =====================================================================
# Visualization Functions (Matplotlib & Seaborn)
# =====================================================================

def plot_temperature_trend(df: pd.DataFrame) -> plt.Figure:
    """Plots temperature trends over time with rolling average."""
    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=100)
    
    if "Date" in df.columns and "Temperature_C" in df.columns:
        ax.plot(df["Date"], df["Temperature_C"], color="#E76F51", alpha=0.45, linewidth=1.2, label="Daily Temperature (°C)")
        
        # 30-day moving average
        if len(df) >= 30:
            rolling_avg = df["Temperature_C"].rolling(window=30, center=True).mean()
            ax.plot(df["Date"], rolling_avg, color="#9D0208", linewidth=2.5, label="30-Day Moving Average")
        
        ax.set_title("Historical Temperature Trends Over Time", pad=12)
        ax.set_xlabel("Date")
        ax.set_ylabel("Temperature (°C)")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
        fig.autofmt_xdate()
        ax.legend(loc="upper right", frameon=True, facecolor="white", edgecolor="#E0E0E0")
        ax.grid(True, linestyle="--", alpha=0.6)
    return fig


def plot_monthly_avg_temp(monthly_df: pd.DataFrame) -> plt.Figure:
    """Plots bar chart of monthly average temperatures."""
    fig, ax = plt.subplots(figsize=(9, 4.2), dpi=100)
    
    if "Month_Name" in monthly_df.columns and "Temperature_C" in monthly_df.columns:
        norm = plt.Normalize(monthly_df["Temperature_C"].min(), monthly_df["Temperature_C"].max())
        colors = plt.cm.YlOrRd(norm(monthly_df["Temperature_C"]))
        
        bars = ax.bar(monthly_df["Month_Name"], monthly_df["Temperature_C"], color=colors, edgecolor="#B23A22", linewidth=0.8, width=0.65)
        
        # Value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f"{height:.1f}°C",
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 4), textcoords="offset points",
                        ha="center", va="bottom", fontsize=9, fontweight="bold")

        ax.set_title("Monthly Average Temperature Profile", pad=12)
        ax.set_xlabel("Month")
        ax.set_ylabel("Average Temperature (°C)")
        ax.set_ylim(0, max(monthly_df["Temperature_C"].max() * 1.15, 30))
        ax.grid(axis="y", linestyle="--", alpha=0.6)
    return fig


def plot_monthly_rainfall(monthly_df: pd.DataFrame) -> plt.Figure:
    """Plots bar chart for monthly cumulative rainfall."""
    fig, ax = plt.subplots(figsize=(9, 4.2), dpi=100)
    
    if "Month_Name" in monthly_df.columns and "Precipitation_mm" in monthly_df.columns:
        bars = ax.bar(monthly_df["Month_Name"], monthly_df["Precipitation_mm"], color="#3A86FF", edgecolor="#0056B3", linewidth=0.8, width=0.65)
        
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.annotate(f"{height:.0f}mm",
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 4), textcoords="offset points",
                            ha="center", va="bottom", fontsize=9, fontweight="bold")

        ax.set_title("Monthly Total Rainfall (Precipitation)", pad=12)
        ax.set_xlabel("Month")
        ax.set_ylabel("Total Rainfall (mm)")
        ax.set_ylim(0, max(monthly_df["Precipitation_mm"].max() * 1.15, 10))
        ax.grid(axis="y", linestyle="--", alpha=0.6)
    return fig


def plot_humidity_trend(df: pd.DataFrame) -> plt.Figure:
    """Plots daily humidity fluctuations and smoothing curve."""
    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=100)
    
    if "Date" in df.columns and "Humidity_pct" in df.columns:
        ax.plot(df["Date"], df["Humidity_pct"], color="#00B4D8", alpha=0.45, linewidth=1.2, label="Daily Humidity (%)")
        
        if len(df) >= 30:
            rolling_hum = df["Humidity_pct"].rolling(window=30, center=True).mean()
            ax.plot(df["Date"], rolling_hum, color="#0077B6", linewidth=2.5, label="30-Day Trend")
            
        ax.set_title("Humidity Variation & Trends Over Time", pad=12)
        ax.set_xlabel("Date")
        ax.set_ylabel("Relative Humidity (%)")
        ax.set_ylim(0, 105)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
        fig.autofmt_xdate()
        ax.legend(loc="lower right", frameon=True, facecolor="white", edgecolor="#E0E0E0")
        ax.grid(True, linestyle="--", alpha=0.6)
    return fig


def plot_temp_distribution(df: pd.DataFrame) -> plt.Figure:
    """Histogram with KDE distribution curve for temperature."""
    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=100)
    
    if "Temperature_C" in df.columns:
        sns.histplot(df["Temperature_C"], kde=True, color="#E76F51", bins=24, ax=ax, edgecolor="#8B2500")
        mean_val = df["Temperature_C"].mean()
        median_val = df["Temperature_C"].median()
        ax.axvline(mean_val, color="#D90429", linestyle="--", linewidth=1.8, label=f"Mean ({mean_val:.1f}°C)")
        ax.axvline(median_val, color="#2B9348", linestyle=":", linewidth=1.8, label=f"Median ({median_val:.1f}°C)")
        
        ax.set_title("Temperature Frequency Distribution & Density", pad=12)
        ax.set_xlabel("Temperature (°C)")
        ax.set_ylabel("Day Count")
        ax.legend(loc="upper right", frameon=True, facecolor="white", edgecolor="#E0E0E0")
        ax.grid(True, linestyle="--", alpha=0.6)
    return fig


def plot_temp_vs_humidity(df: pd.DataFrame) -> plt.Figure:
    """Scatter plot between temperature and humidity with trendline."""
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=100)
    
    if "Temperature_C" in df.columns and "Humidity_pct" in df.columns:
        sns.regplot(
            data=df,
            x="Temperature_C",
            y="Humidity_pct",
            scatter_kws={"alpha": 0.45, "color": "#2A9D8F", "s": 25},
            line_kws={"color": "#E63946", "linewidth": 2.2, "label": "Linear Fit Trend"},
            ax=ax
        )
        corr = df["Temperature_C"].corr(df["Humidity_pct"])
        ax.set_title(f"Temperature vs. Humidity Correlation (r = {corr:.2f})", pad=12)
        ax.set_xlabel("Temperature (°C)")
        ax.set_ylabel("Humidity (%)")
        ax.legend(loc="upper right", frameon=True, facecolor="white", edgecolor="#E0E0E0")
        ax.grid(True, linestyle="--", alpha=0.6)
    return fig


def plot_correlation_heatmap(df: pd.DataFrame) -> plt.Figure:
    """Heatmap showing Pearson correlations across all numeric weather variables."""
    fig, ax = plt.subplots(figsize=(7, 5.2), dpi=100)
    
    numeric_cols = [c for c in ["Temperature_C", "Humidity_pct", "Precipitation_mm", "WindSpeed_kmh", "Pressure_hPa"] if c in df.columns]
    if len(numeric_cols) >= 2:
        corr_matrix = df[numeric_cols].corr()
        
        # Pretty labels
        labels = [c.replace("_", " ") for c in numeric_cols]
        
        sns.heatmap(
            corr_matrix,
            annot=True,
            fmt=".2f",
            cmap="coolwarm",
            vmin=-1,
            vmax=1,
            square=True,
            linewidths=1.2,
            cbar_kws={"shrink": 0.8, "label": "Pearson Correlation (r)"},
            xticklabels=labels,
            yticklabels=labels,
            ax=ax
        )
        ax.set_title("Correlation Heatmap: Weather Variables", pad=14)
    return fig


def plot_weather_condition_pie(df: pd.DataFrame) -> plt.Figure:
    """Donut/Pie chart showing distribution of weather conditions."""
    fig, ax = plt.subplots(figsize=(7, 4.8), dpi=100)
    
    if "Weather_Condition" in df.columns and not df["Weather_Condition"].empty:
        cond_counts = df["Weather_Condition"].value_counts()
        colors = sns.color_palette("Set2", len(cond_counts))
        
        wedges, texts, autotexts = ax.pie(
            cond_counts,
            labels=cond_counts.index,
            autopct="%1.1f%%",
            pctdistance=0.75,
            startangle=140,
            colors=colors,
            wedgeprops={"edgecolor": "white", "linewidth": 1.5, "width": 0.55}  # Donut hole
        )
        for autotext in autotexts:
            autotext.set_fontsize(9)
            autotext.set_fontweight("bold")
            
        ax.set_title("Weather Condition Breakdown", pad=12)
    return fig
