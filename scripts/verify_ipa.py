#!/usr/bin/env python3
"""Verify deployment targets and required TrollStore entitlements in an IPA."""

import argparse
import json
import os
from pathlib import Path
import plistlib
import re
import subprocess
import tempfile
import zipfile

MAXIMUM_IOS = (14, 8)
REQUIRED_ENTITLEMENTS = (
    "get-task-allow",
    "com.apple.developer.kernel.extended-virtual-addressing",
    "com.apple.developer.kernel.increased-memory-limit",
)


def version(value):
    return tuple(int(part) for part in value.split("."))


def inspect_binary(path):
    result = subprocess.run(
        ["otool", "-l", str(path)], check=True, capture_output=True, text=True
    ).stdout
    found = re.findall(r"^\s+minos\s+([0-9.]+)$", result, re.MULTILINE)
    if not found:
        raise ValueError(f"No Mach-O iOS deployment version found in {path.name}")
    for value in found:
        if version(value) > MAXIMUM_IOS:
            raise ValueError(f"{path.name} targets iOS {value}, above 14.8")
    return found


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("ipa", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if not args.ipa.is_file():
        raise ValueError(f"Missing IPA: {args.ipa}")

    report = {"ipa": args.ipa.name, "bundles": [], "entitlements": {}}
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with zipfile.ZipFile(args.ipa) as archive:
            archive.extractall(root)
        bundles = sorted([*root.glob("Payload/*.app"), *root.glob("Payload/*.app/**/*.appex")])
        if not bundles:
            raise ValueError("The IPA contains no app bundle")
        for bundle in bundles:
            with (bundle / "Info.plist").open("rb") as stream:
                info = plistlib.load(stream)
            minimum = info.get("MinimumOSVersion")
            if minimum is None or version(minimum) > MAXIMUM_IOS:
                raise ValueError(f"{bundle.name} has unsupported MinimumOSVersion: {minimum}")
            executable = bundle / info["CFBundleExecutable"]
            report["bundles"].append(
                {
                    "name": bundle.name,
                    "bundleId": info.get("CFBundleIdentifier"),
                    "minimumOSVersion": minimum,
                    "machOVersions": inspect_binary(executable),
                }
            )
            if bundle.suffix == ".app":
                signed = subprocess.run(
                    ["ldid", "-e", str(executable)],
                    check=True,
                    capture_output=True,
                ).stdout
                entitlements = plistlib.loads(signed)
                for key in REQUIRED_ENTITLEMENTS:
                    if entitlements.get(key) is not True:
                        raise ValueError(f"Missing or disabled entitlement: {key}")
                report["entitlements"] = {key: entitlements[key] for key in REQUIRED_ENTITLEMENTS}

    report["status"] = "passed-static-checks"
    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    print(text, end="")
    if args.report:
        args.report.write_text(text)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as stream:
            stream.write("## IPA static verification\n\n```json\n" + text + "```\n")


if __name__ == "__main__":
    main()
