# Badminton schedule updater

This directory contains the daily pipeline that publishes the current and next
Monday-through-Sunday Open Play Badminton schedules for Cooke Hall 325.

## Run locally

Python 3.11 or newer is required. The scraper uses only the Python standard
library.

```bash
export MAZEVO_CALENDAR_CODE="..."
python3 scraping/scrape_schedule.py
```

Run the tests with:

```bash
python3 -m unittest discover -s scraping/tests -v
```

The calendar share code must stay out of the repository. The GitHub Actions
workflow reads it from the `MAZEVO_CALENDAR_CODE` repository secret.

## Output

Each successful run atomically replaces
`assets/data/badminton_schedule.json`. The file contains the Monday-through-
Sunday week that includes the run date plus the following week. A failed
request or invalid response leaves the prior file untouched.
