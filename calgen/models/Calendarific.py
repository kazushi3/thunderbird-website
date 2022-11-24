
from datetime import datetime
from calgen.models.Calendar import Calendar, CalendarTypes

'''
API Documentation available at: https://calendarific.com/api-documentation

Instantiate this calendar api class to parse Calendarific api data
'''
class Calendarific(Calendar):
    def __init__(self, data = None, year = 2022, calendar_type = CalendarTypes.NATIONAL):
        super(Calendarific, self).__init__(data, year)
        self.calendar_type = calendar_type

    def from_api(self, data):
        self.unique_id = data['urlid']
        self.name = data['name']
        self.description = data['description']
        self.iso_date = datetime.fromisoformat(data['date']['iso'])

        return self