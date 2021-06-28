import streamlit as st
import pandas as pd
import altair as alt


@st.cache
def get_data():
    temp_df = pd.read_csv("processed_temp_df.csv")
    temp_df.location_date = pd.to_datetime(temp_df.location_date)
    return temp_df


st.write(
    "# Plotting Recorded Temperatures Overtime",
)
df = get_data()
cities = st.multiselect(
    "Choose Cities", list(df.name.unique()), ["Portland", "New York"]
)
aggregate_filter = st.checkbox("Average Cities")
from_date = st.date_input("From", df.location_date.min().date())
to_date = st.date_input("To", df.location_date.max().date())

if not cities:
    st.error("Please select at least one city.")
elif from_date > to_date:
    st.error("Please from date less than the to date.")
else:
    from_date_ts = pd.Timestamp(from_date)
    to_date_ts = pd.Timestamp(to_date)

    mask = (
        (df.location_date >= from_date_ts)
        & (df.name.isin(cities))
        & (df.location_date <= to_date_ts)
    )
    data = df.loc[mask]
    if not aggregate_filter:
        line = (
            alt.Chart(data)
            .mark_line(opacity=0.7)
            .encode(
                x=alt.X("location_date:T", title="Date"),
                y=alt.Y("temp_mean_c:Q", title="Temperature (Celcius)"),
                color="name",
            )
        )
        band = (
            alt.Chart(data)
            .mark_area(opacity=0.3)
            .encode(
                x=alt.X("location_date:T", title="Date"),
                y="temp_min_c:Q",
                y2="temp_max_c:Q",
                color="name",
            )
        )
    else:
        line = (
            alt.Chart(data)
            .mark_line(opacity=0.7)
            .encode(
                x=alt.X("location_date:T", title="Date"),
                y=alt.Y("mean(temp_mean_c):Q", title="Temperature (Celcius)"),
            )
        )
        band = (
            alt.Chart(data)
            .mark_area(opacity=0.3)
            .encode(
                x=alt.X("location_date:T", title="Date"),
                y="mean(temp_min_c):Q",
                y2="mean(temp_max_c):Q",
            )
        )

    lb = alt.layer(line, band)
    ch = (
        alt.Chart(data)
        .mark_rule(opacity=0.5)
        .encode(
            x=alt.X("location_date:T", title="Date"),
            color=alt.condition(
                "datum.filled", alt.ColorValue("red"), alt.ColorValue(None)
            ),
        )
    )
    chart = lb + ch
    chart.title = "Average Temperatures Recorded"

    st.altair_chart(chart, use_container_width=True)
    st.write(
        "Days with missing recordings are shown in red. We fill in the missing values based on an average between the previous and next recording for that station."
    )
    st.write(
        "#### Missing Temperatures Recordings",
        df.loc[(df.filled) & mask].sort_values(by="location_date"),
    )

# Streamlit widgets automatically run the script from top to bottom. Since
# this button is not connected to any other logic, it just causes a plain
# rerun.
st.button("Re-run")
