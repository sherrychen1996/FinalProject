# SI507 Final Project
This project allows you to search for restaurants in one of the 100 largest cities in the US and get maps and many kinds of charts by choosing the ones you want in a Flask Web App.

## Data Sources
(1) The information about the 100 largest cities in the US from https://en.wikipedia.org/wiki/List_of_United_States_cities_by_population  
(2) The information about the restaurants in a city from Yelp Fusion. ( Documentation Link: https://www.yelp.com/developers/documentation/v3 ) ( You also need to get a Yelp APIkey by sign up this website: https://www.yelp.com/fusion )  

## Other Information
Getting-started page of plotly: https://plot.ly/python/getting-started/

## Code Structure
### Significant Data Processing Functions
(1) *get_city_info_db* Function: This function takes one parameter, *cond*, as input, which has a default value "None". When *cond* takes its default value, the function returns a list of City class instances of all 100 cities; when *cond* takes a business id, it returns a list which only contains one City class instance of the city the business is in.     
(2) *map_business* Function: This function takes a City class instance as input, and return a mapbox scatter plot. In this function, I loop the latitude, longitude and name of restaurants in the given city into three lists and use these lists to create a plotly map.  
(3) *pie_rating_price* Function: This function takes two parameters as inputs -- one is a City class instance and the other is a string which can take the value of "rating" or "price" (default: "rating"), and return a pie chart showing the percentage of different ratings/prices in a given city. In this function, I loop the restaurants' ratings and prices into two lists and use them to create a pie chart.
### Class Definitions  
(1) City: This class has four initial parameters -- *cityName*, *stateName*, *lat* and *lon*, and the *\_\_str\_\_* method returns a string which looks like "*cityName*, *stateName*".  
(2) YelpBusiness: This class has ten initial parameters -- *name*, *city*, *imageUrl* and so on. It has two methods -- the *open_time* method and the *review* method. The first one get the information about open and close time of the restaurant from the database, and the second one get the customer reviews from the database. What's more, the *\_\_str\_\_* method returns a string containing the restaurant's name, rating and price.  

## User Guide  
### How to Run the Program
Step 1: Install the Required Packages  
```  
$ pip install -r requirements.txt  
```  
Step 2: Run the app.py File  
```  
$ python app.py  
```  
Step 3: Copy the Url ( http://127.0.0.1:5000/ ) and Paste it in a Browser  
### How to Choose Presentation Options  
You can choose the presentation options by selecting the different checkbox and clicking the *update* button in the web app, or clicking a link to direct you to a different page.  
