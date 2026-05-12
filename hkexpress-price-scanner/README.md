# HKExpress Price Scanner

A Python project to periodically scan HKExpress flight prices for configured routes, track historical prices, and notify on cheaper options.

## Features
- Configurable routes and search parameters
- Web scraping using Playwright (for dynamic content)
- Historical price tracking (SQLite)
- Scheduler (APScheduler or GitHub Actions)
- Notifications (email/Telegram)
- Detect price drops

## Setup
1. Clone or navigate to this folder
2. `pip install -r requirements.txt`
3. Configure `config.yaml`
4. Run `python main.py`

## Project Structure
```
hkexpress-price-scanner/
├── main.py
├── scraper.py
├── database.py
├── notifier.py
├── config.yaml
├── requirements.txt
├── scheduler.py
└── README.md
```