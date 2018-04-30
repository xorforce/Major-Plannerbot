import numpy as np
import re
import textrazor
from collections import Counter
import smtplib
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
from time import time
from pyquery import PyQuery
import requests
# from greetings import greetings as gr

# Time
import parsedatetime
cal = parsedatetime.Calendar()
from datetime import datetime
from timex import tag_time

# Yahoo Weather API
import urllib, json
baseurl = "https://query.yahooapis.com/v1/public/yql?"
yql_query = "select * from weather.forecast where woeid in (select woeid from geo.places(1) where text=\"%s\")"

# Google Places API
google_api = "AIzaSyArwRcZV-dbWsd42y-LGj59267D49E0WXM"
goog_query = "https://maps.googleapis.com/maps/api/place/textsearch/json?"

# Our database of activities
activities_list = json.load(open('list.json'))['all']
activities_keys = activities_list.keys()

# Messages
# greetings = gr.get_greetings()
greetings = ['hey', 'hello', 'what\'s up', 'hi', 'hola', 'konichiwa', 'ola', 'khamma ghani']
gratitudes = ['thanks', 'thank you']
resets = ['stop', 'reset', 'cancel']

import random
intros = [ 'Wow, that sounds fun!', 'Interesting...' ]

# initalize global vars
global complete_input
global processed
global current_data 

cards = [] 

complete_input = ""
processed = { 'time': False, 'location': False, 'activities': False }
current_data = { 'time': None, 'location': None, 'activities': [] }

##### PARSE INPUT #####

def get_time(phrase):
	time_expr = tag_time(phrase)
	if time_expr == 'no time found':
		return None
	else:
		# Convert time expression into numerical time
		time_struct, parse_status = cal.parse(time_expr)
		time = datetime(*time_struct[:3])
		# Make sure time is present or future, not past
		if datetime.now() <= time:
			return { 'time': time, 'time_expr': time_expr }
		else: return None

def get_location(phrase):
	locs_found = []
	formatted_phrase = phrase.title()
	for loc in locs:
		if str(loc) in formatted_phrase:
			locs_found.append(str(loc))
	if len(locs_found) == 0:
		return None
	else:
		loc_counter = Counter(locs_found)
		most_common = loc_counter.most_common(1)[0][0]
		return most_common


def get_activities(phrase):
	activities = []
	for key in activities_keys:
		if key in phrase:
			activities.append(key)
	return activities

##### GET DATA #####

def get_list(data):
	things = []
	# Based on activities
	for activity in data['activities']:
		things.extend(activities_list[activity])
	return list(set(things))

def getTimeStamp(month):
	time_url = "http://www.convert-unix-time.com/api?date=2017-" + month + "-01&timestamp=0"

	print("Collecting Timezone and Timestamp")

	result = urllib.request.urlopen(time_url).read()
	data = json.loads(result)
	timestamp = data['timestamp']

	print("Timezone and timestamp collected")

	return str(timestamp)

def getHistoricalWeather(latitude, longitude, month):
	key = "aeb17ae66d2c7eafcbce2696415e3fce/"
	url = "https://api.darksky.net/forecast/"
	time = getTimeStamp(month)
	latitude = "28.7041"
	longitude = "77.1025"
	final_url = url + key + latitude + "," + longitude + "," + time
	print("Collecting Weather")
	result = urllib.request.urlopen(final_url).read()
	data = json.loads(result)
	print("Collected Weather, parsing..")
	daily = data["daily"]
	temp = daily['data'][0]['temperatureMax']
	tempC = ((temp - 32) * 5) / 9
	print("Done.")
	return tempC

def get_flights(source, destination):
	import time

	opts = Options()
	opts.set_headless()

	browser = Firefox(options=opts)
	browser.get('https://www.google.com')

	search_form = browser.find_element_by_id('lst-ib')
	search_form.send_keys(source + " to " + destination + " flights")
	search_form.submit()
	time.sleep(3)

	pq = PyQuery(browser.page_source)

	tag = pq('.ADuBqd.wZSfG')
	items = str(tag)
	items = items.split("<span class=\"WW7zhf\">")[1:]

	flights = []

	for i in items:
		f = {}
		name = i.split('<')[0]
		time = (str(i).split("<span class=\"hdSHM\">")[1]).split("</span>")[0]
		price = ((str(i).split("<span class=\"JlkRud\">")[1]).split("</span>")[0]).split("from")[1].strip()

		f['name'] = name
		f['time'] = time
		f['price'] = price
		flights.append(f)

	return(flights)
	

def get_weather(location, data_time):
	
	#TODO :- Check for historical weather
	#getHistoricalWeather()
	
	# Convert date to format for Yahoo API
	time = data_time.strftime('%d %b %Y')
	# Get weather conditions for the day - note weather conditions do not go more than a month
	yql_url = baseurl + urllib.parse.urlencode({ 'q': (yql_query % location) }) + "&format=json"
	result = urllib.request.urlopen(yql_url).read()
	json_result = json.loads(result)
	if json_result['query']['count'] != 0:
		weather_data = json_result['query']['results']['channel']['item']['forecast']
		weather = next((item['text'] for item in weather_data if item['date'] == time), None)
		print(weather)
		return(weather)

	else: return None

def get_lat_long(location):
	geocode_api = "965a3c2337904e"
	url = "https://us1.locationiq.org/v1/search.php?key=" + geocode_api + "&q=" + location + "&format=json"

	r = requests.get(url)

	data = json.loads(r.text)
	lat = (data[0]['lat'])
	lng = (data[0]['lon'])
	
	return(lat, lng)

def get_points_of_interest(place):
	req = goog_query + urllib.parse.urlencode({ 'query': 'attractions in ' + place, 'key': google_api })
	print(req)
	result = json.loads(urllib.request.urlopen(req).read())
	points = [interest['name'] for interest in result['results']][0:2] # only first 2
	return points

def analysis(text_input):
	textrazor.api_key = "fa5d3f9828d852fc40a39704d15a2b3ff5a5ec189f14e39a65a40984"

	client = textrazor.TextRazor(extractors=["entities", "topics"])
	response = client.analyze(text_input)

	is_place = False
	
	res = {}

	if(len(response.entities())>0):
		for entity in response.entities():
			if ('Place' in entity.dbpedia_types):
				res['contains_city'] = "true"
				res['city_name'] = entity.matched_text
				
		for fTypes in entity.freebase_types:
			if('sport' in fTypes):

				res['contains_activity'] = "true"
				res['activity_name'] = 'sport'
	
	return(response, res)

##### CREATE RESPONSE #####

def parse_phrase(input_text):

	future_weather = False
	tempC = ""
	lat = ""
	lng = ""
	card = {}
	
	response, res = analysis(input_text)

	# Check if it contains a City
	if("contains_city" in res):
		current_data['location'] = res['city_name']

	# if("true" in res['contains_activity']):
	# 	current_data['activity'] = res['activity_name']

	if "time" not in current_data:
		current_data['time'] = get_time(input_text)

	if "activities" not in current_data:
		current_data['activities'] = get_activities(input_text.lower())

	
	######## Card 1 : Weather Data ########
	month_text = ""
	month = ""

	calender = {"01" : "January", "02" : "February", "03": "March", "04" : "April", "05" : "May", "06" : "June", "07" : "July", "08" : "August", "09":"September", "10":"October", "11" : "Movember", "12":"December"}
	
	print("Building Card 1")
	for e in response.entities():
		if 'Time' in e.dbpedia_types:
			month = str(e.id).split("-")[1]
		else:
			month = "05"

	month_text = calender[month]
	lat, lng = get_lat_long(current_data['location'])
	tempC = getHistoricalWeather(lat, lng, month)
	tempC = str(round(tempC, 2) ) + " °C"
	weather_type = get_weather(current_data['location'], current_data['time']['time'])

	#Create and Append Card
	card["card"] = "1"
	card["title"] = "Weather"
	card["description"] = "Some details about the weather in " + str(current_data['location'])
	card["month"] = month_text
	card["content"] = "The weather is expected to be " + str(weather_type) + " at temperatures around " + str(tempC) + " during the month of " + month_text

	cards.append(card)
	print("Done")

	######## Card 2 : Place of Interest ########
	print("Building Card 2")
	card = {}
	card["card"] = "2"
	card["title"] = "Places to Visit"
	card['description'] = "You should check out some of these places when visiting " + str(current_data['location'])

	places = get_points_of_interest(current_data['location'])
	s = ""
	for p in places:
		s = s + str(p) + " <br/> "

	card["content"] = s 
	cards.append(card)
	print("Done")

	######## Card 3 : Flight Details ########
	print("Building Card 3")
	card = {}
	card["card"] = "3"
	card["title"] = "Flights"
	card["description"] = "Some Flights details that go from Delhi to " + current_data['location']

	flights = get_flights("Delhi", current_data['location'])

	s = ""
	if(len(flights)>0): # WGJK WGJF 
		flights = flights[:3]

		for f in flights:
			s = s + "Name : " + f['name'] + " <br/> "
			s = s + "Flight Time : " + f['time'] + " <br/> "
			s = s + "Price : " + f['price'] + " <br/><br/> "

	card['content'] = s

	cards.append(card)
	print("Done")

	final_data = {"data" : cards}

	print("\n"*3, "Hat Jaayo Saare", "\n"*2)
	print(final_data)

	response = ""

	# Generate response
	if current_data['time'] != None and current_data['location'] != None and not processed['time'] and not processed['location']:
		weather = get_weather(current_data['location'], current_data['time']['time'])
		if weather:
			response += ' The weather is ' + weather + ' in ' + current_data['location'] + ' ' + current_data['time']['time_expr'] + '.'
		response += 'Maybe you could check out ' + ' and '.join(get_points_of_interest(current_data['location']))
		# todo: respond with what clothing to wear
		processed['time'] = True
		processed['location'] = True
	if len(current_data['activities']) > 0:
		response += ' Seems like you\'ve got some things to pack!'
		response += ' You definitely want to pack a ' + ', '.join(get_list(current_data)[:5])

	response = response.strip()
	print(response)

	# Render formatted HTML
	render_this = str(complete_input)

	if current_data['time'] != None:
		render_this = render_this.replace(current_data['time']['time_expr'], 
			"<span style=\"color: #f18973;\">%s</span>" % current_data['time']['time_expr'])
	if current_data['location'] != None:
		render_this = render_this.replace(current_data['location'], 
			"<span style=\"color: #00FF00;\">%s</span>" % current_data['location'])
	if len(current_data['activities']) != 0:
		for activity in current_data['activities']:
			render_this = render_this.replace(activity,  
				"<span style=\"color: #0000FF;\">%s</span>" % activity)

	return response, final_data

##### ENTRY AND EXIT POINT #####

def converse(input_chunk):
	global current_data
	global complete_input
	global processed

	if any(greeting in input_chunk.lower().split() for greeting in greetings):
		return 'Hi there! What can I help you with?', ""

	elif any(gratitude in input_chunk.lower() for gratitude in gratitudes):
		# resets after gratitude expressed
		current_data = { 'time': None, 'location': None, 'activities': [] }
		complete_input = ""
		processed = { 'time': False, 'location': False, 'activities': False }
		return 'No problem!', ""

	elif any(reset in input_chunk.lower() for reset in resets):
		# resets after cancellation
		current_data = { 'time': None, 'location': None, 'activities': [] }
		complete_input = ""
		processed = { 'time': False, 'location': False, 'activities': False }
		return 'Cancelled', ""
	else:
		complete_input = complete_input + input_chunk
		current_data = {"data" : None}
		input_chunk = input_chunk.title()
		return parse_phrase(input_chunk)

# END
