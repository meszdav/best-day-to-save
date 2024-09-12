import plotly.io as pio
import plotly.graph_objects as go
import plotly.express as px
import polars as pl
import numpy as np

colors = [
    "#219ebc",
    "#ffb703",
    "#7209b7",
    "#023097",
    "#f72585",
    "#8ecae6",
    "#fb8500",
    "#3a0ca3",
    "#4361ee",
    "#4cc9f0",
]

pio.templates.default = "plotly_dark"

# add colors to the template
pio.templates[pio.templates.default].layout.update({"colorway": colors})

# add fig.update_traces(marker_line_width=1, marker_line_color="#252525") to layout
pio.templates[pio.templates.default].layout.update(
    {
        "marker": {"line": {"width": 1, "color": "#252525"}},
    }
)


def plot_total_worth(
    total_worth_all: list,
    title: str,
    period: str,
):

    fig = go.Figure()

    fig.add_trace(go.Bar(x=list(range(1, 32)), y=total_worth_all, name="Total Worth"))

    # update range for y
    fig.update_yaxes(
        tickformat="$,.0f",
        range=[np.min(total_worth_all) * 0.992, np.max(total_worth_all) * 1.002],
    )

    # show all ticks for x
    fig.update_xaxes(tickmode="array", tickvals=list(range(1, 32)))

    if period == "max":
        period = "3/1/1972 - 3/9/2024"
    else:
        period = f"{period[0].strftime('%d/%m/%Y')} - {period[1].strftime('%d/%m/%Y')}"

    # update layout
    fig.update_layout(
        width=1000,
        height=500,
        title=title + f" ({period})",
        xaxis_title="Day of the Month",
        yaxis_title="Total Worth in USD",
        template="plotly_dark",
    )

    # add a horizontal line for the total worth
    fig.add_hline(
        y=np.max(total_worth_all),
        line_dash="dash",
        line_color="red",
        annotation_text=f"Max Total Worth: {np.max(total_worth_all):.2f}",
        annotation_position="bottom right",
    )

    # add horizontal line for the worst day
    worst_day = np.argmin(total_worth_all) + 1
    fig.add_hline(
        y=total_worth_all[worst_day - 1],
        line_dash="dash",
        line_color="yellow",
        annotation_text=f"Min Total Worth: {np.min(total_worth_all):.2f}",
        annotation_position="top right",
    )

    return fig


def plot_max_diff_distribution(df: pl.DataFrame):
    if isinstance(df, pl.LazyFrame):
        df = df.collect()

    plot_df = (
        df.group_by("period")
        .agg(
            pl.min("total_worth").alias("min_total_worth"),
            pl.max("total_worth").alias("max_total_worth"),
        )
        .with_columns(
            (pl.col("max_total_worth") - pl.col("min_total_worth")).alias("diff")
        )
        .with_columns(
            (pl.col("diff") / pl.col("min_total_worth")).alias("diff_percentage") * 100
        )
    )

    values = plot_df["diff_percentage"].to_numpy()

    fig = px.histogram(
        values,
        nbins=100,
        title="Distribution of max total worth difference in % for every possible 15 year period",
    )

    # change ticks to every second
    tickvals = list(range(int(values.min()), int(values.max()), 1))
    fig.update_xaxes(tickmode="array", tickvals=tickvals, showgrid=False)
    fig.update_yaxes(showgrid=False)

    # q1
    q1 = np.quantile(values, 0.25)
    q3 = np.quantile(values, 0.75)
    median = np.median(values)

    fig.add_vline(
        x=q1,
        line_dash="dash",
        line_color="yellow",
        annotation_text=f"Q1: {q1:.2f}%",
        annotation_position="top left",
    )
    fig.add_vline(
        x=median,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Median: {median:.2f}%",
        annotation_position="right",
    )
    fig.add_vline(
        x=q3,
        line_dash="dash",
        line_color="yellow",
        annotation_text=f"Q3: {q3:.2f}%",
        annotation_position="top right",
    )

    fig.update_traces(marker_line_width=1, marker_line_color="#252525")

    fig.update_layout(
        width=1000,
        height=500,
        title="Distribution of max total worth difference in % for every possible 15 year period",
        xaxis_title="Total Worth Difference in %",
        yaxis_title="Frequency",
        template="plotly_dark",
        showlegend=False,
    )

    return fig


def plot_best_day_distribution(result_df: pl.DataFrame):
    """Plot the distribution of the best day to invest."""
    if isinstance(result_df, pl.LazyFrame):
        result_df = result_df.collect()

    plot_df = result_df.filter(
        pl.col("total_worth").max().over("period") == pl.col("total_worth")
    )

    values = (
        plot_df["day_to_invest"]
        .value_counts(name="num_occurences")
        .sort("day_to_invest")
    )
    print(values)

    fig = px.bar(
        x=values["day_to_invest"].to_list(),
        y=values["num_occurences"].to_list(),
        title="Distribution of mean total worth for every possible day to invest",
    )

    fig.update_xaxes(title="Day to Invest")
    fig.update_yaxes(title="Mean Total Worth")

    fig.update_layout(
        width=1000,
        height=500,
        title="Distribution of mean total worth for every possible day to invest",
        xaxis_title="Day to Invest",
        yaxis_title="How many times was the best day to invest",
        template="plotly_dark",
        showlegend=False,
    )

    return fig
