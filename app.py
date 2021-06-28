import streamlit as st
import pandas as pd
import altair as alt


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
    # scales = alt.selection_interval(bind="scales")
    chart = lb + ch  # .add_selection(scales)
    chart.title = "Average Temperatures Recorded (unweighted)"

    st.altair_chart(chart, use_container_width=True)
    st.write(
        "Days with missing recordings are shown in red. We fill in the missing values based on an average between the previous and next recording for that station."
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
daily_weighted_data = get_daily_weighted_temperatures()
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
        tooltip=["weighted_mean_temp:Q"],
    )
)
band = (
    alt.Chart(data)
    .mark_area(opacity=0.3)
    .encode(
        x=alt.X("location_date:T", title="Date"),
        y="weighted_min_temp:Q",
        y2="weighted_max_temp:Q",
        tooltip=["weighted_mean_temp:Q"],
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
    "Here we weight temperatures recorded by the population of the cities in which they are recorded, to obtain a single timeseries."
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


# st.write("### Monthly and Seasonly Aggregates (weighted by population)")

# cities_agg = st.multiselect(
#     "Choose Cities", list(df.name.unique()), ["Portland", "New York"], key="Cities Agg"
# )
# from_date_agg = st.date_input(
#     "From", df.location_date.min().date(), key="From Date Agg"
# )
# to_date_agg = st.date_input("To", df.location_date.max().date(), key="To Date Agg")

# all_series = []

# for name in df["name"].unique():

#     mean_series = (
#         df.loc[df["name"] == name]
#         .groupby(pd.Grouper(key="location_date", freq="1M"))
#         .apply(weighted_mean_function())
#         .reset_index(name="weighted_mean_temp")
#     )
#     min_series = (
#         df.groupby(pd.Grouper(key="location_date", freq="1M"))
#         .apply(weighted_mean_function("temp_min_c"))
#         .reset_index(name="weighted_min_temp")
#     )
#     max_series = (
#         df.groupby(pd.Grouper(key="location_date", freq="1M"))
#         .apply(weighted_mean_function("temp_max_c"))
#         .reset_index(name="weighted_max_temp")
#     )
#     mean_series["weighted_min_temp"] = min_series["weighted_min_temp"]
#     mean_series["weighted_max_temp"] = max_series["weighted_max_temp"]
#     mean_series["name"] = name

#     all_series.append(mean_series)

# mean_df = pd.concat(all_series)

# if not cities_agg:
#     st.error("Please select at least one city.")
# elif from_date_agg > to_date_agg:
#     st.error("Please from date less than the to date.")
# else:
#     from_date_ts_agg = pd.Timestamp(from_date)
#     to_date_ts_agg = pd.Timestamp(to_date)

#     mask_agg = (
#         (mean_df.location_date >= from_date_ts_agg)
#         & (mean_df.name.isin(cities_agg))
#         & (mean_df.location_date <= to_date_ts_agg)
#     )
#     agg_data = mean_df.loc[mask_agg]

#     line_agg = (
#         alt.Chart(agg_data)
#         .mark_line(opacity=0.7)
#         .encode(
#             x=alt.X("location_date:T", title="Date"),
#             y=alt.Y(
#                 "weighted_mean_temp:Q",
#                 title="Weighted Mean Temperature (Pop * Celsius))",
#             ),
#         )
#     )
#     band_agg = (
#         alt.Chart(agg_data)
#         .mark_area(opacity=0.3)
#         .encode(
#             x=alt.X("location_date:T", title="Date"),
#             y="weighted_min_temp:Q",
#             y2="weighted_max_temp:Q",
#         )
#     )

#     lb_agg = alt.layer(line_agg, band_agg)

#     lb_agg.title = "Average Temperatures Recorded"

#     st.altair_chart(lb_agg, use_container_width=True)

# Streamlit widgets automatically run the script from top to bottom. Since
# this button is not connected to any other logic, it just causes a plain
# rerun.
st.button("Re-run")
