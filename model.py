import requests
import json
import sqlite3
from requests_oauthlib import OAuth1
from bs4 import BeautifulSoup
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from plotly.offline import plot
import numpy as np
from secret import *

DBNAME = "FinalProj.db"
CACHE_FNAME = "cache.json"

# CACHE FUNCTIONS
headers = {"Authorization": "Bearer " + yelp_api_key}

try:
	cache_file = open(CACHE_FNAME, "r")
	cache_content = cache_file.read()
	CACHE_DICTION = json.loads(cache_content)
	cache_file.close()
except:
	CACHE_DICTION = {}

def make_request_using_cache_scrape(url):
	if url in CACHE_DICTION:
		return CACHE_DICTION[url]
	else:
		CACHE_DICTION[url] = requests.get(url).text
		fw = open(CACHE_FNAME, "w")
		fw.write(json.dumps(CACHE_DICTION))
		fw.close()
		return CACHE_DICTION[url]

def get_response_dict(params_inp, base_url_inp):
	response = requests.get(base_url_inp, headers=headers, params=params_inp)
	response_dict = json.loads(response.text)
	return response_dict

def params_unique_combination(params_inp, base_url_inp):
	alphabetized_keys = sorted(params_inp.keys())
	res = []
	for k in alphabetized_keys:
		res.append("{}-{}".format(k, params_inp[k]))
	return base_url_inp + "_" + "_".join(res)

def make_request_using_cache_api(params_inp, base_url_inp):
	unique_ident = params_unique_combination(params_inp, base_url_inp)
	if unique_ident in CACHE_DICTION:
		return json.loads(CACHE_DICTION[unique_ident])
	else:
		CACHE_DICTION[unique_ident] = json.dumps(
			get_response_dict(params_inp, base_url_inp))
		fw = open(CACHE_FNAME, "w")
		fw.write(json.dumps(CACHE_DICTION))
		fw.close()
		return json.loads(CACHE_DICTION[unique_ident])


# CREATE A DATABASE

conn = sqlite3.connect(DBNAME)
cur = conn.cursor()

## Scrape the Page
def init_scrape():
	page_url = "https://en.wikipedia.org/wiki/List_of_United_States_cities_by_population"
	page_text = make_request_using_cache_scrape(page_url)
	soup = BeautifulSoup(page_text, "html.parser")

	target = soup.find_all(
		"table", class_="wikitable sortable")[0].find("tbody").find_all("tr")
	city_list = []
	state_list = []
	land_area_list = []
	population_density_list = []
	lat_list = []
	lon_list = []
	for i in range(100):
		td_list = target[i + 1].find_all("td")
		city_list.append(td_list[1].find("a").text)
		try:
			state_list.append(td_list[2].find("a").text)
		except:
			state_list.append(td_list[2].text[1:-1])
		land_area_list.append(
			float(td_list[7].text.split("\xa0")[0].replace(",", "")))
		population_density_list.append(
			int(td_list[9].text.split("/")[0].replace(",", "")))
		lat_list.append(
			float(td_list[-1].find("span", class_="geo-dec").text.split()[0][:-2]))
		lon_list.append(-float(td_list[-1].find(
			"span", class_="geo-dec").text.split()[1][:-2]))
	city_table_row_list = []
	for i in range(len(city_list)):
		city_table_row_list.append(
			(city_list[i], state_list[i], land_area_list[i],
			population_density_list[i], lat_list[i], lon_list[i]))

	return city_table_row_list

cmd = "DROP TABLE IF EXISTS 'City';"
cur.execute(cmd)

cmd = "CREATE TABLE 'City' ("
cmd += "Id INTEGER PRIMARY KEY AUTOINCREMENT, "
cmd += "CityName TEXT NOT NULL, "
cmd += "StateName TEXT NOT NULL, "
cmd += "LandArea REAL NOT NULL, "
cmd += "PopulationDensity INTEGER NOT NULL, "
cmd += "Lat REAL NOT NULL, "
cmd += "Lon REAL NOT NULL"
cmd += ");"
cur.execute(cmd)

cmd = "INSERT INTO City "
cmd += "VALUES (NULL, ?, ?, ?, ?, ?, ?);"
for c in init_scrape():
	cur.execute(cmd, c)
conn.commit()

## Yelp Search Businesses
def init_yelp_search():
	business_table_row_list = []
	search_business_url = "https://api.yelp.com/v3/businesses/search"
	i = 0
	id_list = []
	for c in init_scrape():
		i += 1
		search_business_params = {"location": c[0], "categories": "food"}
		yelp_list = make_request_using_cache_api(search_business_params,
												search_business_url)["businesses"]
		for b in yelp_list:
			add_list = []
			try:
				if b["id"] not in id_list:
					id_list.append(b["id"])
					add_list.append(b["id"])
				else:
					continue
				add_list.append(b["name"])
				add_list.append(i)
				add_list.append(b["image_url"])
				add_list.append(b["review_count"])
				add_list.append(b["rating"])
				add_list.append(b["coordinates"]["latitude"])
				add_list.append(b["coordinates"]["longitude"])
				add_list.append(len(b["price"]))
				add_list.append(", ".join(b["location"]["display_address"]))
				business_table_row_list.append(tuple(add_list))
			except:
				continue

	return business_table_row_list

cmd = "DROP TABLE IF EXISTS 'Businesses';"
cur.execute(cmd)

cmd = "CREATE TABLE 'Businesses' ("
cmd += "Id TEXT PRIMARY KEY, "
cmd += "BusinessName TEXT NOT NULL, "
cmd += "CityId INTEGER NOT NULL, "
cmd += "ImageUrl TEXT, "
cmd += "NumOfReview INTEGER, "
cmd += "Rating REAL, "
cmd += "Lat REAL, "
cmd += "Lon REAL, "
cmd += "Price INTEGER, "
cmd += "Address TEXT NOT NULL, "
cmd += "FOREIGN KEY(CityId) REFERENCES City(Id)"
cmd += ");"
cur.execute(cmd)

cmd = "INSERT INTO Businesses "
cmd += "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"
for b in init_yelp_search():
	cur.execute(cmd, b)
conn.commit()

## Yelp Business Times
def get_id_list():
	conn_f = sqlite3.connect(DBNAME)
	cur_f = conn_f.cursor()
	cmd = "SELECT Id FROM Businesses"
	result = cur_f.execute(cmd).fetchall()
	id_list = []
	for row in result:
		id_list.append(row[0])
	conn_f.close()
	return id_list

def init_yelp_times():
	business_detail_table_row_list = []
	business_detail_url = "https://api.yelp.com/v3/businesses/{}"
	for id_i in get_id_list():
		yelp_dict = make_request_using_cache_api({},
												business_detail_url.format(id_i))
		add_list = []
		add_list.append(id_i)
		try:
			j_list = [0, 1, 2, 3, 4, 5, 6]
			time_list = [[], [], [], [], [], [], []]
			for days in yelp_dict["hours"][0]["open"]:
				for j in j_list:
					if days["day"] == j:
						time_list[j].append("{} to {}".format(
							days["start"][:2] + ":" + days["start"][2:],
							days["end"][:2] + ":" + days["end"][2:]))
		except:
			continue
		for t in time_list:
			if t == []:
				add_list.append("closed")
			else:
				add_list.append(", ".join(t))
		business_detail_table_row_list.append(tuple(add_list))

	return business_detail_table_row_list

cmd = "DROP TABLE IF EXISTS 'BusinessTimes';"
cur.execute(cmd)

cmd = "CREATE TABLE 'BusinessTimes' ("
cmd += "BusinessId TEXT PRIMARY KEY, "
cmd += "Mon TEXT NOT NULL, "
cmd += "Tues TEXT NOT NULL, "
cmd += "Wed TEXT NOT NULL, "
cmd += "Thur TEXT NOT NULL, "
cmd += "Fri TEXT NOT NULL, "
cmd += "Sat TEXT NOT NULL, "
cmd += "Sun TEXT NOT NULL, "
cmd += "FOREIGN KEY(BusinessId) REFERENCES Businesses(Id)"
cmd += ");"
cur.execute(cmd)

cmd = "INSERT INTO BusinessTimes "
cmd += "VALUES (?, ?, ?, ?, ?, ?, ?, ?);"
for b in init_yelp_times():
	cur.execute(cmd, b)
conn.commit()

## Yelp Business Reviews
def init_yelp_reviews():
	business_review_row_list = []
	business_review_url = "https://api.yelp.com/v3/businesses/{}/reviews"
	for id_i in get_id_list():
		yelp_list = make_request_using_cache_api(
			{}, business_review_url.format(id_i))["reviews"]
		add_list = []
		add_list.append(id_i)
		try:
			for r in yelp_list:
				add_list.append(r["text"])
				add_list.append(r["time_created"])
		except:
			add_list += ["", "", "", "", "", ""]
		business_review_row_list.append(tuple(add_list))

	return business_review_row_list

cmd = "DROP TABLE IF EXISTS 'BusinessReviews';"
cur.execute(cmd)

cmd = "CREATE TABLE 'BusinessReviews' ("
cmd += "BusinessId TEXT PRIMARY KEY, "
cmd += "Review1 TEXT, "
cmd += "CreateTime1 TEXT, "
cmd += "Review2 TEXT, "
cmd += "CreateTime2 TEXT, "
cmd += "Review3 TEXT, "
cmd += "CreateTime3 TEXT, "
cmd += "FOREIGN KEY(BusinessId) REFERENCES Businesses(Id)"
cmd += ");"
cur.execute(cmd)

cmd = "INSERT INTO BusinessReviews "
cmd += "VALUES (?, ?, ?, ?, ?, ?, ?);"
for b in init_yelp_reviews():
	cur.execute(cmd, b)
conn.commit()
conn.close()


# CREATE CLASSES
## City Class
class City():
	def __init__(self, cityName=None, stateName=None, lat=None, lon=None):
		self.cityName = cityName
		self.stateName = stateName
		self.lat = lat
		self.lon = lon

	def __str__(self):
		return "{}, {}".format(self.cityName, self.stateName)

## Yelp Class
class YelpBusiness():
	def __init__(self,
				name=None,
				city=None,
				imageUrl=None,
				rating=None,
				price=None,
				address=None,
				lat=None,	
				lon=None,
				ID=None,
				reviewNum=None):
		self.name = name
		self.city = city
		self.imageUrl = imageUrl
		self.reviewNum = reviewNum
		self.rating = rating
		self.price = price
		self.address = address
		self.lat = lat
		self.lon = lon
		self.ID = ID

	def open_time(self):
		conn = sqlite3.connect(DBNAME)
		cur = conn.cursor()
		cmd = "SELECT Mon, Tues, Wed, Thur, Fri, Sat, Sun "
		cmd += "FROM BusinessTimes "
		cmd += 'WHERE BusinessId="{}";'.format(self.ID)
		result = cur.execute(cmd).fetchall()
		time = []
		for row in result:
			for i in range(len(row)):
				time.append(row[i])
		time_split = []
		for t in time:
			time_split.append(t.split(", "))
		conn.close()
		return time_split

	def review(self):
		conn = sqlite3.connect(DBNAME)
		cur = conn.cursor()
		cmd = "SELECT CreateTime1, Review1, CreateTime2, Review2, CreateTime3, Review3 "
		cmd += "FROM BusinessReviews "
		cmd += 'WHERE BusinessId="{}";'.format(self.ID)
		result = cur.execute(cmd).fetchall()
		time_list = []
		review_list = []
		for row in result:
			time_list += [row[0], row[2], row[4]]
			review_list += [row[1], row[3], row[5]]
		conn.close()
		return (time_list, review_list)

	def __str__(self):
		try:
			return "{} (Rating: {}, Price: {})".format(
				self.name, str(self.rating), "$" * self.price)
		except:
			return self.name


# PRESENTATION FUNCTIONS
## Map for 100 Largest Cities
def get_city_info_db(cond=None):
	conn = sqlite3.connect(DBNAME)
	cur = conn.cursor()
	cmd = "SELECT c.CityName, c.StateName, c.Lat, c.Lon"
	cmd += " From City AS c"
	if cond != None:
		cmd += " JOIN Businesses AS b ON b.cityId=c.Id"
		cmd += ' WHERE b.Id="{}"'.format(cond)
	cmd += ";"
	city_class_list = []
	result = cur.execute(cmd).fetchall()
	for row in result:
		city_class_list.append(City(*row))
	conn.close()
	return city_class_list

def map_cities():
	text_list = []
	lat_list = []
	lon_list = []
	for city in get_city_info_db():
		text_list.append(city.__str__())
		lat_list.append(str(city.lat))
		lon_list.append(str(city.lon))

	layout = dict(title='(Hover for city names)',
                  geo=dict(scope='usa',
                           showland=True,
                           showocean=True,
                           showlakes=True,
                           showsubunits=True,
                           lakecolor="lightblue",
                           oceancolor="lightblue",
                           bgcolor="cornsilk",
                           countrywidth=3,
                           subunitwidth=3))

	fig = go.Figure(data=go.Scattergeo(
        lon=lon_list,
        lat=lat_list,
        text=text_list,
        mode='markers',
        marker=dict(size=15, symbol="star", color="purple")))

	fig.update_layout(layout)

	layout = go.Layout(plot_bgcolor="cornsilk",
                       paper_bgcolor="cornsilk",
                       width=1200,
                       height=700)
	fig.update_layout(layout)

	pic = plot(fig, output_type="div")

	return pic

## Table of a Business Open Times
def table_open_times(yelp_business):
	table_content = []
	for time in yelp_business.open_time():
		table_content.append("; ".join(time))

	headerColor = 'mediumorchid'
	rowEvenColor = 'plum'
	rowOddColor = 'white'

	if len(table_content) == 0:
		table_content = ["Unavailable"] * 7

	fig = go.Figure(data=[
        go.Table(
            header=dict(values=['<b>DAY</b>', '<b>OPEN TIME</b>'],
                        line_color='darkslategray',
                        fill_color=headerColor,
                        align=['left', 'center'],
                        font=dict(color='white', size=12)),
            cells=dict(values=[
                [
                    'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday',
                    'Saturday', 'Sunday'
                ],
                table_content,
            ],
                       line_color='darkslategray',
                       fill_color=[[
                           rowOddColor, rowEvenColor, rowOddColor,
                           rowEvenColor, rowOddColor, rowEvenColor, rowOddColor
                       ] * 2],
                       align=['left', 'center'],
                       font=dict(color='darkslategray', size=11)))
    ])

	layout = go.Layout(plot_bgcolor="cornsilk",
                       paper_bgcolor="cornsilk",
                       width=1200,
                       height=400)
	fig.update_layout(layout)

	pic = plot(fig, output_type="div")

	return pic

## Map for Businesses in a City
def get_busi_info_db(params_inp=None):
	conn = sqlite3.connect(DBNAME)
	cur = conn.cursor()
	cmd = "SELECT b.BusinessName, c.CityName, b.ImageUrl, b.Rating, b.Price, b.Address, b.Lat, b.Lon, b.ID"
	cmd += " FROM Businesses AS b"
	cmd += " JOIN City AS c ON b.CityId=c.Id"
	if params_inp != None:
		key = list(params_inp.keys())[0]
		cmd += ' WHERE {}="{}"'.format(key, params_inp[key])
	cmd += ";"
	result = cur.execute(cmd).fetchall()
	business_list = []
	for row in result:
		business_list.append(YelpBusiness(*row))
	
	conn.close()
	return business_list

def map_businesses(city):
	params = {"c.CityName": city.cityName}
	text_list = []
	lat_list = []
	lon_list = []
	for busi in get_busi_info_db(params):
		text_list.append("{} ({})".format(busi.name, busi.address))
		lat_list.append(str(busi.lat))
		lon_list.append(str(busi.lon))

	lat_list_num = []
	lon_list_num = []
	for i in range(len(lat_list)):
		lat_list_num.append(float(lat_list[i]))
		lon_list_num.append(float(lon_list[i]))
	lat_center = np.median(lat_list_num)
	lon_center = np.median(lon_list_num)

	fig = go.Figure(
        go.Scattermapbox(
            lat=lat_list,
            lon=lon_list,
            mode='markers',
            marker=go.scattermapbox.Marker(size=6),
            text=text_list,
        ))

	layout = dict(
        autosize=True,
        hovermode='closest',
        mapbox=go.layout.Mapbox(accesstoken=mapbox_access_token,
                                bearing=0,
                                center=go.layout.mapbox.Center(lat=lat_center,
                                                               lon=lon_center),
                                pitch=0,
                                zoom=10),
    )

	fig.update_layout(layout)

	layout = go.Layout(plot_bgcolor="cornsilk",
                       paper_bgcolor="cornsilk",
                       width=1200,
                       height=700)
	fig.update_layout(layout)

	pic = plot(fig, output_type="div")

	return pic

## Pie Charts
def pie_rating_price(city, pie_info="rating"):
	params = {"c.CityName": city.cityName}
	rating_list = []
	price_list = []
	for busi in get_busi_info_db(params):
		rating_list.append(busi.rating)
		price_list.append(busi.price)
	rating_dict = {}
	price_dict = {}
	for r in rating_list:
		if r not in rating_dict:
			rating_dict[r] = 0
		rating_dict[r] += 1
	for p in price_list:
		p_key = "$" * p
		if p_key not in price_dict:
			price_dict[p_key] = 0
		price_dict[p_key] += 1

	label1 = sorted(rating_dict, reverse=True)
	value1 = []
	for l in label1:
		value1.append(rating_dict[l])
	label2 = sorted(price_dict, key=lambda x: len(x), reverse=True)
	value2 = []
	for l in label2:
		value2.append(price_dict[l])

	fig = make_subplots(rows=1,
                        cols=1,
                        specs=[[{
                            'type': 'domain'
                        }]])

	if pie_info == "rating":
		fig.add_trace(go.Pie(labels=label1, values=value1, name="Ratings"), 1, 1)
		text = "Ratings"
	else:
		fig.add_trace(go.Pie(labels=label2, values=value2, name="Prices"), 1, 1)
		text = "Prices"
		
	fig.update_traces(hole=.4, hoverinfo="label+percent+name")
	fig.update_layout(annotations=[
						dict(text=text,
							font_size=20,
							showarrow=False)])

	layout = go.Layout(plot_bgcolor="cornsilk",
                       paper_bgcolor="cornsilk",
                       width=1000,
                       height=600)
	fig.update_layout(layout)

	pic = plot(fig, output_type="div")

	return pic

## Bar Plots for Ratings and Prices
def get_avg_info(params_inp):
	conn = sqlite3.connect(DBNAME)
	cur = conn.cursor()
	cmd = "SELECT AVG({})".format(list(params_inp.keys())[3])
	cmd += " FROM Businesses AS b"
	cmd += " JOIN City AS c ON b.CityId=c.Id"
	cmd += ' WHERE c.CityName="{}" and {}={} and b.BusinessName<>"{}";'.format(
        list(params_inp.values())[0], 
		list(params_inp.keys())[1], 
		list(params_inp.values())[1], 
		list(params_inp.values())[2])
	result = cur.execute(cmd).fetchall()

	conn.close()
	return result[0][0]

def bar_rating_same_price(yelp_business):
	params = {"c.CityName": yelp_business.city, 
				"b.Price": yelp_business.price, 
				"b.BusinessName": yelp_business.name,
				"b.Rating": None}

	text_same_price = [yelp_business.name, "Average of Others"]
	rating_same_price = [yelp_business.rating, get_avg_info(params)]

	colors = ["mediumorchid", "plum"]

	fig = go.Figure(data=[
        go.Bar(
            x=text_same_price,
            y=rating_same_price,
            text=rating_same_price,
            marker_color=colors,
            textposition='auto',
        )
    ])
    
	layout = go.Layout(plot_bgcolor="cornsilk",
                       paper_bgcolor="cornsilk",
					   title="Ratings",
                       width=900,
                       height=500)
	fig.update_layout(layout)

	pic = plot(fig, output_type="div")

	return pic

def bar_price_same_rating(yelp_business):
	params = {"c.CityName": yelp_business.city,
				"b.Rating": yelp_business.rating,
				"b.BusinessName": yelp_business.name,
				"b.Price": None}

	text_same_rating = [yelp_business.name, "Average of Others"]
	price_same_rating = [yelp_business.price, get_avg_info(params)]

	colors = ["mediumorchid", "plum"]

	fig = go.Figure(data=[
        go.Bar(
            x=text_same_rating,
            y=price_same_rating,
            text=price_same_rating,
            marker_color=colors,
            textposition='auto',

        )
    ])
	
	layout = go.Layout(plot_bgcolor="cornsilk",
                       paper_bgcolor="cornsilk",
					   title="Prices",
                       width=900,
                       height=500)
	fig.update_layout(layout)
	pic = plot(fig, output_type="div")

	return pic

## Table of Reviews
def table_reviews(yelp_business):
	time_content = yelp_business.review()[0]
	review_content = yelp_business.review()[1]

	headerColor = 'mediumorchid'
	rowEvenColor = 'plum'
	rowOddColor = 'white'

	fig = go.Figure(data=[
        go.Table(header=dict(values=['<b>CREATE TIME</b>', '<b>REVIEW</b>'],
                             line_color='darkslategray',
                             fill_color=headerColor,
                             align=['center'],
                             font=dict(color='white', size=12)),
                 cells=dict(
                     values=[
                         time_content,
                         review_content,
                     ],
                     line_color='darkslategray',
                     fill_color=[[
                         rowOddColor, rowEvenColor, rowOddColor
                     ] * 2],
                     align=['center'],
                     font=dict(color='darkslategray', size=11)))
    ])

	layout = go.Layout(plot_bgcolor="cornsilk",
                       paper_bgcolor="cornsilk",
                       width=1200,
                       height=400)
	fig.update_layout(layout)

	pic = plot(fig, output_type="div")

	return pic