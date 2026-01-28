#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shared utilities for D&D 5e API interactions.
Provides common functions for fetching and parsing D&D 5e API data.
"""

import requests
import time
from typing import Dict, Any, Optional

# D&D 5e API configuration
API_ROOT = "https://www.dnd5eapi.co"
API_TIMEOUT = 12
RETRY_ATTEMPTS = 3
RETRY_DELAY = 2  # seconds between retries
DEFAULT_SLEEP = 0.2  # polite rate limiting between requests


def get_json(url: str, retries: int = RETRY_ATTEMPTS, timeout: int = API_TIMEOUT) -> Optional[Dict[str, Any]]:
    """
    Fetch JSON from URL with retry logic.
    
    Args:
        url: The URL to fetch from
        retries: Number of retry attempts on failure
        timeout: Request timeout in seconds
        
    Returns:
        Parsed JSON dict, or None if all retries failed
    """
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=timeout)
            if r.status_code == 200:
                return r.json()
            else:
                print(f"HTTP {r.status_code} for {url}")
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1}/{retries} failed for {url}: {e}")
            if attempt < retries - 1:
                time.sleep(RETRY_DELAY)
    
    print(f"Failed to fetch {url} after {retries} attempts")
    return None


def get_json_paginated(initial_url: str) -> Optional[list]:
    """
    Fetch all paginated results from a D&D 5e API endpoint.
    
    Args:
        initial_url: The initial API endpoint URL
        
    Returns:
        List of all results from all pages, or None if initial fetch fails
    """
    data = get_json(initial_url)
    if not data or "results" not in data:
        return None
    
    results = data.get("results", [])
    
    # Handle pagination if present
    index = 0
    while "next" in data:
        next_url = f"{API_ROOT}{data['next']}"
        data = get_json(next_url)
        if data and "results" in data:
            results.extend(data["results"])
        else:
            break
        index += 1
    
    return results


def construct_full_url(endpoint: str) -> str:
    """Construct full URL from API endpoint path."""
    if endpoint.startswith("http"):
        return endpoint
    if not endpoint.startswith("/"):
        endpoint = "/" + endpoint
    return f"{API_ROOT}/api{endpoint}"
