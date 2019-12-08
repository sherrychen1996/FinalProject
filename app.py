from flask import Flask, render_template, Markup, request
from model import *

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def homepage():
	if request.method == "POST":
		try:
			sortby = request.form["sortby"]
		except:
			sortby = "City Name"
		try:
			sortorder = request.form["sortorder"]
		except:
			sortorder = "AtoZ"
	else:
		sortby = "City Name"
		sortorder = "AtoZ"
	if sortorder == "ZtoA":
		bool_reverse = True
	else:
		bool_reverse = False
	if sortby == "City Name":
		city_list = sorted(get_city_info_db(), key=lambda x: x.cityName, reverse=bool_reverse)
	else:
		city_list = sorted(get_city_info_db(), key=lambda x: x.stateName, reverse=bool_reverse)
	len_list = range(len(city_list)//4)
	return render_template("homepage.html", 
		all_city_map=Markup(map_cities()), 
		list=city_list, 
		len_list=len_list)

@app.route("/<city>", methods=["GET", "POST"])
def citypage(city):
	city_list = get_city_info_db()
	for c in city_list:
		if c.cityName == city:
			break

	params = {"c.CityName": c.cityName}
	bsn_list = get_busi_info_db(params)
	bsn_dict = {}

	if request.method == "POST":
		try:
			show_info = request.form["show"]
			pie_chart = pie_rating_price(c, pie_info=show_info)
		except:
			pie_chart = pie_rating_price(c)
	else:
		pie_chart = pie_rating_price(c)

	if request.method == "POST":
		try:
			sortby = request.form["sortby"]
		except:
			sortby = "0/"
		try:
			sortorder = request.form["sortorder"]
		except:
			sortorder = "0/"
	else:
		sortby = "0/"
		sortorder = "0/"
	if sortorder == "0/":
		bool_sort = False
	else:
		bool_sort = True

	for b in bsn_list:
		bsn_dict[b.ID] = (b.name, b.rating, b.price)
	bsn_id_list = sorted(bsn_dict, key=lambda x: bsn_dict[x][int(sortby[0])], reverse=bool_sort)
	bsn_dict_sorted = {}
	for i in bsn_id_list:
		bsn_dict_sorted[i] = "{} (Rating: {}; Price: {})".format(*bsn_dict[i])

	return render_template("city.html", 
		CityName=c.__str__(), 
		City=city,
		RestaurantMap=Markup(map_businesses(c)),
		PieChart=Markup(pie_chart),
		BsnDict=bsn_dict_sorted)

@app.route("/res/<bsn>", methods=["GET", "POST"])
def respage(bsn):
	params = {"b.Id": bsn}
	res_list = get_busi_info_db(params)
	res = res_list[0]
	res_name = res.name
	image_url = res.imageUrl
	city_name = get_city_info_db(cond=res.ID)[0].cityName
	if request.method == "POST":
		try:
			user_choice = request.form["chart"]
			if user_choice == "rating":
				chart = bar_rating_same_price(res)
			elif user_choice == "price":
				chart = bar_price_same_rating(res)
			elif user_choice == "time":
				chart = table_open_times(res)
			else:
				chart = table_reviews(res)
		except:
			chart = 'Please choose one before click the "Update" button!'
	else:
		chart = ""
	
	return render_template("res.html", 
		ResName=res_name, 
		ImgUrl=image_url, 
		Bsn=bsn,
		Chart=Markup(chart),
		Reviews=Markup(table_reviews(res)),
		CityName=city_name)

if __name__=="__main__":
	app.run(debug=True)