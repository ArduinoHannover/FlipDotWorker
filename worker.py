#!/usr/bin/python2.7

import urllib, urllib2, subprocess, os, string, json, re, sys
from datetime import date, datetime, time, timedelta
from sunrise import sun
from time import sleep
from PIL import Image, ImageFont, ImageDraw

ip = '192.168.0.193'
width = 112
height = 16
stationBoardFrom=time(hour=22,minute=0,second=0)
stationBoardTo=time(hour=8,minute=0,second=0)

s = sun(lat=52.37,long=9.72)
lightIs = False
black = (0,0,0)
yellow = (255,255,0)

debug = False
if len(sys.argv) >= 2:
	debug = (sys.argv[1] == "debug")

bigfont = ImageFont.truetype("5x7.ttf", 16)
digfont = ImageFont.truetype("4x7.ttf", 7)
font =  ImageFont.truetype("5x7.ttf", 8)

def isDarkOutside():
	return s.sunrise() > datetime.now().time() or datetime.now().time() > s.sunset()

def URLRequest(url, params, method="GET"):
	try:
		params = urllib.urlencode(params)
		if debug:
			print(url+'?'+params)
		if method == "POST":
			f = urllib2.urlopen(url, params, timeout=10)
		else:
			f = urllib2.urlopen(url+'?'+params, None, timeout=10)
		if debug:
			print("done.")
		return f.read()
	except Exception, e:
		if debug:
			print("Exception while fetching: ",e)
		return False

def doorIsOpen():
	return URLRequest("http://leinelab.net/ampel/status.txt", {}) == "OpenLab"

def getTimeImage():
	now = datetime.now()
	img = Image.new('RGB', (width, height))
	draw = ImageDraw.Draw(img)
	tstr = now.strftime("%H:%M:%S")
	for i in range(0,8):
		w, h = bigfont.getsize(tstr[i])
		draw.text((16+i*10+(10-w)/2, 1), tstr[i], yellow, font=bigfont)
	if debug:
		img.save('sample-out.png')
	return img
	

def getStationImage(stationId):
	now = datetime.now()
	req_for = (now + timedelta(0,60*5))
	req = URLRequest("http://pebble.sndstrm.de/fahrplan/stationBoard.php", {"ext_id":stationId,"max":10,"date":req_for.strftime("%d.%m.%y"),"time":req_for.strftime("%H:%M")})
	if req == False:
		return False
	depatures = json.loads(req)
	station = {"in":list(), "out":list()}
	for depature in depatures["Journey"]:
		depOb = {}
		dep = depature["attributes"]
		dest = dep["targetLoc"]
		d_time = datetime.strptime(dep["fpDate"]+" "+dep["fpTime"], '%d.%m.%y %H:%M')
		depOb["line"] = re.search('[0-9]+',dep["prod"]).group(0)
		depOb["in"] = int((d_time-now).total_seconds()/60)
		if re.search('Aegidientorplatz', dest):
			depOb["destination"] = "Aegi"
			station["in"].append(depOb)
		elif re.search('Fasanenkrug', dest):
			depOb["destination"] = "Fa.krug"
			station["in"].append(depOb)
		elif re.search('Hannover ZOB', dest):
			depOb["destination"] = "ZOB"
			station["in"].append(depOb)
		elif re.search('Altwarmb', dest):
			depOb["destination"] = "Altwb."
			station["in"].append(depOb)
		elif re.search('Pattensen ZOB', dest):
			depOb["destination"] = "Pat ZOB"
			station["out"].append(depOb)
		elif re.search('Pattensen/Briefzentrum', dest):
			depOb["destination"] = "Pat BZ"
			station["out"].append(depOb)
		elif re.search('Gehrden', dest):
			depOb["destination"] = "Gehrd."
			station["out"].append(depOb)
		elif re.search('Dedensen', dest):
			depOb["destination"] = "Deden."
			station["out"].append(depOb)
		elif re.search('Wettbergen', dest):
			depOb["destination"] = "Wettb."
			station["out"].append(depOb)
		elif re.search('Lohnde', dest):
			depOb["destination"] = "Lohnde"
			station["in"].append(depOb)
		elif re.search('Empelde', dest):
			depOb["destination"] = "Empelde"
			station["in"].append(depOb)
		elif re.search('Wallensteinstra', dest):
			depOb["destination"] = "Walle."
			station["in"].append(depOb)
		elif re.search('Ahlem', dest):
			depOb["destination"] = "Ahlem"
			station["out"].append(depOb)
		else:
			depOb["destination"] = dest[:6]
			station["out"].append(depOb)
	if debug:
		print station
	img = Image.new('RGB', (width, height))
	draw = ImageDraw.Draw(img)
	draw.rectangle(((0,0),(12,16)), fill=yellow)
	draw.text((1, 1), station["in"][0]["line"].rjust(3, " "), black, font=digfont)
	draw.text((14, 0), station["in"][0]["destination"], yellow, font=font)
	draw.text((1, 9), station["in"][1]["line"].rjust(3, " "), black, font=digfont)
	draw.text((14, 8), station["in"][1]["destination"], yellow, font=font)

	draw.rectangle(((46,0),(69,16)), fill=yellow)
	draw.line((56,0,56,15), fill=black)
	draw.line((55,0,55,15), fill=black)

	draw.text((47, 1), str(station["in"][0]["in"]).rjust(2, "0"), black, font=digfont)
	draw.text((47, 9), str(station["in"][1]["in"]).rjust(2, "0"), black, font=digfont)

	draw.text((1 +57, 1), station["out"][0]["line"].rjust(3, " "), black, font=digfont)
	draw.text((14+57, 0), station["out"][0]["destination"],  yellow, font=font)
	draw.text((1 +57, 9), station["out"][1]["line"].rjust(3, " "), black, font=digfont)
	draw.text((14+57, 8), station["out"][1]["destination"],  yellow, font=font)

	draw.rectangle(((103,0),(112,16)), fill=yellow)
	draw.text((47+57, 1), str(station["out"][0]["in"]).rjust(2, "0"), black, font=digfont)
	draw.text((47+57, 9), str(station["out"][1]["in"]).rjust(2, "0"), black, font=digfont)
	if debug:
		img.save('sample-out.png')
	return img

def pushImage(img):
	if img != False:
		bitmap = ""
		for pixel in list(img.getdata()):
			bitmap += "0" if pixel == black else "1"
		URLRequest('http://'+ip+'/api', {'drawBitmap':bitmap})

if debug:
	getStationImage("000638934")
	getTimeImage()

while True:
	if lightIs != isDarkOutside():
		URLRequest('http://'+ip+'/api', {'setBacklight':1 if isDarkOutside() else 0})
		lightIs = not lightIs
	if (
	datetime.today().weekday() in [2,4,5] and datetime.now().time() > stationBoardFrom or
	datetime.today().weekday() in [3,5,6] and datetime.now().time() < stationBoardTo
	):
		for i in range[0:5]:
			if i == 0:
				show_for = datetime.now()+timedelta(0,10)
				while datetime.now() <= show_for:
					st = datetime.now()
					pushImage(getTimeImage())
					try:
						sleep(1-(datetime.now()-st).total_seconds())
					except Exception:
						pass
			elif i == 1:
				URLRequest('http://'+ip+'/api', {'fillScreen':0,'setCursor':1,'x':0,'y':0,'print':"Abfahrten von\nGoetheplatz"})
				sleep(5)
			elif i == 2:
				pushImage(getStationImage("000638934"))
				sleep(15)
			elif i == 3:
				URLRequest('http://'+ip+'/api', {'fillScreen':0,'setCursor':1,'x':0,'y':0,'print':"Abfahrten von\nSchwarzer Baer"})
				sleep(5)
			elif i == 4:
				pushImage(getStationImage("000638551"))
				sleep(15)
	else:
		URLRequest('http://'+ip+'/api', {'fillScreen':0,'setCursor':1,'x':0,'y':0,'print':"LeineLab ist\n"+("offen" if doorIsOpen() else "geschlossen")})
		sleep(50)
		show_for = datetime.now()+timedelta(0,10)
		while datetime.now() <= show_for:
			st = datetime.now()
			pushImage(getTimeImage())
			try:
				sleep(1-(datetime.now()-st).total_seconds())
			except Exception:
				pass
