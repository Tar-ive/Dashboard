#!/usr/bin/env python3
"""
Test script to verify the HTML structure and components are properly implemented
"""

import os
import re
from pathlib import Path

def test_html_structure():
    """Test that the HTML file has all required components"""
    html_path = Path("public/index.html")
    
    if not html_path.exists():
        print("❌ HTML file not found")
        return False
    
    with open(html_path, 'r') as f:
        content = f.read()
    
    # Test required components
    tests = [
        # Basic HTML structure
        (r'<!DOCTYPE html>', "HTML5 doctype"),
        (r'<html lang="en">', "HTML lang attribute"),
        (r'<meta charset="UTF-8">', "UTF-8 charset"),
        (r'<meta name="viewport"', "Viewport meta tag"),
        
        # Title and description
        (r'<title>CADS Research Visualization</title>', "Page title"),
        (r'<meta name="description"', "Meta description"),
        
        # Preload directives
        (r'<link rel="preload" href="/data/visualization-data.json.gz"', "Data preload"),
        (r'<link rel="preload" href="/data/search-index.json.gz"', "Search index preload"),
        
        # Dark theme CSS
        (r'background: #1a1a1a', "Dark background"),
        (r'color: #ffffff', "Light text color"),
        
        # Required containers
        (r'<div id="loading">', "Loading container"),
        (r'<div id="map-container">', "Map container"),
        (r'<div id="ui-panel">', "UI panel"),
        (r'<div id="tooltip">', "Tooltip container"),
        (r'<div id="error-message">', "Error message container"),
        
        # UI components
        (r'<input type="text" id="search-input"', "Search input"),
        (r'<select id="researcher-filter"', "Researcher filter"),
        (r'<input type="range" id="year-filter"', "Year filter"),
        (r'<select id="cluster-filter"', "Cluster filter"),
        
        # Deck.gl CDN
        (r'<script src="https://unpkg.com/deck.gl@latest/dist.min.js">', "Deck.gl CDN"),
        
        # Loading states
        (r'class="spinner"', "Loading spinner"),
        (r'Loading CADS Research Visualization', "Loading text"),
        
        # Responsive design
        (r'@media \(max-width: 768px\)', "Mobile responsive CSS"),
        (r'@media \(prefers-reduced-motion: reduce\)', "Accessibility CSS"),
        (r'@media \(prefers-contrast: high\)', "High contrast CSS"),
        
        # JavaScript functionality
        (r'function init\(\)', "Init function"),
        (r'setupUIEventListeners', "Event listeners setup"),
        (r'togglePanel', "Panel toggle function"),
        (r'showTooltip', "Tooltip function"),
        (r'debounce', "Debounce utility"),
    ]
    
    passed = 0
    failed = 0
    
    print("🧪 Testing HTML structure and components...")
    print()
    
    for pattern, description in tests:
        if re.search(pattern, content, re.IGNORECASE):
            print(f"✅ {description}")
            passed += 1
        else:
            print(f"❌ {description}")
            failed += 1
    
    print()
    print(f"📊 Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! HTML structure is complete.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
        return False

def test_css_dark_theme():
    """Test that dark theme is properly implemented"""
    html_path = Path("public/index.html")
    
    with open(html_path, 'r') as f:
        content = f.read()
    
    # Extract CSS content
    css_match = re.search(r'<style>(.*?)</style>', content, re.DOTALL)
    if not css_match:
        print("❌ No CSS found")
        return False
    
    css_content = css_match.group(1)
    
    # Test dark theme colors
    dark_theme_tests = [
        ('#1a1a1a', "Primary dark background"),
        ('#ffffff', "Primary light text"),
        ('#333', "Secondary dark background"),
        ('#555', "Border color"),
        ('#ccc', "Secondary light text"),
        ('#888', "Muted text"),
        ('rgba(42, 42, 42, 0.95)', "Panel background"),
    ]
    
    print("🎨 Testing dark theme implementation...")
    print()
    
    passed = 0
    for color, description in dark_theme_tests:
        if color in css_content:
            print(f"✅ {description}: {color}")
            passed += 1
        else:
            print(f"❌ {description}: {color}")
    
    print()
    print(f"📊 Dark theme: {passed}/{len(dark_theme_tests)} colors found")
    
    return passed == len(dark_theme_tests)

if __name__ == "__main__":
    print("🔍 CADS Research Visualization - HTML Structure Test")
    print("=" * 60)
    
    structure_ok = test_html_structure()
    print()
    theme_ok = test_css_dark_theme()
    
    print()
    print("=" * 60)
    if structure_ok and theme_ok:
        print("🎯 All tests passed! HTML frontend is ready.")
        exit(0)
    else:
        print("❌ Some tests failed. Please review the implementation.")
        exit(1)