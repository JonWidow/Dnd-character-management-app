#!/usr/bin/env python3
"""Test if assets are working properly"""

import requests
import json

BASE_URL = "http://localhost:5000"

# Test 1: Check if API endpoints work
print("=" * 60)
print("Test 1: API Endpoints")
print("=" * 60)

try:
    resp = requests.get(f"{BASE_URL}/api/assets/files", timeout=5)
    print(f"GET /api/assets/files: {resp.status_code}")
    data = resp.json()
    for category, items in data.items():
        print(f"  {category}: {len(items)} items")
        if items:
            print(f"    - {items[0]['name']}: {items[0]['path']}")
except Exception as e:
    print(f"ERROR: {e}")

print()

# Test 2: Check if SVG files are accessible
print("=" * 60)
print("Test 2: SVG Files")
print("=" * 60)

svg_files = [
    "/static/assets/terrain/grass.svg",
    "/static/assets/objects/pillar.svg",
    "/static/assets/effects/fire.svg",
]

for svg_path in svg_files:
    try:
        resp = requests.get(f"{BASE_URL}{svg_path}", timeout=5)
        print(f"GET {svg_path}: {resp.status_code} ({len(resp.content)} bytes)")
        # Check if it's valid SVG
        if resp.status_code == 200:
            if b"<svg" in resp.content:
                print("  ✓ Valid SVG content")
            else:
                print("  ✗ Not valid SVG content")
    except Exception as e:
        print(f"ERROR {svg_path}: {e}")

print()

# Test 3: Check page loads
print("=" * 60)
print("Test 3: Page Loads")
print("=" * 60)

try:
    resp = requests.get(f"{BASE_URL}/grid/test123", timeout=5)
    print(f"GET /grid/test123: {resp.status_code}")
    if resp.status_code == 200:
        # Check for key components
        checks = [
            ("AssetLoader", "class AssetLoader" in resp.text),
            ("assetPlacement.js", "assetPlacement.js" in resp.text),
            ("assetLayer", "assetLayer" in resp.text),
            ("Asset Panel", "assetPanel" in resp.text),
            ("Test Button", "testAssetPlacement" in resp.text),
        ]
        for check_name, result in checks:
            print(f"  {check_name}: {'✓' if result else '✗'}")
except Exception as e:
    print(f"ERROR: {e}")

print()
print("=" * 60)
print("All tests completed!")
print("=" * 60)
