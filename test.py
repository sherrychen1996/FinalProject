import unittest
from app import *

class TestDataSource(unittest.TestCase):

    def testScrapeSource(self):
        self.assertEqual(len(init_scrape()), 100)

        city_list = []
        for i in init_scrape():
            city_list.append(i[0])
        self.assertIn("Dallas", city_list)
    
    def testYelpSource(self):
        self.assertEqual(len(init_yelp_search()[19]), 10)
        self.assertEqual(len(init_yelp_times()[35]), 8)
        self.assertEqual(len(init_yelp_reviews()[52]), 7)
    
class TestDataBase(unittest.TestCase):

    def testCityTable(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()

        cmd = "SELECT CityName FROM City "
        cmd += "ORDER BY LandArea DESC "
        cmd += "LIMIT 1;"
        result = cur.execute(cmd).fetchall()
        
        conn.close()
        self.assertEqual(result[0][0], "Anchorage")
    
    def testBusinessesTable(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()

        cmd = "SELECT BusinessName FROM Businesses "
        cmd += "WHERE CityId=7;"
        result = cur.execute(cmd).fetchall()

        conn.close()
        self.assertLessEqual(len(result), 20)
    
    def testTimesTable(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()

        cmd = "SELECT Tues FROM BusinessTimes "
        cmd += "LIMIT 1 OFFSET 56;"
        result = cur.execute(cmd).fetchall()
        r = result[0][0]

        conn.close()
        self.assertTrue(("to" in r) or (r == "closed"))
    
    def testReviewsTable(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()

        cmd = "SELECT CreateTime1 FROM BusinessReviews "
        cmd += "LIMIT 1 OFFSET 45;"
        result = cur.execute(cmd).fetchall()
        r = result[0][0]

        conn.close()
        self.assertIn("-", r)
    
    def testCityCmdFunc(self):
        r = get_city_info_db()
        self.assertIsInstance(r[0], City)
        self.assertEqual(len(r), 100)
    
    def testBusiCmdFunc(self):
        r = get_busi_info_db()
        self.assertIsInstance(r[0], YelpBusiness)

class TestClasses(unittest.TestCase):

    def testCityClass(self):
        c = City("Detroit", "Michigan")
        self.assertEqual(c.__str__(), "Detroit, Michigan")

    def testYelpBusiClass(self):
        b1 = YelpBusiness(name="Dough", rating=3.5, price=4)
        b2 = YelpBusiness(name="Milk")

        self.assertEqual(b1.__str__(), "Dough (Rating: 3.5, Price: $$$$)")
        self.assertEqual(b2.__str__(), "Milk")

class TestProcessing(unittest.TestCase):

    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    cmd = "SELECT b.BusinessName, c.CityName, b.ImageUrl, b.Rating, b.Price, b.Address, b.Lat, b.Lon, b.Id "
    cmd += "FROM Businesses AS b "
    cmd += "JOIN City AS c ON b.CityId=c.Id "
    cmd += "LIMIT 1;"
    result = cur.execute(cmd).fetchall()[0]
    yp = YelpBusiness(*result)

    city = City("New York", "New York", 40.6635, -73.9387)

    def testMapCities(self):
        try:
            map_cities()
        except:
            self.fail()
    
    def testTableOpenTimes(self):
        try:
            table_open_times(self.yp)
        except:
            self.fail()

    def testMapBusinesses(self):
        try:
            map_businesses(self.city)
        except:
            self.fail()
    
    def testPieChart(self):
        try:
            pie_rating_price(self.city)
        except:
            self.fail()
    
    def testBarChart(self):
        try:
            bar_price_same_rating(self.yp)
            bar_rating_same_price(self.yp)
        except:
            self.fail()
    
    def testTableReviews(self):
        try:
            table_reviews(self.yp)
        except:
            self.fail()

unittest.main(verbosity=2)