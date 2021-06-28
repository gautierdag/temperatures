# temperatures

This is a short analysis of temperature data recorded from 2015-2020.

What prompted this analysis was a tweet:

![prompt][prompt.jpg]

All the code can be found in the jupyter notebook as well as a streamlit app running on heroku.

For imputing missing data/days we use an average between the last recorded temperature and the next recorded temperature.

Popualtion data for a couple of cities was found missing from the population dataframe and we complete this data from wikipedia.

Observations from weather stations are typically unique to cities, except for Portland which has two stations. We average the temperature recordings of these two stations to obtain a single series per city.
