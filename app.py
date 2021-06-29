import streamlit as st
import pandas as pd
import altair as alt
import numpy as np

pd.set_option("display.precision", 2)
pd.set_option("display.precision", 2)


@st.cache
def get_processed_temp_data():
    temp_df = pd.read_csv("processed_temp_df.csv")
    temp_df.location_date = pd.to_datetime(temp_df.location_date)
    return temp_df


@st.cache
def get_daily_weighted_temperatures():
    df = pd.read_csv("daily_weighted_temperatures.csv")
    df.location_date = pd.to_datetime(df.location_date)
    return df


def weighted_mean_function(column="temp_mean_c"):
    def weighted_mean(rows):
        return (rows.population_weight * rows[column]).sum() / len(
            rows.location_date.unique()
        )

    return weighted_mean


st.write(
    "# Plotting Recorded Temperatures Overtime",
)
df = get_processed_temp_data()
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
                tooltip=[
                    alt.Tooltip("location_date:T"),
                    alt.Tooltip("temp_mean_c:Q", format=".2f"),
                    alt.Tooltip("temp_min_c:Q", format=".2f"),
                    alt.Tooltip("temp_max_c:Q", format=".2f"),
                ],
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
                tooltip=[
                    alt.Tooltip("location_date:T"),
                    alt.Tooltip("temp_mean_c:Q", format=".2f"),
                    alt.Tooltip("temp_min_c:Q", format=".2f"),
                    alt.Tooltip("temp_max_c:Q", format=".2f"),
                ],
            )
        )
    else:
        line = (
            alt.Chart(data)
            .mark_line(opacity=0.7)
            .encode(
                x=alt.X("location_date:T", title="Date"),
                y=alt.Y("mean(temp_mean_c):Q", title="Temperature (Celcius)"),
                tooltip=[
                    alt.Tooltip("location_date:T"),
                    alt.Tooltip("temp_mean_c:Q", format=".2f"),
                    alt.Tooltip("temp_min_c:Q", format=".2f"),
                    alt.Tooltip("temp_max_c:Q", format=".2f"),
                ],
            )
        )
        band = (
            alt.Chart(data)
            .mark_area(opacity=0.3)
            .encode(
                x=alt.X("location_date:T", title="Date"),
                y="mean(temp_min_c):Q",
                y2="mean(temp_max_c):Q",
                tooltip=[
                    alt.Tooltip("location_date:T"),
                    alt.Tooltip("temp_mean_c:Q", format=".2f"),
                    alt.Tooltip("temp_min_c:Q", format=".2f"),
                    alt.Tooltip("temp_max_c:Q", format=".2f"),
                ],
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
    # scales = alt.selection_interval(bind="scales")
    chart = lb + ch  # .add_selection(scales)
    chart.title = "Average Temperatures Recorded (unweighted)"

    st.altair_chart(chart, use_container_width=True)
    st.write(
        "Days with missing recordings are shown in red. We fill in the missing values based on an average between the previous and next recording for that station. We average recordings for stations in the same city - this is the case for both Portland and Washington DC."
    )
    st.write(
        "#### Missing Temperatures Recordings",
        df.loc[(df.filled) & mask][
            [
                "location_date",
                "name",
                "station_code",
                "temp_min_c",
                "temp_mean_c",
                "temp_max_c",
            ]
        ].sort_values(by="location_date"),
    )

st.write("## Population weighted temperatures recorded")
daily_weighted_data = get_daily_weighted_temperatures().copy()
mask = (daily_weighted_data.location_date >= from_date_ts) & (
    daily_weighted_data.location_date <= to_date_ts
)
data = daily_weighted_data[mask]
line = (
    alt.Chart(data)
    .mark_line(opacity=0.7)
    .encode(
        x=alt.X("location_date:T", title="Date"),
        y=alt.Y(
            "weighted_mean_temp:Q", title="Weighted Average Temperatures (Celcius)"
        ),
        tooltip=[
            alt.Tooltip("location_date:T"),
            alt.Tooltip("weighted_mean_temp:Q", format=".2f"),
            alt.Tooltip("weighted_min_temp:Q", format=".2f"),
            alt.Tooltip("weighted_max_temp:Q", format=".2f"),
        ],
    )
)
band = (
    alt.Chart(data)
    .mark_area(opacity=0.3)
    .encode(
        x=alt.X("location_date:T", title="Date"),
        y="weighted_min_temp:Q",
        y2="weighted_max_temp:Q",
        tooltip=[
            alt.Tooltip("location_date:T"),
            alt.Tooltip("weighted_mean_temp:Q", format=".2f"),
            alt.Tooltip("weighted_min_temp:Q", format=".2f"),
            alt.Tooltip("weighted_max_temp:Q", format=".2f"),
        ],
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
chart.title = "Average Temperatures Recorded Weighted by Population"
st.altair_chart(chart, use_container_width=True)
st.write(
    "Here we weight daily temperatures (min/max/mean) recorded by the population of the cities in which they are recorded, to obtain a single timeseries."
)

st.write("### Population data")
pop_df = df.groupby("name").first().reset_index()
pop_chart = (
    alt.Chart(pop_df)
    .mark_circle()
    .encode(
        alt.X("Lon:Q", scale=alt.Scale(zero=False)),
        alt.Y("Lat:Q", scale=alt.Scale(zero=False)),
        color=alt.Color("name:N", legend=None),
        tooltip="name:N",
        size="population",
    )
)
st.altair_chart(pop_chart, use_container_width=True)


st.write(
    "## Plotting Monthly Population Weighted Mean, Min and Max Temperatures",
)
data = daily_weighted_data.copy()
mean_df = data.groupby(pd.Grouper(key="location_date", freq="1M")).mean().reset_index()
mean_df["date_string"] = (
    mean_df.location_date.dt.month_name()
    + " "
    + mean_df.location_date.dt.year.apply(str)
)

if from_date > to_date:
    st.error("Please from date less than the to date.")
else:

    mask_agg = (mean_df.location_date >= from_date_ts) & (
        mean_df.location_date <= to_date_ts
    )
    agg_data = mean_df.loc[mask_agg]
    line_agg = (
        alt.Chart(agg_data)
        .mark_line(opacity=0.7)
        .encode(
            x=alt.X("location_date:T", title="Date"),
            y=alt.Y(
                "weighted_mean_temp:Q",
                title="Weighted Mean Temperature (Pop * Celsius))",
            ),
            tooltip=[
                "date_string",
                alt.Tooltip("weighted_mean_temp:Q", format=".2f"),
                alt.Tooltip("weighted_min_temp:Q", format=".2f"),
                alt.Tooltip("weighted_max_temp:Q", format=".2f"),
            ],
        )
    )
    band_agg = (
        alt.Chart(agg_data)
        .mark_area(opacity=0.3)
        .encode(
            x=alt.X("location_date:T", title="Date"),
            y="weighted_min_temp:Q",
            y2="weighted_max_temp:Q",
            tooltip=[
                "date_string",
                alt.Tooltip("weighted_mean_temp:Q", format=".2f"),
                alt.Tooltip("weighted_min_temp:Q", format=".2f"),
                alt.Tooltip("weighted_max_temp:Q", format=".2f"),
            ],
        )
    )

    lb_agg = alt.layer(line_agg, band_agg)

    lb_agg.title = "Population Weighted Monthly Temperatures"

    st.altair_chart(lb_agg, use_container_width=True)

    st.write(
        "Overlay your cursor to get specific temperature information for a given month/year."
    )

# Season based
seasons = st.multiselect(
    "Filter on specific seasons",
    [
        "Winter",
        "Summer",
        "Autumn",
        "Spring",
    ],
    [],
)
if not seasons:
    seasons = ["Winter", "Spring", "Summer", "Autumn"]

data["season_name"] = data.location_date.dt.month_name().map(
    {
        "December": "Winter",
        "January": "Winter",
        "February": "Winter",
        "March": "Spring",
        "April": "Spring",
        "May": "Spring",
        "June": "Summer",
        "July": "Summer",
        "August": "Summer",
        "September": "Autumn",
        "October": "Autumn",
        "November": "Autumn",
    }
)
data["year"] = data["location_date"].apply(lambda x: x.year)
data["month"] = data["location_date"].apply(lambda x: x.month)
data["month"] = np.where(data["month"] == 12, 0, data["month"])
data["season"] = data["month"] // 3
data["name_year_cumulative"] = data["year"] - data["year"].min()
data["cumulative_season"] = np.where(
    data["month"] == 0,
    data["season"] + (data["name_year_cumulative"] + 1) * 4,
    data["season"] + data["name_year_cumulative"] * 4,
)
season_weighted_data = (
    data.groupby("cumulative_season")
    .agg(
        {
            "weighted_mean_temp": "mean",
            "weighted_min_temp": "mean",
            "weighted_max_temp": "mean",
            "season_name": "first",
            "year": "first",
        }
    )
    .reset_index()
)
season_weighted_data = season_weighted_data[
    season_weighted_data.season_name.isin(seasons)
]
season_weighted_data["season_name_yr"] = (
    season_weighted_data["season_name"] + " " + season_weighted_data["year"].apply(str)
)
if len(seasons) < 4:
    line_agg = (
        alt.Chart(season_weighted_data)
        .mark_line(opacity=0.7)
        .encode(
            x=alt.X("cumulative_season:T", title="Date"),
            y=alt.Y(
                "weighted_mean_temp:Q",
                title="Weighted Mean Temperature (Pop * Celsius))",
                scale=alt.Scale(zero=False),
            ),
            tooltip=[
                "season_name_yr",
                alt.Tooltip("weighted_mean_temp:Q", format=".2f"),
                alt.Tooltip("weighted_min_temp:Q", format=".2f"),
                alt.Tooltip("weighted_max_temp:Q", format=".2f"),
            ],
            color="season_name",
        )
    )
    band_agg = (
        alt.Chart(season_weighted_data)
        .mark_area(opacity=0.3)
        .encode(
            x=alt.X("cumulative_season:T", title="Date"),
            y="weighted_min_temp:Q",
            y2="weighted_max_temp:Q",
            tooltip=[
                "season_name_yr",
                alt.Tooltip("weighted_mean_temp:Q", format=".2f"),
                alt.Tooltip("weighted_min_temp:Q", format=".2f"),
                alt.Tooltip("weighted_max_temp:Q", format=".2f"),
            ],
            color="season_name",
        )
    )
else:
    line_agg = (
        alt.Chart(season_weighted_data)
        .mark_line(opacity=0.7)
        .encode(
            x=alt.X("cumulative_season:T", title="Date"),
            y=alt.Y(
                "weighted_mean_temp:Q",
                title="Weighted Mean Temperature (Pop * Celsius))",
                scale=alt.Scale(zero=False),
            ),
            tooltip=[
                "season_name_yr",
                alt.Tooltip("weighted_mean_temp:Q", format=".2f"),
                alt.Tooltip("weighted_min_temp:Q", format=".2f"),
                alt.Tooltip("weighted_max_temp:Q", format=".2f"),
            ],
        )
    )
    band_agg = (
        alt.Chart(season_weighted_data)
        .mark_area(opacity=0.3)
        .encode(
            x=alt.X("cumulative_season:T", title="Date"),
            y="weighted_min_temp:Q",
            y2="weighted_max_temp:Q",
            tooltip=[
                "season_name_yr",
                alt.Tooltip("weighted_mean_temp:Q", format=".2f"),
                alt.Tooltip("weighted_min_temp:Q", format=".2f"),
                alt.Tooltip("weighted_max_temp:Q", format=".2f"),
            ],
        )
    )

lb_agg = alt.layer(line_agg, band_agg)

lb_agg.title = "Population Weighted Seasonal Temperatures"

st.altair_chart(lb_agg, use_container_width=True)

st.write(
    "Overlay your cursor to get specific temperature information for a given season/year. Seasons are calculated as Winter (Dec-Feb), Spring (March-May), Summer (June-Aug), and Autumn (Sept-Nov)."
)

st.button("Re-run")
