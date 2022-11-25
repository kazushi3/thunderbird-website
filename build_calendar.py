#!/usr/bin/python
import json
import sys
from datetime import datetime
import os
import time
import icalendar
import requests
import settings

from calgen.mixins import GlobalHolidays
from calgen.models.Calendar import CalendarTypes
from calgen.models.Calendarific import Calendarific

class CountryNotSupportedException(Exception):
    def __init__(self, country):
        self.country = country


def query_calendarific(api_key, country, year, calendar_type):
    if country not in settings.CALENDAR_LOCALES:
        raise CountryNotSupportedException(country)

    payload = {
        'api_key': api_key,
        'country': country,
        'year': year,
        'type': calendar_type
    }

    response = requests.get(settings.CALENDARIFIC_API_URL, params=payload)
    response.raise_for_status()

    try:
        return response.json()['response']['holidays']
    except KeyError:
        print("Malformed response for {}, {}, {}".format(country, year, calendar_type))
        return None

def mixin_events(ical, locale):
    # Global mix ins
    for event in GlobalHolidays.MIXINS:
        ical.add_component(event.to_ics())

    # Locale specific mix ins
    # ...

def build_calendars(locales):
    try:
        api_key = os.environ['CALENDARIFIC_API_KEY']
    except KeyError:
        sys.exit("No `CALENDARIFIC_API_KEY` defined.")

    try:
        is_free_tier = os.environ['os.CALENDARIFIC_IS_FREE_TIER'].lower() == 'true'
    except KeyError:
        is_free_tier = True

    years_to_generate = 3
    current_year = datetime.now().year
    date_span = "{}-{}".format(current_year, current_year + years_to_generate)

    calendar_metadata = []

    print("Querying calendar data from provider")

    for locale, country_name in locales.items():
        ical = icalendar.Calendar()
        ical.add('prodid', '-//Mozilla.org/NONSGML Mozilla Calendar V1.1//EN')
        ical.add('version', '2.0')

        mixin_events(ical, locale)

        # Wait 1 second due to free api restrictions
        if is_free_tier:
            time.sleep(1)

        for i in range(0, years_to_generate):
            year = current_year + i

            for calendar_type in [CalendarTypes.NATIONAL, CalendarTypes.OBSERVANCE]:
                try:
                    holidays = query_calendarific(api_key, locale, year, calendar_type.value)
                    formatted_holidays = [Calendarific(holiday, year, calendar_type) for holiday in holidays]

                    for holiday in formatted_holidays:
                        ical.add_component(holiday.to_ics())
                except requests.HTTPError as err:
                    response = err.response.json()

                    # Generic error message
                    error_response = "{}: {}. ".format(err.response.status_code, err.response.reason)

                    # If we have the error_detail key, append that.
                    if response['meta'].get('error_detail'):
                        error_response += response['meta'].get('error_detail')

                    # Known errors:
                    # Too many requests, upgrade required are API limit reached.
                    # Unauthorized is malformed or bad API key.
                    sys.exit(error_response)
                except CountryNotSupportedException as err:
                    sys.exit("Country code {} is not a supported locale.".format(err.country))

        calendar_name = '{}Holidays.ics'.format(country_name.replace(' ', ''))

        calendar_metadata.append({
            'country': country_name,
            'filename': "autogen/{}".format(calendar_name),
            'datespan': date_span,
            'authors': 'Autogenerator'
        })

        with open('media/caldata/autogen/{}'.format(calendar_name), 'wb') as fh:
            fh.write(ical.to_ical())


    print("Re-building calendars.json")
    with open('media/caldata/autogen/calendars.json', 'w') as fh:
        fh.write(json.dumps(calendar_metadata, indent=2))
