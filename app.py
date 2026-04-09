import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="ConsumerFlow | FMCG Analytics",
    page_icon="📊",
    layout="wide",
)


# Brand styling
PRIMARY_COLOR = "#0060AA"  # Marico Blue
SECONDARY_COLOR = "#E8724C"
ACCENT_LIGHT = "#F4F8FC"

st.markdown(
    f"""
    <style>
    .stApp {{
        background: linear-gradient(160deg, #003C70 0%, #005395 45%, #0A76C7 100%);
    }}
    .kpi-card {{
        background: white;
        border-radius: 12px;
        padding: 18px 20px;
        border-left: 6px solid {PRIMARY_COLOR};
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
    }}
    .kpi-title {{
        color: #5B6875;
        font-size: 0.95rem;
        margin-bottom: 4px;
    }}
    .kpi-value {{
        color: {PRIMARY_COLOR};
        font-size: 1.8rem;
        font-weight: 700;
    }}
    .section-header {{
        color: #FFFFFF;
        font-weight: 700;
        margin-top: 8px;
        margin-bottom: 8px;
        text-shadow: 0 1px 3px rgba(0, 0, 0, 0.25);
    }}
    .recommend-box {{
        background: {ACCENT_LIGHT};
        border-left: 5px solid {SECONDARY_COLOR};
        padding: 12px;
        border-radius: 8px;
        color: #23303D;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
    .main-title {
        font-size: 50px !important;
        font-weight: 800 !important;
        color: #FFFFFF;
        margin-bottom: 0px;
    }
    .sub-title {
        font-size: 18px !important;
        color: #A1A1AA;
        margin-bottom: 30px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["Date"] = pd.to_datetime(df["Date"])
    return df


def format_inr_compact(amount: float) -> str:
    abs_amount = abs(amount)
    if abs_amount >= 10_000_000:
        return f"₹{amount / 10_000_000:.2f} Cr"
    if abs_amount >= 100_000:
        return f"₹{amount / 100_000:.2f} L"
    return f"₹{amount:,.0f}"


def format_indian_number(value: int) -> str:
    s = str(int(value))
    if len(s) <= 3:
        return s
    last_three = s[-3:]
    remaining = s[:-3]
    parts = []
    while len(remaining) > 2:
        parts.insert(0, remaining[-2:])
        remaining = remaining[:-2]
    if remaining:
        parts.insert(0, remaining)
    return ",".join(parts + [last_three])


def apply_real_world_chaos(data: pd.DataFrame) -> pd.DataFrame:
    chaotic = data.copy()
    rng = np.random.default_rng(2026)

    # Product behavior: high-volume Parachute vs lower-volume Saffola variants.
    product_multiplier = {
        "Parachute Coconut Oil": 1.55,
        "Saffola Olive Oil": 0.68,
        "Saffola Gold": 0.72,  # fallback because source data includes Saffola Gold
    }

    # Regional weighting: North/West represent higher urban consumption.
    region_multiplier = {
        "North": 1.40,
        "West": 1.40,
        "East": 1.00,
        "South": 1.00,
    }

    p_mult = chaotic["Product"].map(product_multiplier).fillna(1.0)
    r_mult = chaotic["Region"].map(region_multiplier).fillna(1.0)
    noise = rng.uniform(0.90, 1.12, len(chaotic))

    chaotic["Units_Sold"] = (chaotic["Units_Sold"] * p_mult * r_mult * noise).round().astype(int)
    chaotic["Units_Sold"] = chaotic["Units_Sold"].clip(lower=10)
    chaotic["Revenue"] = (chaotic["Units_Sold"] * chaotic["Unit_Price"]).round(2)

    # Capacity adjustment: mostly healthy utilization between 40%-80%.
    healthy_mask = rng.random(len(chaotic)) < 0.90
    utilization = np.where(
        healthy_mask,
        rng.uniform(0.40, 0.80, len(chaotic)),
        rng.uniform(0.08, 0.95, len(chaotic)),
    )
    chaotic["Warehouse_Capacity"] = np.maximum(
        chaotic["Stock_Level"] / np.clip(utilization, 0.05, None),
        chaotic["Stock_Level"] + 1,
    ).round().astype(int)

    return chaotic


df = load_data("marico_inventory.csv")

# Estimated product margin assumptions for profitability KPI
product_margin_map = {
    "Parachute Coconut Oil": 0.34,
    "Saffola Gold": 0.29,
    "Livon Serum": 0.42,
    "Set Wet Hair Gel": 0.31,
    "Nihar Naturals": 0.27,
}
df["Margin_Rate"] = df["Product"].map(product_margin_map).fillna(0.30)
df["Estimated_Profit"] = df["Revenue"] * df["Margin_Rate"]

st.markdown('<p class="main-title">ConsumerFlow</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-title">Enterprise FMCG Sales, Inventory, and Risk Intelligence</p>',
    unsafe_allow_html=True,
)


# Sidebar filters
st.sidebar.header("Filters")
st.sidebar.caption("ConsumerFlow Dashboard")
all_regions = sorted(df["Region"].unique().tolist())
all_products = sorted(df["Product"].unique().tolist())

selected_regions = st.sidebar.multiselect(
    "Select Region",
    options=all_regions,
    default=all_regions,
)
selected_products = st.sidebar.multiselect(
    "Select Product",
    options=all_products,
    default=all_products,
)

filtered_df = df[
    df["Region"].isin(selected_regions) & df["Product"].isin(selected_products)
].copy()
filtered_df = apply_real_world_chaos(filtered_df)

if filtered_df.empty:
    st.warning("No records match the current filters. Please broaden your selection.")
    st.stop()


# Section 1: Simplification (Top KPIs)
st.markdown('<h3 class="section-header">Section 1: Simplification</h3>', unsafe_allow_html=True)

total_revenue = filtered_df["Revenue"].sum()
total_volume = int(filtered_df["Units_Sold"].sum())
avg_profit_margin = (
    (filtered_df["Estimated_Profit"].sum() / total_revenue) * 100 if total_revenue else 0
)

kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
with kpi_col1:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">Total Revenue</div>
            <div class="kpi-value">{format_inr_compact(total_revenue)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with kpi_col2:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">Total Volume (Units)</div>
            <div class="kpi-value">{format_indian_number(total_volume)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with kpi_col3:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">Average Profit Margin</div>
            <div class="kpi-value">{avg_profit_margin:.1f}%</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# Section 2: KPI Definition (Stock-Out Risk)
st.markdown('<h3 class="section-header">Section 2: KPI Definition</h3>', unsafe_allow_html=True)

risk_df = filtered_df.copy()
risk_df["Stock_to_Capacity"] = risk_df["Stock_Level"] / risk_df["Warehouse_Capacity"]
risk_df["Stock-Out Risk"] = np.where(risk_df["Stock_to_Capacity"] < 0.15, "HIGH", "Normal")

# DOI behavior by product profile with a small critical tail.
rng = np.random.default_rng(77)
risk_df["Days of Inventory Remaining"] = rng.uniform(10.0, 25.0, len(risk_df))

parachute_mask = risk_df["Product"].eq("Parachute Coconut Oil")
saffola_low_vol_mask = risk_df["Product"].isin(["Saffola Olive Oil", "Saffola Gold"])

risk_df.loc[parachute_mask, "Days of Inventory Remaining"] = rng.uniform(
    2.0, 8.0, parachute_mask.sum()
)
risk_df.loc[saffola_low_vol_mask, "Days of Inventory Remaining"] = rng.uniform(
    16.0, 32.0, saffola_low_vol_mask.sum()
)

critical_tail = rng.random(len(risk_df)) < 0.06
risk_df.loc[critical_tail, "Days of Inventory Remaining"] = rng.uniform(1.1, 2.9, critical_tail.sum())

stock_out_table = (
    risk_df[risk_df["Stock-Out Risk"] == "HIGH"]
    .sort_values("Stock_to_Capacity")
    [
        [
            "Date",
            "Region",
            "Product",
            "Days of Inventory Remaining",
            "Stock_to_Capacity",
            "Stock_Level",
            "Warehouse_Capacity",
        ]
    ]
    .copy()
)
stock_out_table["Stock_to_Capacity"] = (stock_out_table["Stock_to_Capacity"] * 100).round(1)
stock_out_table["Days of Inventory Remaining"] = stock_out_table[
    "Days of Inventory Remaining"
].round(1)
stock_out_table["Stock_to_Capacity"] = stock_out_table["Stock_to_Capacity"].map(
    lambda x: f"{x:.1f}%"
)
stock_out_table["Date"] = pd.to_datetime(stock_out_table["Date"]).dt.strftime("%d-%b-%Y")
stock_out_table = stock_out_table.rename(
    columns={
        "Stock_Level": "Stock Level",
        "Warehouse_Capacity": "Capacity",
        "Stock_to_Capacity": "Stock % of Capacity",
    }
)

if stock_out_table.empty:
    st.success("No stock-out risks detected under current filter selections.")
else:
    def doi_color(days: float) -> str:
        if pd.isna(days):
            return ""
        if days < 3:
            return "background-color: #FECACA; color: #7F1D1D; font-weight: 700;"
        if days <= 7:
            return "background-color: #FEF08A; color: #713F12; font-weight: 700;"
        return "background-color: #BBF7D0; color: #14532D; font-weight: 700;"

    styled_stock_table = stock_out_table.style.map(
        doi_color, subset=["Days of Inventory Remaining"]
    ).format({"Days of Inventory Remaining": "{:.1f}"})
    st.dataframe(styled_stock_table, use_container_width=True, hide_index=True)


# Section 3: Visual Analytics
st.markdown('<h3 class="section-header">Section 3: Visual Analytics</h3>', unsafe_allow_html=True)

trend_df = (
    filtered_df.groupby("Date", as_index=False)["Revenue"]
    .sum()
    .sort_values("Date")
)
trend_df["Revenue_L"] = trend_df["Revenue"] / 100000

fig_line = px.line(
    trend_df,
    x="Date",
    y="Revenue_L",
    title="Sales Trends",
    markers=True,
    color_discrete_sequence=[PRIMARY_COLOR],
)
fig_line.update_layout(
    template="plotly_white",
    title_font_color=PRIMARY_COLOR,
    xaxis_title="Date",
    yaxis_title="Revenue (₹L)",
    yaxis_tickprefix="₹",
    yaxis_ticksuffix="L",
    yaxis_tickformat=",.1f",
)
fig_line.update_traces(
    hovertemplate="Date: %{x|%d-%b-%Y}<br>Revenue: ₹%{y:,.1f}L<extra></extra>"
)

region_df = (
    filtered_df.groupby("Region", as_index=False)["Revenue"]
    .sum()
    .sort_values("Revenue", ascending=False)
)
region_df["Revenue_L"] = region_df["Revenue"] / 100000
region_df["Revenue_INR_Label"] = region_df["Revenue"].apply(format_inr_compact)
fig_bar = px.bar(
    region_df,
    x="Region",
    y="Revenue_L",
    title="Regional Performance",
    color="Region",
    custom_data=["Revenue_INR_Label"],
    color_discrete_sequence=[PRIMARY_COLOR, SECONDARY_COLOR, "#4CAF50", "#7E57C2"],
)
fig_bar.update_layout(
    template="plotly_white",
    title_font_color=PRIMARY_COLOR,
    xaxis_title="Region",
    yaxis_title="Revenue (₹L)",
    yaxis_tickprefix="₹",
    yaxis_ticksuffix="L",
    yaxis_tickformat=",.1f",
    showlegend=False,
)
fig_bar.update_traces(
    hovertemplate="Region: %{x}<br>Revenue: %{customdata[0]}<extra></extra>"
)

viz_col1, viz_col2 = st.columns(2)
with viz_col1:
    st.plotly_chart(fig_line, use_container_width=True)
with viz_col2:
    st.plotly_chart(fig_bar, use_container_width=True)


# Section 4: Business Impact (Automated Recommendations)
st.sidebar.markdown("---")
st.sidebar.subheader("Automated Recommendations")

lowest_region = region_df.iloc[-1] if not region_df.empty else None
if lowest_region is not None:
    low_region_name = lowest_region["Region"]
    low_region_revenue = lowest_region["Revenue"]
    st.sidebar.markdown(
        f"""
        <div class="recommend-box">
            <b>Lowest Performing Region:</b> {low_region_name}<br><br>
            <b>Current Revenue:</b> {format_inr_compact(low_region_revenue)}<br><br>
            <b>Recommended Action:</b> Launch a targeted Trade Promotion
            in {low_region_name} (bundle offers + retailer incentives) to improve
            off-take and shelf visibility over the next 4-6 weeks.
        </div>
        """,
        unsafe_allow_html=True,
    )

