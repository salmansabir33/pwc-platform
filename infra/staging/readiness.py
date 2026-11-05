"""Offline coexistence assessment, never a host probe or deployment permission."""

import argparse
import json
from pathlib import Path
import re
from .deploy import metadata, unique


def coexistence(project, inventory):
    if (
        not isinstance(inventory, dict)
        or set(inventory) != {"inventory_complete", "compose_projects", "tcp_ports"}
        or inventory["inventory_complete"] is not True
        or not re.fullmatch(r"pwc-staging(?:-[a-z0-9-]{1,24})?", project)
        or not isinstance(inventory["compose_projects"], list)
        or len(inventory["compose_projects"]) > 100
        or not all(
            isinstance(p, str) and re.fullmatch(r"[a-z0-9][a-z0-9_.-]{0,63}", p)
            for p in inventory["compose_projects"]
        )
        or not isinstance(inventory["tcp_ports"], list)
        or len(inventory["tcp_ports"]) > 1024
        or not all(type(p) is int and 1 <= p <= 65535 for p in inventory["tcp_ports"])
    ):
        raise ValueError("Incomplete host inventory (values redacted)")
    blockers = []
    if 443 in inventory["tcp_ports"]:
        blockers.append("PUBLIC_443_OCCUPIED_DO_NOT_STOP_OTHER_PROJECTS")
    if project in inventory["compose_projects"]:
        blockers.append("COMPOSE_PROJECT_ALREADY_EXISTS_DO_NOT_OVERWRITE")
    return {
        "coexistence_preflight_passed": not blockers,
        "blockers": blockers,
        "actual_host_acceptance": False,
        "deployment_authorized": False,
        "real_enrollment_ready": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    options = parser.parse_args()
    try:
        value = metadata(
            json.loads(options.config.read_text(), object_pairs_hook=unique)
        )
        inventory = json.loads(options.inventory.read_text(), object_pairs_hook=unique)
        report = coexistence(value["project"], inventory)
        print(json.dumps(report, indent=2))
        return int(not report["coexistence_preflight_passed"])
    except (ValueError, OSError, TypeError):
        print(
            '{"coexistence_preflight_passed":false,"error":"INVALID_OR_UNAVAILABLE_INPUT"}'
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
