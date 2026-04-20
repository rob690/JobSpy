# Daily recruitment leads

Thin wrapper around `jobspy.scrape_jobs()` for generating a daily list of fresh
job-posting leads across configured tech verticals and locations. The posting's
company is the lead — a company actively hiring is a prospect for your
recruitment services.

## Files

- `daily_leads.py` — runner script
- `leads_config.yaml` — edit this to change verticals, locations, sites, etc.

## First run

From the repo root:

```bash
pip install -e .
pip install pyyaml
python examples/daily_leads.py
```

Outputs:
- `leads/leads_YYYY-MM-DD.csv` — today's new leads
- `leads/seen_jobs.csv` — running history of every job URL ever emitted;
  used to dedupe subsequent runs

Run it a second time immediately — the summary should report `0 new leads`,
confirming dedupe works.

## Scheduling daily

Linux/macOS cron (06:00 local):

```cron
0 6 * * *  cd /path/to/JobSpy && /usr/bin/python examples/daily_leads.py >> leads/run.log 2>&1
```

Windows: use Task Scheduler with the same command.

## Tuning

- **Verticals / locations**: edit `leads_config.yaml`. Start small (1-2
  verticals x 1-2 locations) to sanity-check, then expand.
- **results_wanted**: per board, per query. 50 is a good starting point.
- **hours_old**: keep at 24 for a daily schedule. Increase if you run less
  often. Note LinkedIn/Indeed restrict combining `hours_old` with some other
  filters — the script avoids those combinations by default.
- **Proxies**: if you hit rate limits, add a `proxies` key to the config and
  wire it through to `scrape_jobs(proxies=...)` in `daily_leads.py`.

## Output columns

The CSV leads with recruitment-relevant fields: `site, company, title,
location, job_url, company_url, date_posted, job_type, is_remote, min_amount,
max_amount, currency, interval, description, search_term, search_location`.
All other JobSpy fields are retained after these.
