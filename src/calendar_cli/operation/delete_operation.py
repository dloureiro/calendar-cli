from __future__ import division, print_function, absolute_import, unicode_literals

from calendar_cli.operation.operation import Operation
from calendar_cli.service import GoogleCalendarService
from calendar_cli.i18n import MSG_EVENT_DELETED
from mog_commons.io import print_safe


class DeleteOperation(Operation):
    """Delete an event to Google Calendar"""

    def __init__(self, calendar_id, event_id, credential_path):
        """
        :param calendar_id: string: calendar id
        :param event_id: string: event id
        :param credential_path: string: path to the credential file
        """
        Operation.__init__(
            self,
            ('calendar_id', calendar_id),
            ('event_id', event_id),
            ('credential_path', credential_path)
        )

    def run(self):
        service = GoogleCalendarService(self.credential_path)
        service.delete_event(self.calendar_id, self.event_id, self.credential_path)
        print_safe(MSG_EVENT_DELETED % {'event': self.event_id})
