from datetime import datetime, timedelta

# Generic transformer class, extend to implement api input, by default contains ics output
import icalendar

CALENDAR_TYPES = {
    'NATIONAL': 'national',
    'LOCAL': 'local',
    'RELIGIOUS': 'religious',
    'OBSERVANCE': 'observance'
}

class Calendar(object):
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
            'dtstart': self.iso_date + timedelta(hours=8),
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
