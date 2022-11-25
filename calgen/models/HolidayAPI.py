from datetime import datetime
from calgen.models.Calendar import Calendar, CalendarTypes

class HolidayAPI(Calendar):
    """
    API Documentation available at: https://holidayapi.com/docs

    Instantiate this calendar api class to parse HolidayAPI data
    """
    def from_api(self, data):
        self.unique_id = data['uuid']
        self.name = data['name']
        self.iso_date = datetime.fromisoformat(data['date'])
        self.calendar_type = CalendarTypes.NATIONAL if bool(data['public']) else CalendarTypes.OBSERVANCE
