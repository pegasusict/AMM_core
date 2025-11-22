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


MIGRATIONS = {
    "1.0": migrate_1_0_to_1_1,
}

LATEST_VERSION = "1.1"
