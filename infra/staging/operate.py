"""Explicit operator workflow. No command confers host or independent acceptance.

Build/scan/bootstrap/expose approvals bind actual configuration, secrets, source
and local image IDs. No synthetic mode, arbitrary hooks, proxy edits or data seed.
"""

import argparse
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import ssl
import socket
import subprocess
import uuid

from . import deploy, provision, scan_summary

ROLES = ("app", "ngo", "ops", "db", "gateway")


def run(*args):
    return provision.run(*args)


def store(path, value):
    provision.write_new(
        path, (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()
    )


def json_file(path):
    return json.loads(Path(path).read_text(), object_pairs_hook=deploy.unique)


def machine():
    return hashlib.sha256(Path("/etc/machine-id").read_bytes().strip()).hexdigest()


def compose(manifest, *args):
    return ("docker", "compose", "--env-file", "/dev/null", "-f", str(manifest), *args)


def validate(config, rendered):
    value = provision.load(config)
    deploy.render(config, None)
    rendered = provision.external(rendered)
    manifest = rendered / "compose.json"
    # Never trust a substituted Compose/portal file: compare to canonical render.
    if json_file(manifest) != deploy.compose(value, rendered):
        raise ValueError("MANIFEST_DRIFT")
    for name in ("ngo", "ops"):
        if (rendered / (name + ".conf")).read_text() != deploy.portal(
            value[name + "_host"]
        ):
            raise ValueError("PORTAL_DRIFT")
    if (rendered / "haproxy.cfg").read_text() != deploy.gateway_config(value):
        raise ValueError("GATEWAY_DRIFT")
    evidence = json_file(rendered / "evidence.json")
    if evidence["synthetic"] or evidence["configuration_sha256"] != provision.digest(
        config
    ):
        raise ValueError("RENDER_DRIFT")
    # Include every rendered file, including the SNI gateway, in approval binding.
    if run("git", "-C", str(deploy.ROOT), "status", "--porcelain").strip():
        raise ValueError("REVIEWED_CLEAN_CHECKOUT_REQUIRED")
    return value, manifest


def image_ids(value):
    result = {}
    for role in ROLES:
        tag = value["project"] + "-" + role + ":" + value["release"]
        image = (
            run("docker", "image", "inspect", tag, "--format", "{{.Id}}")
            .decode()
            .strip()
        )
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", image):
            raise ValueError("IMAGE_ID_INVALID")
        result[role] = image
    return result


def binding(config, rendered, built=False):
    value, manifest = validate(config, rendered)
    result = {
        "config": provision.digest(config),
        "release": value["release"],
        "machine": machine(),
        "inputs": {
            name: provision.digest(path) for name, path in value["files"].items()
        },
        "render": {
            p.name: provision.digest(p)
            for p in sorted(Path(rendered).iterdir())
            if p.is_file()
        },
        "images": image_ids(value) if built else value["images"],
    }
    return value, manifest, result


def token(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def scan_binding(config, rendered, reports):
    value, manifest, bound = binding(config, rendered, built=True)
    report = json_file(Path(reports) / "binding.json")
    if report != bound or scan_summary.main(reports):
        raise ValueError("SCAN_INVALID_OR_FIXABLE_FINDINGS")
    findings = []
    for index, role in enumerate(ROLES, 1):
        path = Path(reports) / f"image-{index}.json"
        data = json_file(path)
        if data.get("Metadata", {}).get("ImageID") != bound["images"][role]:
            raise ValueError("SCAN_IMAGE_MISMATCH")
        bound["scan_" + role] = provision.digest(path)
        for section in data["Results"]:
            for item in section.get("Vulnerabilities") or []:
                if item.get("Severity") in {"HIGH", "CRITICAL"}:
                    findings.append(item["VulnerabilityID"])
    bound["unfixed_high_critical"] = sorted(set(findings))
    return value, manifest, bound


def authorize(bound, approval, disposition):
    if approval != token(bound):
        raise ValueError("EXACT_PLAN_APPROVAL_REQUIRED")
    if bound.get("unfixed_high_critical"):
        risk = json_file(disposition)
        if (
            risk.get("plan_sha256") != approval
            or not isinstance(risk.get("reviewer"), str)
            or not risk["reviewer"].strip()
            or sorted(risk.get("accepted_unfixed_ids", []))
            != bound["unfixed_high_critical"]
        ):
            raise ValueError("OWNER_RISK_DISPOSITION_REQUIRED")


def healthy(manifest, roles, expected_images=None):
    rows = run(*compose(manifest, "ps", "--all", "--format", "json")).decode()
    # Compose versions emit an array or one JSON object per line.
    data = (
        json.loads(rows)
        if rows.lstrip().startswith("[")
        else [json.loads(r) for r in rows.splitlines() if r.strip()]
    )
    for role in roles:
        matches = [r for r in data if r.get("Service") == role]
        if (
            len(matches) != 1
            or matches[0].get("State") != "running"
            or matches[0].get("Health") != "healthy"
        ):
            raise ValueError("SERVICE_NOT_HEALTHY")
        if expected_images is not None:
            actual = (
                run("docker", "inspect", "--format", "{{.Image}}", matches[0]["ID"])
                .decode()
                .strip()
            )
            if actual != expected_images[role]:
                raise ValueError("RUNNING_IMAGE_DRIFT")


def require_free_ingress():
    """Read-only availability check, not a reservation or firewall change."""
    for family, address in ((socket.AF_INET, "0.0.0.0"), (socket.AF_INET6, "::")):
        with socket.socket(family, socket.SOCK_STREAM) as probe:
            if family == socket.AF_INET6:
                probe.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
            probe.bind((address, 443))


def scan(config, rendered, output, scanner):
    if not re.fullmatch(r"[a-zA-Z0-9./_:-]+@sha256:[0-9a-f]{64}", scanner):
        raise ValueError("REVIEWED_SCANNER_DIGEST_REQUIRED")
    _, _, bound = binding(config, rendered, built=True)
    output = provision.external(output)
    provision.private_directory(output.parent)
    output.mkdir(mode=0o700)  # Never mix scans from different builds.
    run("docker", "pull", scanner)
    for index, role in enumerate(ROLES, 1):
        run(
            "docker",
            "run",
            "--rm",
            "-v",
            "/var/run/docker.sock:/var/run/docker.sock",
            "-v",
            str(output) + ":/reports",
            scanner,
            "image",
            "--scanners",
            "vuln",
            "--severity",
            "HIGH,CRITICAL",
            "--format",
            "json",
            "--output",
            f"/reports/image-{index}.json",
            bound["images"][role],
        )
    store(output / "binding.json", bound)
    scan_binding(config, rendered, output)


def deployment_binding(config, rendered, reports, backup_receipt, restore_receipt):
    value, manifest, bound = scan_binding(config, rendered, reports)
    backup = json_file(backup_receipt)
    restore = json_file(restore_receipt)
    if (
        backup["source_machine"] != bound["machine"]
        or backup["source_images"] != bound["images"]
        or backup["source_config"] != bound["config"]
        or backup["offhost_machine"] == bound["machine"]
        or restore["restore_machine"] in {bound["machine"], backup["offhost_machine"]}
        or restore["backup_sha256"] != backup["sha256"]
        or restore["source_images"] != backup["source_images"]
        or restore["result"] != "RESTORE_APP_DB_HEALTHY_NOT_HOST_ACCEPTANCE"
    ):
        raise ValueError("BACKUP_RESTORE_EVIDENCE_MISMATCH")
    bound["backup_receipt"] = provision.digest(backup_receipt)
    bound["restore_receipt"] = provision.digest(restore_receipt)
    return value, manifest, bound


def verify(value):
    """Anonymous external verification; empty directory only, no fabricated data."""
    outcomes = {}
    for host in (value["ngo_host"], value["ops_host"]):
        for path, status in (
            ("/api/v1/health/", 200),
            ("/api/v1/directory/", 200),
            ("/api/v1/organizations/" + str(uuid.UUID(int=0)) + "/", 404),
            ("/api/v1/opportunities/", 503),
        ):
            client = http.client.HTTPSConnection(
                host, context=ssl.create_default_context(), timeout=15
            )
            try:
                client.request("GET", path, headers={"Accept": "application/json"})
                response = client.getresponse()
                raw = response.read(131073)
                if response.status != status or len(raw) > 131072:
                    raise ValueError("PUBLIC_ENDPOINT_STATUS_OR_SIZE")
                data = json.loads(raw)
                if path.endswith("directory/") and (
                    set(data) != {"results", "next_cursor"}
                    or data["results"] != []
                    or data["next_cursor"] is not None
                    or response.getheader("Cache-Control") != "no-store"
                ):
                    raise ValueError("EMPTY_PUBLIC_DIRECTORY_REQUIRED")
                if path.endswith("health/") and data.get("service") != "pwc-api":
                    raise ValueError("HEALTH_INVALID")
                outcomes[host + path] = status
            finally:
                client.close()
    return {
        "statuses": outcomes,
        "directory": "EMPTY_NO_REAL_DATA_APPROVAL",
        "acceptance": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=[
            "render",
            "plan-build",
            "build",
            "scan",
            "plan-bootstrap",
            "bootstrap",
            "plan-expose",
            "expose",
            "verify",
        ],
    )
    parser.add_argument("--config")
    parser.add_argument("--render")
    parser.add_argument("--ngo-host")
    parser.add_argument("--ops-host")
    parser.add_argument("--reports")
    parser.add_argument("--scanner")
    parser.add_argument("--approve-plan-sha256")
    parser.add_argument("--risk-disposition")
    parser.add_argument("--backup-receipt")
    parser.add_argument("--restore-receipt")
    args = parser.parse_args()
    os.umask(0o077)
    try:
        if args.command == "render":
            deploy.render(args.config, args.render)
        elif args.command == "verify":
            hosts = {"ngo_host": args.ngo_host, "ops_host": args.ops_host}
            if hosts["ngo_host"] == hosts["ops_host"] or any(
                not isinstance(h, str)
                or not re.fullmatch(r"[a-z0-9][a-z0-9.-]{1,251}[a-z0-9]", h)
                or "." not in h
                or h.endswith((".test", ".invalid", ".localhost"))
                for h in hosts.values()
            ):
                raise ValueError("EXACT_PUBLIC_HOSTS_REQUIRED")
            print(json.dumps(verify(hosts), indent=2))
        elif args.command == "scan":
            scan(args.config, args.render, args.reports, args.scanner)
        else:
            if args.command.endswith("expose"):
                _, manifest, bound = deployment_binding(
                    args.config,
                    args.render,
                    args.reports,
                    args.backup_receipt,
                    args.restore_receipt,
                )
            elif args.command.endswith("bootstrap"):
                _, manifest, bound = scan_binding(
                    args.config, args.render, args.reports
                )
            else:
                _, manifest, bound = binding(args.config, args.render)
            bound["action"] = args.command.removeprefix("plan-")
            if args.command.startswith("plan-"):
                print(
                    json.dumps(
                        {
                            "plan_sha256": token(bound),
                            "action": bound["action"],
                            "unfixed_high_critical": bound.get(
                                "unfixed_high_critical", []
                            ),
                            "host_acceptance": False,
                        },
                        indent=2,
                    )
                )
            else:
                authorize(bound, args.approve_plan_sha256, args.risk_disposition)
                if args.command == "build":
                    run(str(deploy.HERE / "stack.sh"), str(manifest), "build")
                elif args.command == "bootstrap":
                    # No published ingress. Stop if any service already exists:
                    # upgrades need their own reviewed maintenance/backup sequence.
                    if (
                        run(*compose(manifest, "ps", "--all", "--quiet")).strip()
                        or run(
                            "docker",
                            "volume",
                            "ls",
                            "--quiet",
                            "--filter",
                            "label=com.docker.compose.project="
                            + provision.load(args.config)["project"],
                        ).strip()
                    ):
                        raise ValueError(
                            "INITIAL_BOOTSTRAP_ONLY_EXISTING_PROJECT_PRESERVED"
                        )
                    run(
                        *compose(
                            manifest,
                            "up",
                            "-d",
                            "--no-build",
                            "--pull",
                            "never",
                            "--wait",
                            "--wait-timeout",
                            "180",
                            "db",
                        )
                    )
                    run(
                        *compose(
                            manifest,
                            "--profile",
                            "maintenance",
                            "run",
                            "--rm",
                            "--no-deps",
                            "migrate",
                        )
                    )
                    run(
                        *compose(
                            manifest,
                            "up",
                            "-d",
                            "--no-build",
                            "--pull",
                            "never",
                            "--wait",
                            "--wait-timeout",
                            "180",
                            "app",
                        )
                    )
                    healthy(manifest, ("db", "app"), bound["images"])
                else:
                    healthy(manifest, ("db", "app"), bound["images"])
                    # Existing ingress is never stopped or adopted. Repeated
                    # exposure is a no-op only if this exact stack is healthy.
                    try:
                        healthy(manifest, ROLES, bound["images"])
                    except ValueError:
                        require_free_ingress()
                    else:
                        print("Exact public stack already healthy; no services changed")
                        return 0
                    # No owner migration replay at ingress activation. Initial
                    # bootstrap has already completed the controlled migration.
                    run(
                        *compose(
                            manifest,
                            "up",
                            "-d",
                            "--no-build",
                            "--pull",
                            "never",
                            "--wait",
                            "--wait-timeout",
                            "180",
                            "ngo",
                            "ops",
                            "gateway",
                        )
                    )
                    healthy(manifest, ROLES, bound["images"])
                print(
                    "Approved operation completed; independent acceptance remains pending"
                )
        return 0
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        subprocess.SubprocessError,
    ) as error:
        print("Operation blocker: " + provision.error_code(error))
        print(
            "Operation blocked or failed (details redacted); inspect approved inputs privately; no automatic retry"
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
