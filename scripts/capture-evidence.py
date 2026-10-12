"""Capture real web pages with a locally installed Edge browser.

Reporting utility only: pip install playwright. Does not alter page contents.
"""
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('url')
parser.add_argument('output')
parser.add_argument('--version')
parser.add_argument('--sha')
parser.add_argument('--width', type=int, default=1440)
parser.add_argument('--selector', help='Capture an actual page element instead of the full page')
parser.add_argument('--viewport', action='store_true', help='Capture the visible browser viewport')
args = parser.parse_args()
Path(args.output).parent.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(channel='msedge', headless=True, args=['--no-proxy-server'])
    page = browser.new_page(viewport={'width': args.width, 'height': 1080}, device_scale_factor=1)
    response = page.goto(args.url, wait_until='domcontentloaded', timeout=90000)
    if response and response.status >= 400:
        raise RuntimeError(f'Page returned HTTP {response.status}')
    if args.version:
        page.locator('#version').filter(has_text=args.version).wait_for(timeout=30000)
        page.locator('#health').filter(has_text='Healthy').wait_for(timeout=30000)
    if args.sha:
        page.locator('#commit-sha').filter(has_text=args.sha).wait_for(timeout=30000)
    page.wait_for_timeout(2500)
    if args.selector:
        page.locator(args.selector).screenshot(path=args.output)
    else:
        page.screenshot(path=args.output, full_page=not args.viewport)
    print(f'Captured {page.url} -> {args.output}')
    browser.close()
