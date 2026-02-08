# Legacy Container

This folder holds code that is no longer wired into the main application but
is preserved for reference or potential re-use. Items here are considered
unsupported in the current runtime.

## Contents

- `GraphQL/`:
  - Legacy GraphQL schema, mapping, and server wrapper superseded by the
    Server GraphQL implementation wired in `src/main.py`.
- `Server/auth.py`:
  - Legacy auth router not currently included in the FastAPI app.

If any of this is needed again, reintroduce it explicitly and review for
compatibility with the current codebase.

## Config Notes

Config version `1.3` removed the single `auth.admin_username` field in favor
of `auth.admin_usernames` (list). The migration moves any existing value into
the list automatically.
