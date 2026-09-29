#!/usr/bin/env python3
"""Fetch and normalize the current week's public badminton schedule."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, time as datetime_time, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


BASE_URL = "https://east.mymazevo.com"
TIME_ZONE_NAME = "America/Chicago"
TIME_ZONE = ZoneInfo(TIME_ZONE_NAME)
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "assets/data/badminton_schedule.json"
USER_AGENT = "MKBC-UMN-schedule-updater/1.0 (+https://mkbc-umn.github.io/)"
# Mazévo's public web client signs every request with this client-side key.
# It is shipped in the site's JavaScript bundle and is not a credential.
REQUEST_SIGNING_KEY = b"q8J7o1x3Jt9pJH2v8Y0sZ4tQ1uF5mA9c3bR7dL2pW0E="
TARGET_BUILDING = "Cooke Hall"
TARGET_ROOM = "Cooke 325"
TARGET_ACTIVITY = "Open Play Badminton"


class ScrapeError(RuntimeError):
    """Raised when Mazévo returns data that cannot be safely published."""


def normalize_label(value: object) -> str:
    """Normalize case, punctuation, and whitespace without broad fuzzy matching."""
    return " ".join(re.findall(r"[a-z0-9]+", str(value).casefold()))


def week_bounds(reference: datetime) -> tuple[date, date]:
    local_reference = reference.astimezone(TIME_ZONE)
    monday = local_reference.date() - timedelta(days=local_reference.weekday())
    return monday, monday + timedelta(days=6)


def _request_json(
    path: str,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    retries: int = 3,
) -> Any:
    body = "" if payload is None else json.dumps(payload, separators=(",", ":"))
    data = None if payload is None else body.encode("utf-8")
    last_error: Exception | None = None

    for attempt in range(retries):
        timestamp = datetime.now(ZoneInfo("UTC")).isoformat(timespec="milliseconds").replace(
            "+00:00", "Z"
        )
        signature = hmac.new(
            REQUEST_SIGNING_KEY,
            f"{timestamp}:{body}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        headers = {
            "Accept": "application/json",
            "Origin": BASE_URL,
            "Referer": f"{BASE_URL}/calendar",
            "User-Agent": USER_AGENT,
            "X-Timestamp": timestamp,
            "X-Signature": signature,
        }
        if data is not None:
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(
            f"{BASE_URL}{path}", data=data, headers=headers, method=method
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                if response.status != 200:
                    raise ScrapeError(f"Mazévo returned HTTP {response.status}")
                return json.load(response)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt + 1 < retries:
                time.sleep(2**attempt)

    raise ScrapeError(f"Unable to retrieve Mazévo calendar data: {last_error}")


def resolve_calendar_filter(code: str) -> dict[str, Any]:
    result = _request_json(
        "/api/calendarfilter/GetEncryptedCalendarFilter",
        method="POST",
        payload={"value": code},
    )
    if not isinstance(result, dict):
        raise ScrapeError("Mazévo returned an invalid calendar filter")
    if not result.get("apiKey"):
        raise ScrapeError("Mazévo calendar filter did not contain a public API key")
    if not isinstance(result.get("buildingIds"), list) or not result["buildingIds"]:
        raise ScrapeError("Mazévo calendar filter did not contain any buildings")
    return result


def build_events_payload(
    calendar_filter: dict[str, Any], monday: date, sunday: date
) -> dict[str, Any]:
    start_local = datetime.combine(monday, datetime_time.min, TIME_ZONE)
    end_local = datetime.combine(sunday + timedelta(days=1), datetime_time.min, TIME_ZONE)
    end_local -= timedelta(minutes=1)

    def utc_iso(value: datetime) -> str:
        return value.astimezone(ZoneInfo("UTC")).isoformat(timespec="milliseconds").replace(
            "+00:00", "Z"
        )

    return {
        "start": utc_iso(start_local),
        "end": utc_iso(end_local),
        "buildingIds": calendar_filter["buildingIds"],
        "roomTags": calendar_filter.get("roomTags"),
        "eventTypeIds": calendar_filter.get("eventTypeIds"),
        "statusIds": calendar_filter.get("statusIds"),
        "organizationIds": calendar_filter.get("organizationIds"),
        "organizationTypeIds": calendar_filter.get("organizationTypeIds"),
        "hideSpecialDates": bool(calendar_filter.get("hideSpecialDates", False)),
        "userOffsetMinutes": int(-(start_local.utcoffset() or timedelta()).total_seconds() / 60),
        "apiKey": calendar_filter["apiKey"],
        "startYear": monday.year,
        "startMonth": monday.month - 1,
        "startDay": monday.day,
        "endYear": sunday.year,
        "endMonth": sunday.month - 1,
        "endDay": sunday.day,
    }


def fetch_bookings(code: str, monday: date, sunday: date) -> list[dict[str, Any]]:
    calendar_filter = resolve_calendar_filter(code)
    response = _request_json(
        "/api/PublicCalendar/GetEvents",
        method="POST",
        payload=build_events_payload(calendar_filter, monday, sunday),
    )
    if not isinstance(response, dict) or not isinstance(response.get("bookings"), list):
        raise ScrapeError("Mazévo events response did not contain a bookings list")
    return response["bookings"]


def is_target_booking(booking: dict[str, Any]) -> bool:
    return (
        is_target_room(booking)
        and normalize_label(booking.get("eventName")) == normalize_label(TARGET_ACTIVITY)
    )


def is_target_room(booking: dict[str, Any]) -> bool:
    return (
        normalize_label(booking.get("buildingDescription")) == normalize_label(TARGET_BUILDING)
        and normalize_label(booking.get("roomDescription")) == normalize_label(TARGET_ROOM)
    )


def _parse_datetime(value: object, field: str) -> datetime:
    if not isinstance(value, str):
        raise ScrapeError(f"A Cooke 325 booking is missing {field}")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ScrapeError(f"A Cooke 325 booking has an invalid {field}") from exc
    if parsed.tzinfo is None:
        raise ScrapeError(f"A Cooke 325 booking has no timezone in {field}")
    return parsed.astimezone(TIME_ZONE)


def _split_by_day(start: datetime, end: datetime) -> list[tuple[date, datetime, datetime]]:
    if end <= start:
        raise ScrapeError("A matching booking ends before it starts")
    pieces: list[tuple[date, datetime, datetime]] = []
    cursor = start
    while cursor.date() < end.date():
        midnight = datetime.combine(cursor.date() + timedelta(days=1), datetime_time.min, TIME_ZONE)
        pieces.append((cursor.date(), cursor, midnight))
        cursor = midnight
    pieces.append((cursor.date(), cursor, end))
    return pieces


def _merge_intervals(intervals: list[tuple[datetime, datetime]]) -> list[tuple[datetime, datetime]]:
    merged: list[list[datetime]] = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return [(start, end) for start, end in merged]


def normalize_schedule(
    bookings: list[dict[str, Any]], monday: date, sunday: date, scraped_at: datetime
) -> dict[str, Any]:
    intervals_by_date: dict[date, list[tuple[datetime, datetime]]] = {
        monday + timedelta(days=offset): [] for offset in range(7)
    }
    reservations_by_date: dict[date, list[tuple[datetime, datetime, str]]] = {
        monday + timedelta(days=offset): [] for offset in range(7)
    }

    for booking in bookings:
        if not isinstance(booking, dict) or not is_target_room(booking):
            continue
        start = _parse_datetime(booking.get("dateTimeStart"), "dateTimeStart")
        end = _parse_datetime(booking.get("dateTimeEnd"), "dateTimeEnd")
        is_open_play = is_target_booking(booking)
        for day, piece_start, piece_end in _split_by_day(start, end):
            if monday <= day <= sunday:
                if is_open_play:
                    intervals_by_date[day].append((piece_start, piece_end))
                reservations_by_date[day].append(
                    (piece_start, piece_end, "open_play" if is_open_play else "reserved")
                )

    schedule = []
    for day in sorted(intervals_by_date):
        intervals = [
            {
                "start": start.strftime("%H:%M"),
                "end": end.strftime("%H:%M"),
            }
            for start, end in _merge_intervals(intervals_by_date[day])
        ]
        reservations = []
        for reservation_type in ("reserved", "open_play"):
            same_type = [
                (start, end)
                for start, end, item_type in reservations_by_date[day]
                if item_type == reservation_type
            ]
            for start, end in _merge_intervals(same_type):
                reservations.append(
                    {
                        "start": start.strftime("%H:%M"),
                        "end": "24:00" if end.date() > day else end.strftime("%H:%M"),
                        "type": reservation_type,
                    }
                )
        reservations.sort(key=lambda item: (item["start"], item["end"], item["type"]))
        schedule.append(
            {
                "date": day.isoformat(),
                "day": day.strftime("%a"),
                "intervals": intervals,
                "reservations": reservations,
            }
        )

    return {
        "location": "Cooke Hall 325",
        "activity": TARGET_ACTIVITY,
        "timezone": TIME_ZONE_NAME,
        "week_start": monday.isoformat(),
        "week_end": sunday.isoformat(),
        "scraped_at": scraped_at.astimezone(TIME_ZONE).isoformat(timespec="seconds"),
        "schedule": schedule,
    }


def write_schedule(schedule: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(f"{output_path.suffix}.tmp")
    temporary_path.write_text(json.dumps(schedule, indent=2) + "\n", encoding="utf-8")
    temporary_path.replace(output_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument(
        "--now",
        help="Override the current time with an ISO-8601 timestamp (for testing).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    code = os.environ.get("MAZEVO_CALENDAR_CODE", "").strip()
    if not code:
        print("MAZEVO_CALENDAR_CODE is required", file=sys.stderr)
        return 2

    try:
        now = datetime.fromisoformat(args.now) if args.now else datetime.now(TIME_ZONE)
        if now.tzinfo is None:
            now = now.replace(tzinfo=TIME_ZONE)
        monday, sunday = week_bounds(now)
        bookings = fetch_bookings(code, monday, sunday)
        schedule = normalize_schedule(bookings, monday, sunday, now)
        write_schedule(schedule, args.output)
    except ScrapeError as exc:
        print(f"Schedule update failed: {exc}", file=sys.stderr)
        return 1

    interval_count = sum(len(day["intervals"]) for day in schedule["schedule"])
    print(f"Wrote {interval_count} intervals for {monday} through {sunday} to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
