import streamlit as st
import polars as pl
import sys
import datetime
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

sys.path.append("../src")

from saving_plan import SavingPlan, get_saving_plans


def main():
    st.set_page_config(layout="wide")


    # Load the data
    df = pl.read_parquet("../data/msci_world_index.parquet").lazy()

    st.title("Simulating Saving Plans with MSCI World Index")

    col1, col2 = st.columns([0.4, 0.7])
    with col1:
        with open("description.txt", "r") as f:
            st.markdown(f.read())

    st.divider()

    col1, col2 = st.columns([0.3, 0.7], vertical_alignment="center")

    with col1:
        # add slider for the amount of money to invest
        st.text("Money to invest in each month")
        invest_amount = st.slider("Amount", 10, 5000, 10, 10)

        # day of month to invest
        st.text("Day of month to invest")
        day_of_month = st.slider("Day", min_value=1, max_value=31, step=1)

        # add date range slider
        st.text("Date range")
        start_date = st.date_input(
            "Start date",
            datetime.date(1990, 1, 1),
            min_value=datetime.date(1972, 1, 1),
            max_value=datetime.date(2024, 8, 31),
        )
        end_date = st.date_input(
            "End date",
            datetime.date(2024, 8, 31),
            min_value=datetime.date(1972, 1, 1),
            max_value=datetime.date(2024, 8, 31),
        )
        period = (start_date, end_date)

    with col2:
        # Get result of saving plan
        saving_plan = SavingPlan(df, invest_amount, day_of_month, period=period)
        result_df = saving_plan.result_df.collect()
        result_df = result_df.to_pandas()

        st.text("Cumulative return")

        fig = go.Figure()
        # st.line_chart(result_df, x="Date", y="total_worth", height=450)
        fig.add_trace(
            go.Scatter(
                x=result_df["Date"],
                y=result_df["total_worth"],
            )
        )
        # fig.add_trace(
        #     go.Scatter(
        #         x=result_df["Date"],
        #         y=result_df["Close"],
        #     ), secondary_y=True
        # )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    col1, col2, col3 = st.columns(3)

    saving_plans = list(
        get_saving_plans(df, invest_amount=invest_amount, period=period)
    )

    with col1:
        best_day = np.argmax([plan.total_worth for plan in saving_plans]) + 1
        st.metric("Best day to invest", f"{best_day}")

    with col2:
        worst_day = np.argmin([plan.total_worth for plan in saving_plans]) + 1
        st.metric("Worst day to invest", f"{worst_day}")

    with col3:
        diff = saving_plans[best_day].total_worth - saving_plans[worst_day].total_worth
        st.metric("Difference", f"{diff:.2f}€")


if __name__ == "__main__":
    main()
