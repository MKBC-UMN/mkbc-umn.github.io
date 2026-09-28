# Repository instructions

## Git synchronization

- The scheduled GitHub Actions workflow may commit `assets/data/badminton_schedule.json` directly to `main` once per day.
- Before editing or pushing, fetch `origin` and rebase the current work onto the latest `origin/main`.
- Never force-push or overwrite automated schedule commits. Resolve conflicts by preserving both the newest generated schedule and the intended code or content changes.
- Before pushing directly to `main`, verify that the push will be a fast-forward of the latest `origin/main`.

## Generated schedule data

- `assets/data/badminton_schedule.json` is a rolling generated snapshot for the current Monday-through-Sunday week. It does not archive prior weeks.
- Do not hand-edit the generated JSON unless the user explicitly requests it. Update `scraping/scrape_schedule.py` when generation behavior needs to change.
- Keep `MAZEVO_CALENDAR_CODE` in GitHub Actions secrets. Never commit or print the secret.
- If scraping fails, preserve the last known-good JSON instead of replacing it with empty or invalid data.

## Verification

- For scraper or schedule-data changes, run `python3 -m unittest discover -s scraping/tests -v`.
- For website changes, run `bundle exec jekyll build`.
- For UI behavior changes, verify the relevant interaction and both desktop and mobile layouts.

## Deployment

- GitHub Pages deploys from the repository root on `main`.
- After pushing a production change, confirm that the Pages deployment succeeds.
