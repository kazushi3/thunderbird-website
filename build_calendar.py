#!/usr/bin/python
import datetime
import json
import time

import requests
import settings_private

# This will correspond with specific api locale sets
LOCALES = [
    'CA',
    'US'
]

# General exception
class APIException(Exception):
    def __init__(self, status_code):
        self.status_code = status_code

class CountryNotSupportedException(Exception):
    def __init__(self, country):
        self.country = country

class RateLimitException(Exception):
    pass
class AuthException(Exception):
    pass

API_URL = "https://calendarific.com/api/v2/holidays"

def quick_cache_put(data, locale, year):
    fh = open('api_cache_%s_%s.txt' % (locale, year), 'w')
    fh.write(json.dumps(data))
    fh.close()

def quick_cache_get(locale, year):
    try:
        fh = open('api_cache_%s_%s.txt' % (locale, year), 'r')
        data = fh.read()
        fh.close()
    except IOError:
        return None

    return json.loads(data)

def query_calendarific(api_key, country, year, calendar_type):
    if country not in LOCALES:
        raise CountryNotSupportedException(country)

    cached_json = quick_cache_get(country, year)
    if cached_json is not None:
        return cached_json['response']['holidays']

    url = [
        API_URL,
        '?',
        'api_key=%s' % api_key,
        'country=%s' % country,
        'year=%s' % year,
        'type=%s' % calendar_type
    ]
    url = "&".join(x for x in url)

    #print("Requesting: ", url)

    response = requests.get(url)

    # We only really care about auth and rate limit, so fall back to the generic api exception if we're hit with anything else
    if response.status_code == 401:
        raise AuthException()
    if response.status_code == 429:
        raise RateLimitException()
    elif response.status_code != 200:
        raise APIException(response.status_code)

    quick_cache_put(response.json(), country, year)

    return response.json()['response']['holidays']


# Lifted from calendarific api - May not be needed
CALENDAR_TYPES = {
    'NATIONAL': 'national',
    'LOCAL': 'local',
    'RELIGIOUS': 'religious',
    'OBSERVANCE': 'observance'
}

# Generic transformer class, extend to implement api input, by default contains ics output
class CalendarTransformer(object):
    def __init__(self, data = None, year = 2022):
        self.unique_id = 0
        self.name = ''
        self.description = ''
        self.iso_date = self.iso_date_to_date_obj('1970-01-01')
        self.calendar_type = ''
        self.year = year

        # If we have data, we can pass it right along
        if data:
            self.from_api(data)


    # TODO: See if there's already a date utils for python 2
    @staticmethod
    def iso_date_to_date_obj(date):
        date_parts = date.split('-')
        return datetime.datetime(int(date_parts[0]), int(date_parts[1]), int(date_parts[2]))

    @staticmethod
    def date_to_caldate(date):
        return date.strftime('%Y%m%dT%H%M%SZ')

    @staticmethod
    def date_to_isodate(date):
        return date.strftime('%Y%m%d')

    def from_api(self, data):
        raise NotImplementedError()

    def to_ics(self):
        # FIXME: Quite messy - use icalendar package instead
        return """BEGIN:VEVENT
UID:%s
LAST-MODIFIED:%s
DTSTART;VALUE=DATE:%s
DTEND;VALUE=DATE:%s
SUMMARY:%s
DESCRIPTION:%s
DTSTAMP:%s
CLASS:PUBLIC
TRANSP:TRANSPARENT
CATEGORIES:Holidays
END:VEVENT
""" % (
            "%s-%s" % (self.unique_id, self.year),
            self.date_to_caldate(datetime.datetime.now()),
            self.date_to_isodate(self.iso_date),
            self.date_to_isodate(self.iso_date + datetime.timedelta(days=1)),
            self.name,
            self.description[0],
            self.date_to_caldate(self.iso_date)
        )


# See: https://calendarific.com/api-documentation
class CalendarificTransformer(CalendarTransformer):
    def __init__(self, data = None, year = 2022, calendar_type = CALENDAR_TYPES['NATIONAL']):
        super(CalendarificTransformer, self).__init__(data, year)
        self.calendar_type = calendar_type

    def from_api(self, data):
        self.unique_id = data['urlid']
        self.name = data['name']
        self.description = data['description'],
        self.iso_date = self.iso_date_to_date_obj(data['date']['iso'])

        return self

# See: https://holidayapi.com/docs
class HolidayAPITransformer(CalendarTransformer):
    def from_api(self, data):
        self.unique_id = data['uuid']
        self.name = data['name']
        self.iso_date = self.iso_date_to_date_obj(data['date'])
        self.calendar_type = CALENDAR_TYPES['NATIONAL'] if bool(data['public']) else CALENDAR_TYPES['OBSERVANCE']

def build_calendars():
    for locale in LOCALES:
        fh = open('%sHolidays.ics' % locale, 'w')

        fh.write("""BEGIN:VCALENDAR
PRODID:-//Mozilla.org/NONSGML Mozilla Calendar V1.1//EN
VERSION:2.0
""")

        years_to_generate = [2022, 2023]

        for year in years_to_generate:
            holidays = query_calendarific(settings_private.CALENDARIFIC_API_KEY, locale, year, CALENDAR_TYPES['NATIONAL'])
            formatted_holidays = [ CalendarificTransformer(holiday, year, CALENDAR_TYPES['NATIONAL']) for holiday in holidays  ]
            ics_files = [ holiday.to_ics() for holiday in formatted_holidays ]

            for ics in ics_files:
                fh.write(ics)

            # Wait 1 second due to api restrictions
            time.sleep(1)

        fh.write('END:VCALENDAR')

        fh.close()
