import plotly.io as pio
import plotly.graph_objects as go
import plotly.express as px
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
