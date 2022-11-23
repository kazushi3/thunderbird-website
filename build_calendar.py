#!/usr/bin/python
import sys
from datetime import datetime
import os
import time
import icalendar
import requests

# This will correspond with specific api locale sets
from calgen.models.Calendar import CALENDAR_TYPES
from calgen.models.Calendarific import Calendarific

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
                formatted_holidays = [Calendarific(holiday, year, CALENDAR_TYPES['NATIONAL']) for holiday in holidays]

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