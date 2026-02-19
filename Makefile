.PHONY: run-local migrate-db

run-local:
	./scripts/run-local-server.sh

migrate-db:
	PYTHONPATH="$(PWD)/src" .venv/bin/python scripts/migrate_db_schema.py
