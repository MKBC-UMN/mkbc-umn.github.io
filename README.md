# MKBC UMN Website

Jekyll/Minimal Mistakes starter for the Minnesota Korean Badminton Club website.

## Local Preview

```bash
bundle install
bundle exec jekyll serve
```

Open `http://localhost:4000`.

## Editing Content

- Club intro: `_data/club.yml`
- Officers: `_data/officers.yml`
- Policies: `_data/policies.yml`
- Join steps: `_data/join.yml`
- Sidebar contacts/logo: `_config.yml`
- Homepage structure: `index.md`

## Automated Schedule

The current Monday-through-Sunday Open Play Badminton schedule is published at
`assets/data/badminton_schedule.json` and rendered on the homepage. A daily
GitHub Actions workflow updates the snapshot from Mazévo.

Repository setup requires an Actions secret named `MAZEVO_CALENDAR_CODE`. See
`scraping/README.md` for local usage and tests.
