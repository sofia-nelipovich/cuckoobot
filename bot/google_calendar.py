from datetime import datetime, timedelta
import httplib2
import googleapiclient
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]

CREDENTIALS_FILE = "service_creds.json"


class GoogleCalendar(object):
    def __init__(self, scopes, service_file):
        self.credentials = ServiceAccountCredentials.from_json_keyfile_name(
            filename=service_file, scopes=scopes
        )
        self.http = self.credentials.authorize(httplib2.Http())
        self.service = googleapiclient.discovery.build(
            "calendar", "v3", credentials=self.credentials
        )

    def get_calendar_list(self):
        return self.service.calendarList().list().execute()

    def add_calendar(self, calendar_id):
        return self.service.calendarList().insert(body={"id": calendar_id}).execute()

    def get_events_for_24(self, calendar_id):
        now = datetime.utcnow().isoformat() + "Z"
        end_of_day = (datetime.utcnow() + timedelta(hours=24)).isoformat() + "Z"

        events_result = (
            self.service.events()
            .list(
                calendarId=calendar_id,
                timeMin=now,
                timeMax=end_of_day,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        events = events_result.get("items", [])

        if not events:
            return {}

        events_dict = {}
        num = 1
        for event in events:
            event_summary = event.get("summary", "Без названия")

            # dateTime - дата+время, date - весь день
            start = event["start"].get("dateTime", event["start"].get("date"))
            end = event["end"].get("dateTime", event["end"].get("date"))
            date_str = datetime.fromisoformat(start).strftime("%d-%m-%Y")
            time_str = f"{datetime.fromisoformat(start).strftime('%H:%M')}-{datetime.fromisoformat(end).strftime('%H:%M')}"
            event_description = event.get("description", "-")

            event_details = (
                f"--------------{num}--------------\n"
                f"Название: {event_summary}\n"
                f"Дата: {date_str}\n"
                f"Время: {time_str}\n"
                f"Описание: {event_description}\n"
            )
            events_dict[event["id"]] = event_details
            num += 1

        return events_dict

    def insert_group_event(self, calendar_id, data):
        start_datetime = datetime.strptime(
            data["date"] + " " + data["start_time"], "%d-%m-%Y %H:%M"
        )
        end_datetime = start_datetime + timedelta(minutes=data["duration"])

        event = {
            "summary": data["title"],
            "start": {
                "dateTime": start_datetime.isoformat(),
                "timeZone": "Europe/Moscow",
            },
            "end": {
                "dateTime": end_datetime.isoformat(),
                "timeZone": "Europe/Moscow",
            },
        }

        if data["description"] != "-":
            event["description"] = data["description"]

        created_event = (
            self.service.events().insert(calendarId=calendar_id, body=event).execute()
        )

        calendar_event_id = created_event.get("id")
        event_link = created_event.get("htmlLink")
        return calendar_event_id, event_link

    def insert_auto_group_event(self, calendar_id, data):
        start_datetime = data["date_and_start_time"]
        end_datetime = start_datetime + timedelta(minutes=int(data["duration"]))

        event = {
            "summary": data["title"],
            "start": {
                "dateTime": start_datetime.isoformat(),
                "timeZone": "Europe/Moscow",
            },
            "end": {
                "dateTime": end_datetime.isoformat(),
                "timeZone": "Europe/Moscow",
            },
        }

        if data["description"] != "-":
            event["description"] = data["description"]

        created_event = (
            self.service.events().insert(calendarId=calendar_id, body=event).execute()
        )

        calendar_event_id = created_event.get("id")
        event_link = created_event.get("htmlLink")
        return calendar_event_id, event_link

    def update_event_name(self, calendar_id, calendar_event_id, new_name):
        event = (
            self.service.events()
            .get(calendarId=calendar_id, eventId=calendar_event_id)
            .execute()
        )
        event["summary"] = new_name
        updated_event = (
            self.service.events()
            .update(calendarId=calendar_id, eventId=calendar_event_id, body=event)
            .execute()
        )
        return updated_event.get("htmlLink")

    def update_event_date(self, calendar_id, calendar_event_id, new_date):
        event = (
            self.service.events()
            .get(calendarId=calendar_id, eventId=calendar_event_id)
            .execute()
        )
        # Calculate the original event duration
        original_start = datetime.fromisoformat(event["start"]["dateTime"])
        original_end = datetime.fromisoformat(event["end"]["dateTime"])
        duration = original_end - original_start

        new_start_datetime = new_date.replace(
            hour=original_start.hour, minute=original_start.minute
        )

        new_end_datetime = new_start_datetime + duration
        event["start"]["dateTime"] = new_start_datetime.isoformat()
        event["end"]["dateTime"] = new_end_datetime.isoformat()

        updated_event = (
            self.service.events()
            .update(calendarId=calendar_id, eventId=calendar_event_id, body=event)
            .execute()
        )
        return updated_event.get("htmlLink")

    def update_event_start(self, calendar_id, calendar_event_id, new_start):
        event = (
            self.service.events()
            .get(calendarId=calendar_id, eventId=calendar_event_id)
            .execute()
        )
        original_start_datetime = datetime.fromisoformat(event["start"]["dateTime"])
        new_start_time = datetime.strptime(new_start, "%H:%M").time()
        new_start_datetime = original_start_datetime.replace(
            hour=new_start_time.hour,
            minute=new_start_time.minute,
            second=0,
            microsecond=0,
        )

        # Calculate the original event duration
        original_end_datetime = datetime.fromisoformat(event["end"]["dateTime"])
        duration = original_end_datetime - original_start_datetime

        new_end_datetime = new_start_datetime + duration
        event["start"]["dateTime"] = new_start_datetime.isoformat()
        event["end"]["dateTime"] = new_end_datetime.isoformat()

        updated_event = (
            self.service.events()
            .update(calendarId=calendar_id, eventId=calendar_event_id, body=event)
            .execute()
        )
        return updated_event.get("htmlLink")

    def update_event_duration(self, calendar_id, calendar_event_id, new_duration):
        event = (
            self.service.events()
            .get(calendarId=calendar_id, eventId=calendar_event_id)
            .execute()
        )

        start_time = datetime.fromisoformat(event["start"]["dateTime"])
        end_time = start_time + timedelta(minutes=new_duration)
        event["end"]["dateTime"] = end_time.isoformat()

        updated_event = (
            self.service.events()
            .update(calendarId=calendar_id, eventId=calendar_event_id, body=event)
            .execute()
        )
        return updated_event.get("htmlLink")

    def update_event_description(self, calendar_id, calendar_event_id, new_description):
        event = (
            self.service.events()
            .get(calendarId=calendar_id, eventId=calendar_event_id)
            .execute()
        )
        if new_description == "-":
            if "description" in event:
                del event["description"]
        else:
            event["description"] = new_description
        updated_event = (
            self.service.events()
            .update(calendarId=calendar_id, eventId=calendar_event_id, body=event)
            .execute()
        )
        return updated_event.get("htmlLink")

    def delete_event(self, calendar_id, calendar_event_id):
        self.service.events().delete(
            calendarId=calendar_id, eventId=calendar_event_id
        ).execute()

    def get_nearest_available_time_slot(self, calendar_ids, required_duration_minutes):
        now = datetime.utcnow()
        end = now + timedelta(hours=48)
        body = {
            "timeMin": now.isoformat() + "Z",
            "timeMax": end.isoformat() + "Z",
            "items": [{"id": id} for id in calendar_ids],
        }

        response = self.service.freebusy().query(body=body).execute()

        time_min = datetime.fromisoformat(response["timeMin"].replace("Z", "+00:00"))
        time_max = datetime.fromisoformat(response["timeMax"].replace("Z", "+00:00"))
        busy_times = {}
        for calendar_id in calendar_ids:
            busy_periods = response["calendars"][calendar_id]["busy"]
            busy_times[calendar_id] = [
                (
                    datetime.fromisoformat(period["start"].replace("Z", "+00:00")),
                    datetime.fromisoformat(period["end"].replace("Z", "+00:00")),
                )
                for period in busy_periods
            ]

        free_times_per_calendar = {
            calendar: find_free_time_slots(busy_periods, time_min, time_max)
            for calendar, busy_periods in busy_times.items()
        }
        common_free_times = list(find_common_free_time_slots(free_times_per_calendar))

        nearest_available_slot = None
        required_duration = timedelta(minutes=required_duration_minutes)
        for start, end in common_free_times:
            if end - start >= required_duration:
                nearest_available_slot = start
                break

        return nearest_available_slot


def find_free_time_slots(busy_periods, start, end):
    free_times = []
    prev_end = start

    for start_busy, end_busy in sorted(busy_periods):
        if prev_end < start_busy:
            free_times.append((prev_end, start_busy))
        prev_end = max(prev_end, end_busy)

    if prev_end < end:
        free_times.append((prev_end, end))

    return free_times


def find_common_free_time_slots(calendars_free_times):
    time_markers = []
    for free_times in calendars_free_times.values():
        for start, end in free_times:
            time_markers.append((start, "start"))
            time_markers.append((end, "end"))

    time_markers.sort(key=lambda x: x[0])

    common_free_times = []
    overlap_count = 0
    current_start = None

    for time, marker in time_markers:
        if marker == "start":
            overlap_count += 1
            if overlap_count == len(calendars_free_times):
                current_start = time
        elif marker == "end":
            if overlap_count == len(calendars_free_times) and current_start is not None:
                common_free_times.append((current_start, time))
            overlap_count -= 1

    return common_free_times
