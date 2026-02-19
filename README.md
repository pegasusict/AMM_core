# Audiophiles' Music Manager - AMM_core

[![Codacy Badge](https://app.codacy.com/project/badge/Grade/1c70bea27f3e440ea6ed1c2737cf926e)](https://app.codacy.com/gh/pegasusict/AMM_core/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)

__AMM__ is a music management system for very large collections.

It has the following processing capabilities:

* Importing / Parsing
* Fingerprinting
* Silence Trimming
* Converting
* Tag Retrieval
* Art Retrieval
* Lyrics Retrieval
* Tagging
* Renaming / Sorting
* exporting

## Modules

|Module |Description            |Progress |
|-------|-----------------------|--------:|
|Core   |Server                 |     90% |
|API client|API client          |    100% |
|Web    |Web Interface          |     10% |
|TUI    |CLI/Terminal Client    | planned |
|GUI    |Graphical Client       | planned |
|Mobile |Mobile Client          | planned |

## user login via google oauth, admin approved registration

## Per-user playback

The system has a icecast like playbacksystem which works on a per-user basis.

## Planned capabilities

audiobook support?
crossfading

## Local test run

Use the helper script to create local test directories and start the API server:

```bash
./scripts/run-local-server.sh
```

Or via Make:

```bash
make run-local
```

## MariaDB run

Set `DATABASE_URL` to an async MySQL/MariaDB URL (driver: `asyncmy`) and start uvicorn:

```bash
export DATABASE_URL="mysql+asyncmy://amm_user:amm_pass@127.0.0.1:3306/amm_db?charset=utf8mb4"
# Bind to localhost-only by default.
PYTHONPATH="$(pwd)/src" .venv/bin/python -m uvicorn main:app --app-dir src --host 127.0.0.1 --port 8000
```

Run database migrations manually (optional; startup also runs `alembic upgrade head`):

```bash
make migrate-db
```
