# SI507 Final Project
This project allows you to search for restaurants in one of the 100 largest cities in the US and get maps and many kinds of charts by choosing the ones you want in a Flask Web App.

## Data Sources
(1) The information about the 100 largest cities in the US from https://en.wikipedia.org/wiki/List_of_United_States_cities_by_population  
(2) The information about the restaurants in a city from Yelp Fusion. ( Documentation Link: https://www.yelp.com/developers/documentation/v3 ) ( You also need to get a Yelp APIkey by sign up this website: https://www.yelp.com/fusion )  

## Code Structure
### Significant Data Processing Functions
(1) *map_business* Function  
    This function takes a City class instance as input, and return a mapbox scatter plot. In this function, I loop the latitude, longitude and name of restaurants in the given city into three lists and use these lists to create a plotly map.  
