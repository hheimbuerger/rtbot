import urllib, urllib2
import httplib
import json
import pytz
import datetime
import sys

def build_geoname_query_url(query):
	# PCLI=countries, PPL=cities, ADM1=states, see http://www.geonames.org/export/codes.html
	return 'http://ws.geonames.org/search?name=%s&featureCode=PPL&featureCode=PCLI&featureCode=ADM1&type=json' % urllib.quote_plus(query)

def build_timezone_query_url(lat, lng):
	return 'http://ws.geonames.org/timezoneJSON?lat=%s&lng=%s' % (lat, lng)

if len(sys.argv) <= 1:
	print "Syntax: NewClock.py <city/state/country>"
	sys.exit(1)

response = urllib2.urlopen(build_geoname_query_url(sys.argv[1]), timeout=10000)
if response and response.getcode() == httplib.OK:
	body = json.load(response)
	totalResultsCount = body['totalResultsCount']
	if totalResultsCount > 0:
		bestMatch = body['geonames'][0]
		lat = bestMatch['lat']
		lng = bestMatch['lng']
		response = urllib2.urlopen(build_timezone_query_url(lat, lng), timeout=10000)
		if response and response.getcode() == httplib.OK:
			body = json.load(response)
			timezoneId = body['timezoneId']
			timezone = pytz.timezone(timezoneId)
			fmt = '%Y-%m-%d %H:%M:%S %Z/UTC%z'
			time = datetime.datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(timezone).strftime(fmt)
			print '%s (%s): %s (%i alternative results)' % (bestMatch['name'], bestMatch['toponymName'], time, totalResultsCount-1)
		else:
			raise Exception('Timezone lookup failed: %i' % response.getcode())
	else:
		raise Exception('No results')
else:
	raise Exception('Name lookup failed: %i' % response.getcode())
