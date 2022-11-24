from datetime import datetime, timedelta
from enum import Enum
import icalendar

''' Note: National sets the calendary `transp` property to opaque. Every other type is transparent. '''
class CalendarTypes(Enum):
    NATIONAL = 0,
    LOCAL = 1,
    RELIGIOUS = 2,
    OBSERVANCE = 3,

'''
Calendar Model

Base class for API / package implementations
Extend and implement from_api to standardize data.

Note: `self.rrule` is mainly used for mixins.
'''
class Calendar(object):
    def __init__(self, data = None, year = 2022):
        self.unique_id = 0
        self.name = ''
        self.description = ''
        self.iso_date = datetime(1970, 1, 1)
        self.calendar_type = ''
        self.year = year
        self.rrule = None

        # If we have data, we can pass it right along
        if data:
            self.from_api(data)

    # By default, we'll just initialize ourselves
    def from_api(self, data):
        self.unique_id = data['unique_id']
        self.name = data['name']
        self.description = data['description']
        self.iso_date = data['iso_date']
        self.calendar_type = data['calendar_type']
        self.rrule = data['rrule']

    def to_ics(self):
        ievt = icalendar.Event()

        data = {
            'uid': "{}-{}".format(self.unique_id, self.year),
            'last-modified': datetime.now(),
            'dtstart': self.iso_date.date(),
            'dtend': self.iso_date.date() + timedelta(days=1),
            'summary': self.name,
            'description': self.description,
            'dtstamp': datetime.now(),
            'class': 'public',
            'transp': 'opaque' if self.calendar_type == CalendarTypes.NATIONAL else 'transparent',
            'categories': ['Holidays'],
            'rrule': self.rrule
        }

        for key, value in data.items():
            if value is None:
                continue
            ievt.add(key, value)

        return ievt
