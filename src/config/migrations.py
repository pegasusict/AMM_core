from typing import Dict, Any
import logging

logger = logging.getLogger("AMM.Config.Migration")


def migrate_1_0_to_1_1(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Example migration:
    - add new logging.format field
    - rename general.clean → general.clean_on_start
    """
    general = cfg.setdefault("general", {})
    if "clean" in general:
        general["clean_on_start"] = general.pop("clean")

    logging_section = cfg.setdefault("logging", {})
    logging_section.setdefault("format", "%(levelname)s:%(message)s")

    return cfg


def migrate_1_1_to_1_2(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add auth section and admin_usernames list.
    """
    auth = cfg.setdefault("auth", {})
    auth.setdefault("google_client_id", "")
    auth.setdefault("google_client_secret", "")
    auth.setdefault("admin_usernames", [])
    auth.setdefault("allowed_usernames", [])
    auth.setdefault("frontend_url", "http://localhost:3000")
    auth.setdefault("backend_url", "http://localhost:8000")
    return cfg


def migrate_1_2_to_1_3(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Consolidate admin_username into admin_usernames and remove the single field.
    """
    auth = cfg.setdefault("auth", {})
    admin_username = auth.pop("admin_username", "")
    admin_usernames = auth.setdefault("admin_usernames", [])
    if admin_username:
        if admin_username not in admin_usernames:
            admin_usernames.append(admin_username)
    return cfg


MIGRATIONS = {
    "1.0": migrate_1_0_to_1_1,
    "1.1": migrate_1_1_to_1_2,
    "1.2": migrate_1_2_to_1_3,
}

LATEST_VERSION = "1.3"
