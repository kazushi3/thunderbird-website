
from datetime import datetime
from calgen.models.Calendar import Calendar, CALENDAR_TYPES

'''
API Documentation available at: https://holidayapi.com/docs

Instantiate this calendar api class to parse HolidayAPI data
'''
class HolidayAPI(Calendar):
    def from_api(self, data):
        self.unique_id = data['uuid']
        self.name = data['name']
        self.iso_date = datetime.fromisoformat(data['date'])
        self.calendar_type = CALENDAR_TYPES['NATIONAL'] if bool(data['public']) else CALENDAR_TYPES['OBSERVANCE']
