import requests
import settings
from calgen.models.Calendarific import Calendarific

from calgen.providers.Provider import Provider


class CalendarificProvider(Provider):
    def __init__(self, auth_options):
        super().__init__('Calendarific', auth_options)
        self.api_key = self.auth_options.get('api_key')

    def query(self, country, year, additional_options):
        """ Queries Calendarific, will return either the response data, or None if the api returns garbage data. """
        if country is None:
            raise RuntimeError("Country parameter is missing")
        if year is None:
            raise RuntimeError("Year parameter is missing")

        calendar_type = additional_options.get('calendar_type')

        if calendar_type is None:
            raise RuntimeError("Calendar Type additional option is missing")


        payload = {
            'api_key': self.api_key,
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

    def build(self, country, year, additional_options):
        """ Queries Calendarific, builds, and returns a list of Calendarific models from the queried data. """
        holidays = self.query(country, year, additional_options)
        return [Calendarific(holiday, year, additional_options.get('calendar_type')) for holiday in holidays]