from __future__ import division, print_function, absolute_import, unicode_literals

from calendar_cli.operation.operation import Operation
from calendar_cli.service import GoogleCalendarService
from mog_commons.io import print_safe


class SummaryOperation(Operation):
    """Print summary of Google Calender"""

    def __init__(self, calendar_id, start_time, duration, credential_path):
        """
        :param calendar_id: string: calendar id
        :param start_time: datetime in tzinfo-aware
        :param duration: timedelta
        :param credential_path: string: path to the credential file
        """
        assert start_time.tzinfo is not None, 'start_time must be tzinfo-aware'

        Operation.__init__(
            self,
            ('calendar_id', calendar_id),
            ('start_time', start_time),
            ('duration', duration),
            ('credential_path', credential_path)
        )

    def run(self):
        service = GoogleCalendarService(self.credential_path)
        events = service.list_events(self.calendar_id, self.start_time, self.start_time + self.duration)
        for e in events:
            print_safe(e.to_short_summary())
        return 0
