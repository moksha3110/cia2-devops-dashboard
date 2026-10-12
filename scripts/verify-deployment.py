"""Verify a deployment over HTTP using only Python's standard library."""

import argparse
import json
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import urlopen


def get_response(url):
    with urlopen(url, timeout=5) as response:
        if response.status != 200:
            raise ValueError(f"{url} returned HTTP {response.status}")
        return response.headers.get_content_type(), response.read().decode("utf-8")


def verify(args):
    base_url = args.url.rstrip("/")
    parsed = urlsplit(base_url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Provide an http:// or https:// deployment URL")

    _, health_body = get_response(f"{base_url}/actuator/health")
    if json.loads(health_body).get("status") != "UP":
        raise ValueError("Application health is not UP")

    _, info_body = get_response(f"{base_url}/api/info")
    info = json.loads(info_body)
    for field in ("name", "version", "environment", "message"):
        if not isinstance(info.get(field), str) or not info[field].strip():
            raise ValueError(f"Missing or empty metadata field: {field}")
    for field, expected in (
        ("commitSha", args.expected_sha),
        ("version", args.expected_version),
        ("environment", args.expected_environment),
    ):
        if expected is not None and info.get(field) != expected:
            raise ValueError(f"Expected {field}={expected!r}, got {info.get(field)!r}")

    content_type, html = get_response(f"{base_url}/")
    if content_type != "text/html" or "<html" not in html.lower() or "</html>" not in html.lower():
        raise ValueError("Dashboard did not return an HTML document")
    return info


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--expected-sha")
    parser.add_argument("--expected-version")
    parser.add_argument("--expected-environment")
    parser.add_argument("--attempts", type=int, default=1)
    parser.add_argument("--delay", type=float, default=5)
    args = parser.parse_args()
    if args.attempts < 1 or args.delay < 0:
        parser.error("attempts must be positive and delay must be non-negative")

    for attempt in range(1, args.attempts + 1):
        try:
            info = verify(args)
            print("Verified HTTP 200, dashboard HTML, health UP, and deployment metadata.")
            print(json.dumps(info, indent=2))
            return 0
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as error:
            print(f"Verification attempt {attempt}/{args.attempts}: {error}", file=sys.stderr)
            if attempt < args.attempts:
                time.sleep(args.delay)
    return 1


if __name__ == "__main__":
    sys.exit(main())
