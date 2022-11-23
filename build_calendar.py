#!/usr/bin/python
import sys
from datetime import datetime, timedelta
import json
import os
import time
import icalendar
import requests

# This will correspond with specific api locale sets
LOCALES = [
    'CA',
    'US'
]

class CountryNotSupportedException(Exception):
    def __init__(self, country):
        self.country = country

API_URL = "https://calendarific.com/api/v2/holidays"

def query_calendarific(api_key, country, year, calendar_type):
    if country not in LOCALES:
        raise CountryNotSupportedException(country)

    payload = {
        'api_key': api_key,
        'country': country,
        'year': year,
        'type': calendar_type
    }

    response = requests.get(API_URL, params=payload)

    response.raise_for_status()

    try:
        return response.json()['response']['holidays']
    except KeyError:
        print("Bad response from {}, {}, {}".format(country, year, calendar_type))
        return None


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
        self.iso_date = datetime(1970, 1, 1)
        self.calendar_type = ''
        self.year = year

        # If we have data, we can pass it right along
        if data:
            self.from_api(data)

    def from_api(self, data):
        raise NotImplementedError()

    def to_ics(self):
        ievt = icalendar.Event()

        data = {
            'uid': "{}-{}".format(self.unique_id, self.year),
            'last-modified': datetime.now(),
            'dtstart': self.iso_date,
            'dtend': self.iso_date + timedelta(days=1),
            'summary': self.name,
            'description': self.description,
            'dtstamp': datetime.now(),
            'class': 'public',
            'transp': 'opaque' if self.calendar_type == CALENDAR_TYPES['NATIONAL'] else 'transparent',
            'categories': 'Holidays',
        }

        for key, value in data.items():
            ievt.add(key, value)

        return ievt


# See: https://calendarific.com/api-documentation
class CalendarificTransformer(CalendarTransformer):
    def __init__(self, data = None, year = 2022, calendar_type = CALENDAR_TYPES['NATIONAL']):
        super(CalendarificTransformer, self).__init__(data, year)
        self.calendar_type = calendar_type

    def from_api(self, data):
        self.unique_id = data['urlid']
        self.name = data['name']
        self.description = data['description'],
        self.iso_date = datetime.fromisoformat(data['date']['iso'])

        return self

# See: https://holidayapi.com/docs
class HolidayAPITransformer(CalendarTransformer):
    def from_api(self, data):
        self.unique_id = data['uuid']
        self.name = data['name']
        self.iso_date = datetime.fromisoformat(data['date'])
        self.calendar_type = CALENDAR_TYPES['NATIONAL'] if bool(data['public']) else CALENDAR_TYPES['OBSERVANCE']

def build_calendars():

    try:
        api_key = os.environ['CALENDARIFIC_API_KEY']
    except KeyError:
        sys.exit("No `CALENDARIFIC_API_KEY` defined.")

    try:
        api_tier = os.environ['os.CALENDARIFIC_API_TIER']
    except KeyError:
        api_tier = 'free'

    years_to_generate = 1 # 3
    current_year = datetime.now().year

    for locale in LOCALES:
        ical = icalendar.Calendar()
        ical.add('prodid', '-//Mozilla.org/NONSGML Mozilla Calendar V1.1//EN')
        ical.add('version', '2.0')

        for i in range(0, years_to_generate):
            year = current_year + i
            try:
                holidays = query_calendarific(api_key, locale, year, CALENDAR_TYPES['NATIONAL'])
                formatted_holidays = [CalendarificTransformer(holiday, year, CALENDAR_TYPES['NATIONAL']) for holiday
                                      in holidays]

                for holiday in formatted_holidays:
                    ical.add_component(holiday.to_ics())

            except requests.HTTPError as err:
                match err.response.status_code:
                    # API limit reached
                    case requests.status_codes.codes.too_many_requests:
                        print("API limit reached, breaking from loop")
                        break
                    # Bad API key
                    case requests.status_codes.codes.unauthorized:
                        print("Bad or missing API key")
                        break
                    case _:
                        print("Error {}".format(err.response.status_code))
                        continue

        # Wait 1 second due to free api restrictions
        if api_tier == 'free':
            time.sleep(1)

        with open('media/caldata/autogen/{}Holidays.ics'.format(locale), 'wb') as fh:
            fh.write(ical.to_ical())

build_calendars()