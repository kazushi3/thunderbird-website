from datetime import datetime
from calgen.models.Calendar import Calendar, CalendarTypes

class Calendarific(Calendar):
    """
    API Documentation available at: https://calendarific.com/api-documentation

    Instantiate this calendar api class to parse Calendarific api data
    """
    def __init__(self, data = None, year = 2022, calendar_type = CalendarTypes.NATIONAL):
        super(Calendarific, self).__init__(data, year)
        self.calendar_type = calendar_type

    def from_api(self, data):
        date = data.get('date')
        iso_date = None
        if date is not None:
            iso_date = datetime.fromisoformat(date.get('iso'))

        self.unique_id = data.get('urlid')
        self.name = data.get('name')
        self.description = data.get('description')
        self.iso_date = iso_date

        return self