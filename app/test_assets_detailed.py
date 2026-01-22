#!/usr/bin/env python3
"""
Test the asset system by simulating JavaScript execution
"""

import requests
from bs4 import BeautifulSoup
import re
import json

BASE_URL = "http://localhost:5000"

print("=" * 70)
print("ASSET SYSTEM DIAGNOSTIC")
print("=" * 70)

# Get the grid page
print("\n1. Loading grid page...")
try:
    resp = requests.get(f"{BASE_URL}/grid/test123", timeout=5)
    html = resp.text
    print(f"   Status: {resp.status_code} OK")
except Exception as e:
    print(f"   ERROR: {e}")
    exit(1)

# Parse HTML
print("\n2. Checking HTML structure...")
soup = BeautifulSoup(html, 'html.parser')

checks = {
    "Konva.js library": len(soup.find_all('script', src=re.compile(r'konva'))) > 0,
    "Socket.IO library": len(soup.find_all('script', src=re.compile(r'socket.io'))) > 0,
    "assetLoader.js script": len(soup.find_all('script', src=re.compile(r'assetLoader'))) > 0,
    "grid module": "grid.js" in html,
    "assetPlacement module": "assetPlacement.js" in html,
    "Asset panel HTML": 'id="assetPanel"' in html,
    "Test button": 'id="testAssetPlacement"' in html,
    "Asset panel script": '[AssetPanel]' in html,
}

for check_name, result in checks.items():
    print(f"   {'✓' if result else '✗'} {check_name}")

# Check if the scripts can be loaded
print("\n3. Checking JavaScript files...")
js_files = [
    "/static/grid/assetLoader.js",
    "/static/grid/assetPlacement.js",
    "/static/grid/grid.js",
    "/static/grid/tokens.js",
]

for js_file in js_files:
    try:
        resp = requests.get(f"{BASE_URL}{js_file}", timeout=5)
        size = len(resp.content)
        has_errors = "SyntaxError" in resp.text or "ReferenceError" in resp.text
        status = "✓" if resp.status_code == 200 and not has_errors else "✗"
        print(f"   {status} {js_file} ({size} bytes)")
    except Exception as e:
        print(f"   ✗ {js_file}: {e}")

# Check API endpoints
print("\n4. Checking API endpoints...")
api_endpoints = [
    "/api/assets/files",
    "/api/assets/files/categories",
]

for endpoint in api_endpoints:
    try:
        resp = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            print(f"   ✓ GET {endpoint}: {list(data.keys())}")
        else:
            print(f"   ✗ GET {endpoint}: {resp.status_code}")
    except Exception as e:
        print(f"   ✗ GET {endpoint}: {e}")

# Check SVG files
print("\n5. Checking SVG asset files...")
svg_files = [
    "/static/assets/terrain/grass.svg",
    "/static/assets/terrain/stone_floor.svg",
    "/static/assets/terrain/water.svg",
    "/static/assets/objects/door.svg",
    "/static/assets/objects/pillar.svg",
    "/static/assets/objects/table.svg",
    "/static/assets/effects/fire.svg",
    "/static/assets/effects/ice.svg",
    "/static/assets/effects/magic_circle.svg",
]

for svg_file in svg_files:
    try:
        resp = requests.get(f"{BASE_URL}{svg_file}", timeout=5)
        if resp.status_code == 200 and b"<svg" in resp.content:
            print(f"   ✓ {svg_file}")
        else:
            print(f"   ✗ {svg_file}: {resp.status_code}")
    except Exception as e:
        print(f"   ✗ {svg_file}: {e}")

print("\n" + "=" * 70)
print("DIAGNOSTIC COMPLETE")
print("=" * 70)
print("\nNext steps:")
print("1. Open http://localhost:5000/grid/test123 in a browser")
print("2. Open the browser's Developer Console (F12)")
print("3. Click the 'Test: Place Grass' button")
print("4. Check for console messages starting with '[AssetPanel]', '[AssetPlacement]', etc.")
print("=" * 70)
