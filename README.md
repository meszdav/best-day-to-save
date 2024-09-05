---
author:
  name: "David Meszaros"
date: 2024-09-03
linktitle: bdts
title: Best day to invest
type:
- post
- posts
weight: 10
aliases:
- /blog/best-day-to-invest/
---
# What is the best day of the month to schedule your saving plans ? 

One day, I checked my ETF savings plan and noticed that the stock price seemed higher on the days when the plan was executed. My intuition suggested that on those days, the price was higher than expected, especially compared to the previous days when it appeared to be lower. Although this perception was rather subjective and I didn’t thoroughly check all the months when my savings plan was executed, it was strange enough to make me curious. I thought it would be interesting to create a project to determine which day is the best to trigger my savings plan.

To check which is the best day to invest, I will analyze the MSCI World Index because it is a well-known and long-established index used by many ETF providers.

I wanted to use the most reliable data source, which I believed would be the official MSCI [data](https://www.msci.com/end-of-day-history). However, this site only provides daily data up to 1997, which is not ideal because determining the best day of the month obviously requires daily data 🧐.

I would just skip the story how I finally found the most obvious and easiest data source for my research after many hours of deep diving into the farthest corners of the internet.

We can simply use the yfinance library, which I was already familiar with, though I wasn't aware that the Yahoo API provides data on indices. With this library, we're able to retrieve historical daily data for the [MSCI World Index](https://finance.yahoo.com/quote/%5E990100-USD-STRD/history/?filter=history) dating back to the 1970s, the last 50 years, which is quite impressive. 

<!-- Additionally, I check the holidays for each date recorded in the data. I think this could have a distortion affect to the end results. To check whether a day is a holiday or not we can use the `holidays` library which supports 152 countries. -->



