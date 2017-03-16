from __future__ import division, print_function, absolute_import, unicode_literals

import re
from datetime import datetime, timedelta
from tzlocal import get_localzone
from calendar_cli.model import EventTime, Event
from calendar_cli.operation import HelpOperation, SummaryOperation, CreateOperation, SetupOperation
from calendar_cli.operation.delete_operation import DeleteOperation
from calendar_cli.setting import arg_parser
from mog_commons.case_class import CaseClass
from mog_commons.functional import oget
from mog_commons.string import to_unicode


class Setting(CaseClass):
    """Manages all settings."""

    DEFAULT_CREATE_DURATION = timedelta(minutes=15)

    def __init__(self, operation=None, now=None, debug=None):
        CaseClass.__init__(self,
                           ('operation', operation),
                           ('now', now or get_localzone().localize(datetime.now())),
                           ('debug', debug)
                           )

    @staticmethod
    def _parse_date(s, now):
        if s is None:
            return None
        try:
            # YYYYmmdd
            if re.compile(r"""^[0-9]{8}$""").match(s):
                return datetime.strptime(s, '%Y%m%d').date()

            # mm/dd or mm-dd (complete with the current year)
            m = re.compile(r"""^([0-9]{1,2})[/-]([0-9]{1,2})$""").match(s)
            if m:
                mm, dd = m.group(1), m.group(2)
                return datetime.strptime(mm.rjust(2, '0') + dd.rjust(2, '0'), '%m%d').date().replace(year=now.year)

            # YYYY/MM/DD or YYYY-MM-DD
            m = re.compile(r"""^([0-9]{4})[/-]([0-9]{1,2})[/-]([0-9]{1,2})$""").match(s)
            if m:
                yyyy, mm, dd = m.group(1), m.group(2), m.group(3)
                return datetime.strptime(yyyy + mm.rjust(2, '0') + dd.rjust(2, '0'), '%Y%m%d').date()

            # MM/DD/YYYY or MM-DD-YYYY
            m = re.compile(r"""^([0-9]{1,2})[/-]([0-9]{1,2})[/-]([0-9]{4})$""").match(s)
            if m:
                mm, dd, yyyy = m.group(1), m.group(2), m.group(3)
                return datetime.strptime(yyyy + mm.rjust(2, '0') + dd.rjust(2, '0'), '%Y%m%d').date()

            raise ValueError()
        except ValueError:
            raise ValueError('Failed to parse --date option: %s' % s)

    @staticmethod
    def _parse_time(s):
        if s is None:
            return None
        try:
            # HHMM
            if re.compile(r"""^[0-9]{4}$""").match(s):
                return datetime.strptime(s, '%H%M').time()

            # HH:MM
            m = re.compile(r"""^([0-9]{1,2}):([0-9]{1,2})$""").match(s)
            if m:
                hh, mm = m.group(1), m.group(2)
                return datetime.strptime(hh.rjust(2, '0') + mm.rjust(2, '0'), '%H%M').time()

            raise ValueError()
        except ValueError:
            raise ValueError('Failed to parse --start or --end option: %s' % s)

    @classmethod
    def _parse_time_range(cls, start_date, end_date,start_time, end_time, now):
        parsed_end_date = cls._parse_date(end_date,now)
        parsed_start_date = cls._parse_date(start_date, now)
        parsed_start_time = cls._parse_time(start_time)
        parsed_end_time = cls._parse_time(end_time)

        if parsed_start_date is None:
            if parsed_start_time is None:
                raise ValueError('Failed to create event: --start options is not well formatted.')
            # set date today or tomorrow
            dt = now.date()
            if (parsed_start_time.hour, parsed_start_time.minute) < (now.hour, now.minute):
                dt += timedelta(days=1)
        else:
            if parsed_start_time is None:
                if parsed_end_time is not None:
                    raise ValueError('Failed to create event: end TIME is set but start time is missing.')
                # all-day event
                t_start = get_localzone().localize(datetime(parsed_start_date.year, parsed_start_date.month, parsed_start_date.day))
                t_end = get_localzone().localize(datetime(parsed_end_date.year, parsed_end_date.month, parsed_end_date.day))
                return EventTime(False, t_start), EventTime(False, t_end)
            dt = parsed_start_date

        # set start and end event time
        start = get_localzone().localize(datetime.combine(dt, parsed_start_time))

        if parsed_end_time is None:
            end = start + cls.DEFAULT_CREATE_DURATION
        else:
            end = get_localzone().localize(datetime.combine(parsed_end_date, parsed_end_time))
            # if parsed_start_time > parsed_end_time:
            #     end += timedelta(days=1)
        return EventTime(True, start), EventTime(True, end)

    def parse_args(self, argv):
        assert self.now is not None

        # decode all args as utf-8
        option, args = arg_parser.parser.parse_args([to_unicode(a, errors='ignore') for a in argv[1:]])

        try:
            if not args:
                # summary
                date_time = option.start_date.split(" ")
                input_date = date_time[0]
                input_time = date_time[1]
                dt = oget(self._parse_date(input_date, self.now), self.now.date())
                start_time = get_localzone().localize(datetime(dt.year, dt.month, dt.day))

                fmt = (option.format or
                       (arg_parser.DEFAULT_FORMAT if option.days == 0 else arg_parser.DEFAULT_FORMAT_DAYS))

                if option.days == 0:
                    # show events on one day
                    duration = timedelta(days=1)
                elif option.days < 0:
                    # show events from past several days
                    duration = timedelta(days=-option.days + 1)
                    start_time -= timedelta(days=-option.days)
                else:
                    # show events from several days from today
                    duration = timedelta(days=option.days + 1)

                operation = SummaryOperation(option.calendar, start_time, duration,
                                             option.credential, fmt, option.separator)
            elif args[0] == 'setup' and len(args) == 2:
                # setup
                operation = SetupOperation(args[1], option.credential, option.read_only, option.no_browser)
            elif args[0] == 'create' and len(args) >= 2:
                # create
                summary = ' '.join(args[1:])
                start, end = self._parse_time_range(option.start_date, option.end_date, option.start_time, option.end_time, self.now)

                ev = Event(start, end, summary, location=option.location)
                operation = CreateOperation(option.calendar, ev, option.credential)
            elif args[0] == 'delete' and len(args) >= 2:
                # delete
                eventID = args[1]
                operation = DeleteOperation(option.calendar, eventID, option.credential)
            else:
                # help
                operation = HelpOperation()
        except Exception as e:
            # parse error
            operation = HelpOperation(e)
            if option.debug:
                import traceback
                traceback.print_exc()
                print()

        return self.copy(operation=operation, debug=option.debug)
