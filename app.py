import streamlit as st
import pandas as pd
import altair as alt
 
# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="Home Energy Use Dashboard",
    page_icon="⚡",
    layout="wide",                      # use the full browser width
    initial_sidebar_state="expanded",
)
 
LABEL_COLOR = "#9aa0a6"   # mid-gray text: readable in both light and dark mode
 
 
# ---------- LOAD DATA ----------
@st.cache_data
def load_data():
    df = pd.read_csv("data/home_energy_use.csv")
    # month is stored as text like "2025-01"; convert it to a real date
    df["month"] = pd.to_datetime(df["month"], format="%Y-%m")
    return df
 
df = load_data()
 
 
# ---------- SIDEBAR FILTERS ----------
with st.sidebar:
    st.title("Home Energy Use Dashboard")
    region_choice = st.multiselect("Region",
        options=sorted(df["region"].unique()),
        default=sorted(df["region"].unique()))
    heating_type = st.multiselect("Heating type",
        options=sorted(df["heating_type"].unique()),
        default=sorted(df["heating_type"].unique()))
    # st.slider needs plain Python datetimes, not pandas Timestamps
    first = df["month"].min().to_pydatetime()
    last_m = df["month"].max().to_pydatetime()
    month_range = st.slider("Month range", min_value=first, max_value=last_m,
                            value=(first, last_m), format="MMM YYYY")
    theme = st.selectbox("Color theme", ["blues", "greens", "oranges", "purples"])
 
# keep only rows that match every filter
mask = (df["region"].isin(region_choice)
        & df["heating_type"].isin(heating_type)
        & df["month"].between(month_range[0], month_range[1]))
filtered = df[mask]
 
if filtered.empty:
    st.warning("No homes match these filters. Select at least one region "
               "and one heating type.")
    st.stop()   # stop here so the charts below don't crash on an empty table
 
 
# ---------- HEADER ----------
st.title("⚡ Home Energy Use Dashboard")
st.caption("Monthly electricity use for 200 Colorado homes in 2025 (synthetic data). "
           "The dataset has no blank values, so no rows were dropped or filled.")
 
 
# ---------- KPIs ----------
k1, k2, k3 = st.columns(3)
k1.metric("Total kWh", f"{filtered['kwh_used'].sum():,.0f}")
# each row is one home in one month, so the row average = kWh per home per month
k2.metric("Avg kWh per home / month", f"{filtered['kwh_used'].mean():,.0f}")
peak = filtered.groupby("month")["kwh_used"].sum().idxmax()
k3.metric("Peak month", peak.strftime("%B %Y"))
 
 
q1_left, q1_right = st.columns(2, gap="medium")
 
with q1_left:
    st.subheader("Avg kWh per home by month and region")
    # mean (not sum) so regions with more homes don't look artificially high
    trend = filtered.groupby(["month", "region"], as_index=False)["kwh_used"].mean()
    line = alt.Chart(trend).mark_line(point=True).encode(
        x=alt.X("month:T", title="Month"),
        y=alt.Y("kwh_used:Q", title="Avg kWh per home", scale=alt.Scale(zero=False)),
        color=alt.Color("region:N", title="Region", scale=alt.Scale(scheme=theme)),
        tooltip=[alt.Tooltip("month:T", title="Month", format="%b %Y"),
                 alt.Tooltip("region:N", title="Region"),
                 alt.Tooltip("kwh_used:Q", title="Avg kWh per home", format=",.0f")],
    )
    st.altair_chart(line, width="stretch")
    st.caption("Each line is one region; each point is the average kWh used per home "
               "in that month. Hover a point for exact values.")
 
with q1_right:
    st.subheader("Electricity use vs. outdoor temperature")
    q1 = filtered.groupby("month", as_index=False)[["kwh_used", "avg_outdoor_temp_f"]].mean()
    points = alt.Chart(q1).mark_circle(size=120).encode(
        x=alt.X("avg_outdoor_temp_f:Q", title="Avg outdoor temperature (°F)",
                scale=alt.Scale(zero=False)),
        y=alt.Y("kwh_used:Q", title="Avg kWh per home", scale=alt.Scale(zero=False)),
        tooltip=[alt.Tooltip("month:T", title="Month", format="%B"),
                 alt.Tooltip("avg_outdoor_temp_f:Q", title="Temp (°F)", format=".1f"),
                 alt.Tooltip("kwh_used:Q", title="Avg kWh per home", format=",.0f")],
    )
    # month name next to each dot so the chart reads without hovering
    labels = points.mark_text(align="left", dx=8, color=LABEL_COLOR, size=14).encode(
        text=alt.Text("month:T", format="%b"))
    st.altair_chart(points + labels, width="stretch")
    st.caption("Each dot is one month: average outdoor temperature vs. average kWh "
               "used per home. Month names are printed beside each dot.")
 
 
# ---------- Q2 + Q3 (side by side) ----------
q2_col, q3_col = st.columns(2, gap="medium")
 
with q2_col:
    st.subheader("Avg kWh per home by region")
    q2 = filtered.groupby("region", as_index=False)["kwh_used"].mean()
    base = alt.Chart(q2).encode(
        x=alt.X("region:N", title="Region", sort="-y",    # tallest bar first
                axis=alt.Axis(labelAngle=0)),             # keep labels flat
        y=alt.Y("kwh_used:Q", title="Avg kWh per home / month"),  # bars start at 0
    )
    bars = base.mark_bar().encode(
        tooltip=[alt.Tooltip("region:N", title="Region"),
                 alt.Tooltip("kwh_used:Q", title="Avg kWh per home", format=",.0f")])
    # print each value on its bar so meaning isn't carried by bar height alone
    values = base.mark_text(dy=-8, color=LABEL_COLOR).encode(
        text=alt.Text("kwh_used:Q", format=",.0f"))
    st.altair_chart(bars + values, width="stretch")
    st.caption("Each bar shows the average monthly kWh used per home in that region "
               "for the selected months, sorted from highest to lowest.")
 
with q3_col:
    st.subheader("kWh by heating type")
    q3 = filtered.groupby("heating_type", as_index=False)["kwh_used"].mean()
    base = alt.Chart(q3).encode(
        x=alt.X("heating_type:N", title="Heating type", sort="-y",   # tallest bar first
                axis=alt.Axis(labelAngle=0)),                        # keep labels flat
        y=alt.Y("kwh_used:Q", title="Avg kWh per home / month"),  # bars start at 0
    )
    bars = base.mark_bar().encode(
        tooltip=[alt.Tooltip("heating_type:N", title="Heating type"),
                 alt.Tooltip("kwh_used:Q", title="Avg kWh per home", format=",.0f")])
    # print each value on its bar so meaning isn't carried by bar height alone
    values = base.mark_text(dy=-8, color=LABEL_COLOR).encode(
        text=alt.Text("kwh_used:Q", format=",.0f"))
    st.altair_chart(bars + values, width="stretch")
    st.caption("Each bar shows the average monthly kWh used per home for each heating type, "
               "sorted from highest to lowest.")
 
 
# ---------- Q4: SOLAR AND EVs ----------
st.subheader("Electricity pulled from the grid: solar and EV homes")
q4 = filtered.groupby(["has_solar", "has_ev"], as_index=False)[["kwh_used", "solar_kwh"]].mean()
# what a home pulls from the grid = what it uses minus what its own panels produce
q4["grid_kwh"] = q4["kwh_used"] - q4["solar_kwh"]
# one plain-text label per bar, so the groups are named in words, not by color alone
q4["group"] = "Solar: " + q4["has_solar"].astype(str) + " / EV: " + q4["has_ev"].astype(str)

base = alt.Chart(q4).encode(
    x=alt.X("group:N", title="Home group", sort="-y", axis=alt.Axis(labelAngle=0)),
    y=alt.Y("grid_kwh:Q", title="Avg kWh from the grid per home / month"),  # bars start at 0
)
bars = base.mark_bar().encode(
    tooltip=[alt.Tooltip("group:N", title="Group"),
             alt.Tooltip("kwh_used:Q", title="Avg kWh used", format=",.0f"),
             alt.Tooltip("solar_kwh:Q", title="Avg solar kWh produced", format=",.0f"),
             alt.Tooltip("grid_kwh:Q", title="Avg kWh from grid", format=",.0f")])
values = base.mark_text(dy=-8, color=LABEL_COLOR).encode(
    text=alt.Text("grid_kwh:Q", format=",.0f"))
st.altair_chart(bars + values, width="stretch")
st.caption("Each bar shows the average monthly electricity a home pulls from the grid "
           "(kWh used minus kWh its solar panels produced), for each solar/EV combination. "
           "Hover a bar to see total use and solar production.")
 
 
# ---------- INSIGHTS ----------
# Numbers are computed from the filtered data, so the takeaways update with the sidebar.
st.header("Key insights")

by_month = filtered.groupby("month")["kwh_used"].mean()   # avg kWh per home, by month
r = q2.set_index("region")["kwh_used"]                    # from the Q2 chart
h = q3.set_index("heating_type")["kwh_used"]              # from the Q3 chart
g = q4.set_index("group")["grid_kwh"]                     # from the Q4 chart

with st.container(border=True):
    # Q1: when is use highest?
    st.markdown(
        f"**Q1 (When):** Usage is highest in **{by_month.idxmax():%B}** "
        f"(~{by_month.max():,.0f} kWh per home) and lowest in **{by_month.idxmin():%B}** "
        f"(~{by_month.min():,.0f} kWh). It rises in both the coldest and hottest months, "
        "likely because of heating in winter and air conditioning in summer.")

    # Q2: which region? (needs at least 2 regions selected to compare)
    if len(r) > 1:
        st.markdown(
            f"**Q2 (Where):** **{r.idxmax()}** homes use the most electricity on average "
            f"(~{r.max():,.0f} kWh per month), while **{r.idxmin()}** homes use the least "
            f"(~{r.min():,.0f} kWh). In the full dataset the Front Range stays on top even "
            "when comparing only gas-heated homes, so heating type doesn't explain the gap.")
    else:
        st.markdown("**Q2 (Where):** Select at least two regions to compare them.")

    # Q3: which heating type? (needs at least 2 heating types selected)
    if len(h) > 1:
        pct_more = (h.max() / h.min() - 1) * 100
        st.markdown(
            f"**Q3 (Heating):** **{h.idxmax()}** homes use about **{pct_more:.0f}% more** "
            f"electricity than **{h.idxmin()}** homes (~{h.max():,.0f} vs. ~{h.min():,.0f} kWh "
            "per month), because homes that heat with electricity draw on the grid every winter.")
    else:
        st.markdown("**Q3 (Heating):** Select at least two heating types to compare them.")

    # Q4: solar and EVs (needs at least 2 home groups in the filtered data)
    if len(g) > 1:
        st.markdown(
            f"**Q4 (Solar & EVs):** **{g.idxmax()}** homes pull the most from the grid "
            f"(~{g.max():,.0f} kWh per month) and **{g.idxmin()}** homes the least "
            f"(~{g.min():,.0f} kWh). Solar has the biggest effect: homes with panels pull far "
            "less from the grid, even when they also charge an EV.")
    else:
        st.markdown("**Q4 (Solar & EVs):** Not enough home groups in the current filters to compare.")

st.caption("Insights are calculated from the current filters. "
           "The explanations describe the pattern across the full dataset.")