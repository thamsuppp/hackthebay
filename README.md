# Isaac and Sean Hack the Bay

View our presentation slides at `Hack the Bay Prez.pdf`.

Watch our presentation video and read our writeup [here](http://devpost.com/software/sean-isaac/)!

Play with our interactive visualization [here](http://thamsuppp.pythonanywhere.com/)!


## Overview

This project aims to visualize and model phosphorous and nitrogen pollution in specific regions of the Chesapeake Bay, utilizing data from the Chesapeake Bay Program's (CBP) database, as well as the Chesapeake Monitoring Collective (CMC). We created an interactive visualization app, as well as used machine learning and time-series analysis to explain and predict pollution levels in various segments of the bay over time.

## Motivation

We are both interested in geography and data science and wanted to apply our skills to solve a challenge of practical environmental concern - water pollution in the Chesapeake Bay. We were inspired by the geospatial data scientists who introduced us to the spatial visualization tools. Geosptial data is a new and challenge type of data that we have yet to work with before, which further motivated us to learn more.

## Screenshots

## Tech/framework used
Visualization App: 

- [Plotly Dash](https://plotly.com/dash/), a Python frameowrk for building interactive data science web apps. 
- [Mapbox](www.mapbox.com), an open source mapping platform API that enables customized plotting - scatter and choropleth overlays on base maps.
- [Python Anywhere](www.pythonanywhere.com), a Python-based web hosting service - we used this to host and deploy the app/

Machine Learning and Time Series Prediction:
- [Statsmodels Time Series Analysis](https://www.statsmodels.org/stable/tsa.html) for SARIMAX time series modelling
- [scikit-learn](https://scikit-learn.org/) for XGBoost regressor as well as other utility functions for machine learning
- [networkx](https://networkx.org/documentation/stable/tutorial.html) to model HUC water flow dependencies as directed acyclic graphs

Processing Land Use Data:
- [QGIS](https://qgis.org/en/site/) to extract pixel counts from raster images for land use analysis

## Files
- `viz.py` - contains the entire code needed for the Dash visualization app
- `Exploratory Data Analysis.ipynb` - processing the HUC, water quality and point source data to a form amenable for analysis
- `Final Raster Land Use Processing.ipynb` and `HUC Filter.ipynb` - processing raster image data output from QGIS into pixel percentages over the appropriate areas
- `Modelling.ipynb` - notebook for the regression, XGBoost and SARIMAX modelling of pollution data

## Our process

### Visualizing the Data
The spatio-temporal data given to us was very complex and difficult to perceive, so we created an interactive visualization using Python Dash that allows us to see spatial relationships between pollution sources and sensor stations, as well as the time-series for each sensor station to see how associations change over time. This allowed us to discover some preliminary hypotheses such as the seasonality of nitrogen and pollution levels, as well as nitrogen pollution being higher near urban areas such as Baltimore.

### Transforming the data
Then, we transformed the given data into relevant input features for machine learning modelling. We found it important to capture the spatial relationships (i.e. upstream and downstream) between HUCs, and hence used innovative data representations like directed acyclic graphs to represent HUC dependencies. We also tried to use the land use data by counting pixels of certain colors using QGIS, but as the files were huge we could only process land use data for 8 HUCs.

### Modelling the data
We then used linear regression to investigate the statistical significance of the different predictors, then used XGBoost, a machine learning algorithm, to uncover non-linear relationships as well as variable importance. This settles our first aim of uncovering the underlying factors affecting nitrogen and phosphorous pollution levels. Then, for each point, we developed a time-series model (SARIMAX) with the goal of predicting future pollution using past data, splitting out data into train and test samples to ensure the generalizability of the fitted models. We were able to fit a model that makes suitably good predictions over the test data.

## Contribute

Feel free to use the code, particularly the visualization, to tackle any geospatial data science project you have!

## Credits

**Hack the Bay Resources**
- [Wrangling Geospatial Data Github](https://github.com/oceanspace/DatabricksHackathon/tree/master/WiDS_Tutorial) - contains very useful code for initial wrangling of geospatial data that got us started
- [Hack the Bay Github](https://github.com/Hack-the-Bay/hack-the-bay) - comprehensive list of relevant datasets and code to process some of the geospatial data

**External Data (not listed in Hack the Bay Github)**
- [Chesapeake Bay Point Source Pollution Database](https://www.chesapeakebay.net/what/downloads/bay_program_nutrient_point_source_database)
- [Population by County (Census Bureau)](https://www.census.gov/data/tables/time-series/demo/popest/intercensal-2000-2010-counties.html)
- [Chesapeake Bay Land Use Data](https://www.chesapeakeconservancy.org/conservation-innovation-center/high-resolution-data/land-use-data-project/)

**Methods**
- [Guide to Time Series Forecasting using ARIMA](https://www.machinelearningplus.com/time-series/arima-model-time-series-forecasting-python/)