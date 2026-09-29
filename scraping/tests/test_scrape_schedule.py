import importlib.util
import unittest
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo


MODULE_PATH = Path(__file__).resolve().parents[1] / "scrape_schedule.py"
SPEC = importlib.util.spec_from_file_location("scrape_schedule", MODULE_PATH)
assert SPEC and SPEC.loader
scraper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(scraper)

CENTRAL = ZoneInfo("America/Chicago")


def booking(event, room, start, end, building="Cooke Hall"):
    return {
        "eventName": event,
        "buildingDescription": building,
        "roomDescription": room,
        "dateTimeStart": start,
        "dateTimeEnd": end,
    }


class WeekBoundsTests(unittest.TestCase):
    def test_sunday_stays_in_preceding_monday_week(self):
        monday, sunday = scraper.week_bounds(datetime(2026, 10, 4, 18, tzinfo=CENTRAL))
        self.assertEqual(monday, date(2026, 9, 28))
        self.assertEqual(sunday, date(2026, 10, 4))

    def test_year_boundary(self):
        monday, sunday = scraper.week_bounds(datetime(2027, 1, 1, 8, tzinfo=CENTRAL))
        self.assertEqual(monday, date(2026, 12, 28))
        self.assertEqual(sunday, date(2027, 1, 3))


class NormalizationTests(unittest.TestCase):
    def test_punctuation_and_case_normalization(self):
        item = booking(
            "OPEN PLAY- Badminton",
            "Cooke 325",
            "2026-09-28T05:45:00-05:00",
            "2026-09-28T16:30:00-05:00",
        )
        self.assertTrue(scraper.is_target_booking(item))

    def test_unrelated_room_or_activity_is_rejected(self):
        wrong_room = booking(
            "Open Play- Badminton",
            "Cooke 308",
            "2026-09-28T05:45:00-05:00",
            "2026-09-28T16:30:00-05:00",
        )
        broad_name = booking(
            "Open Play- Badminton Tournament",
            "Cooke 325",
            "2026-09-28T05:45:00-05:00",
            "2026-09-28T16:30:00-05:00",
        )
        self.assertFalse(scraper.is_target_booking(wrong_room))
        self.assertFalse(scraper.is_target_booking(broad_name))

    def test_sort_merge_and_all_seven_days(self):
        bookings = [
            booking(
                "Open Play- Badminton",
                "Cooke 325",
                "2026-09-28T08:00:00-05:00",
                "2026-09-28T10:00:00-05:00",
            ),
            booking(
                "Open Play Badminton",
                "Cooke 325",
                "2026-09-28T07:00:00-05:00",
                "2026-09-28T08:00:00-05:00",
            ),
            booking(
                "Open Play Badminton",
                "Cooke 325",
                "2026-09-28T09:30:00-05:00",
                "2026-09-28T11:00:00-05:00",
            ),
        ]
        result = scraper.normalize_schedule(
            bookings,
            date(2026, 9, 28),
            date(2026, 10, 4),
            datetime(2026, 9, 28, 6, 15, tzinfo=CENTRAL),
        )
        self.assertEqual(len(result["schedule"]), 7)
        self.assertEqual(
            result["schedule"][0]["intervals"], [{"start": "07:00", "end": "11:00"}]
        )
        self.assertEqual(result["schedule"][1]["intervals"], [])
        self.assertEqual(
            result["schedule"][0]["reservations"],
            [{"start": "07:00", "end": "11:00", "type": "open_play"}],
        )

    def test_other_room_reservations_are_generic_timeline_blocks(self):
        bookings = [
            booking(
                "Varsity Practice",
                "Cooke 325",
                "2026-09-29T08:00:00-05:00",
                "2026-09-29T12:05:00-05:00",
            ),
            booking(
                "Private Event",
                "Cooke 308",
                "2026-09-29T09:00:00-05:00",
                "2026-09-29T10:00:00-05:00",
            ),
        ]
        result = scraper.normalize_schedule(
            bookings,
            date(2026, 9, 28),
            date(2026, 10, 4),
            datetime(2026, 9, 29, 6, 15, tzinfo=CENTRAL),
        )
        self.assertEqual(result["schedule"][1]["intervals"], [])
        self.assertEqual(
            result["schedule"][1]["reservations"],
            [{"start": "08:00", "end": "12:05", "type": "reserved"}],
        )

    def test_utc_input_is_converted_to_chicago_time(self):
        bookings = [
            booking(
                "Open Play- Badminton",
                "Cooke 325",
                "2026-09-28T10:45:00+00:00",
                "2026-09-28T21:30:00+00:00",
            )
        ]
        result = scraper.normalize_schedule(
            bookings,
            date(2026, 9, 28),
            date(2026, 10, 4),
            datetime(2026, 9, 28, 6, 15, tzinfo=CENTRAL),
        )
        self.assertEqual(
            result["schedule"][0]["intervals"], [{"start": "05:45", "end": "16:30"}]
        )

    def test_bad_matching_booking_fails_instead_of_publishing_partial_data(self):
        bookings = [
            booking("Open Play- Badminton", "Cooke 325", None, "2026-09-28T10:00:00-05:00")
        ]
        with self.assertRaises(scraper.ScrapeError):
            scraper.normalize_schedule(
                bookings,
                date(2026, 9, 28),
                date(2026, 10, 4),
                datetime(2026, 9, 28, 6, 15, tzinfo=CENTRAL),
            )


class PayloadTests(unittest.TestCase):
    def test_payload_uses_zero_based_months_and_full_week(self):
        payload = scraper.build_events_payload(
            {
                "apiKey": "public-key",
                "buildingIds": [148],
                "statusIds": [141, 142],
            },
            date(2026, 9, 28),
            date(2026, 10, 4),
        )
        self.assertEqual(payload["startMonth"], 8)
        self.assertEqual(payload["endMonth"], 9)
        self.assertEqual(payload["startDay"], 28)
        self.assertEqual(payload["endDay"], 4)
        self.assertEqual(payload["buildingIds"], [148])


if __name__ == "__main__":
    unittest.main()
