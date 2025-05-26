#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for Enhanced Stock Watchlist Application
This script demonstrates the core functionality and can be used for testing.
"""

import time
import requests
import json
from stock_manager import StockManager

def test_stock_manager():
    """Test the StockManager functionality"""
    print("Testing Stock Manager...")
    
    # Initialize stock manager
    manager = StockManager()
    
    # Test adding stocks
    test_symbols = ['AAPL', 'GOOGL', 'MSFT']
    
    for symbol in test_symbols:
        try:
            print(f"Adding {symbol} to watchlist...")
            result = manager.add_stock(symbol)
            if result:
                print(f"Successfully added {symbol}")
            else:
                print(f"Failed to add {symbol}")
        except Exception as e:
            print(f"Error adding {symbol}: {e}")
    
    # Test getting stock data
    print("\nGetting current stock data...")
    stocks = manager.get_all_stocks()
    
    for stock in stocks:
        print(f"  {stock['symbol']}: ${stock.get('current_price', 'N/A')} "
              f"({stock.get('price_change_percent', 0):.2f}%)")
    
    # Test creating alerts
    print("\nTesting alert creation...")
    try:
        alert = manager.create_alert('AAPL', 'price_above', 150.0)
        if alert:
            print(f"Created alert for AAPL above $150")
        else:
            print(f"Failed to create alert")
    except Exception as e:
        print(f"Error creating alert: {e}")
    
    # Get alerts
    alerts = manager.get_alerts()
    print(f"Current alerts: {len(alerts)}")
    
    return True

def test_web_endpoints():
    """Test the web application endpoints"""
    print("\nTesting Web Endpoints...")
    
    base_url = "http://127.0.0.1:5000"
    
    endpoints_to_test = [
        ("/", "GET", "Main dashboard"),
        ("/alerts", "GET", "Alerts page"),
        ("/api/stocks", "GET", "Stocks API"),
        ("/api/alerts", "GET", "Alerts API"),
        ("/api/market_summary", "GET", "Market summary API"),
    ]
    
    for endpoint, method, description in endpoints_to_test:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"[OK] {description}: {response.status_code}")
            else:
                print(f"[WARN] {description}: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] {description}: Connection failed - {e}")
    
    return True

def test_add_sample_stocks():
    """Add sample stocks via API for demonstration"""
    print("\nAdding sample stocks via API...")
    
    base_url = "http://127.0.0.1:5000"
    sample_stocks = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA']
    
    for symbol in sample_stocks:
        try:
            response = requests.post(
                f"{base_url}/add_stock",
                data={'symbol': symbol},
                timeout=10
            )
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"[OK] Added {symbol} successfully")
                else:
                    print(f"[ERROR] Failed to add {symbol}: {result.get('message')}")
            else:
                print(f"[ERROR] HTTP error adding {symbol}: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Connection error adding {symbol}: {e}")
    
    return True

def test_create_sample_alerts():
    """Create sample alerts via API"""
    print("\nCreating sample alerts via API...")
    
    base_url = "http://127.0.0.1:5000"
    sample_alerts = [
        ('AAPL', 'price_above', 200.0),
        ('GOOGL', 'price_below', 100.0),
        ('MSFT', 'percentage_change', 5.0),
        ('TSLA', 'volume_spike', 1000000),
        ('NVDA', 'price_above', 1000.0),
    ]
    
    for symbol, alert_type, target_value in sample_alerts:
        try:
            response = requests.post(
                f"{base_url}/create_alert",
                data={
                    'symbol': symbol,
                    'alert_type': alert_type,
                    'target_value': target_value,
                    'sound_enabled': True,
                    'browser_notifications': True
                },
                timeout=10
            )
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"[OK] Created {alert_type} alert for {symbol} at {target_value}")
                else:
                    print(f"[ERROR] Failed to create alert for {symbol}: {result.get('message')}")
            else:
                print(f"[ERROR] HTTP error creating alert for {symbol}: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Connection error creating alert for {symbol}: {e}")
    
    return True

def main():
    """Main test function"""
    print("Enhanced Stock Watchlist Application Test Suite")
    print("=" * 60)
    
    # Test stock manager functionality
    try:
        test_stock_manager()
    except Exception as e:
        print(f"Stock manager test failed: {e}")
    
    print("\n" + "=" * 60)
    
    # Wait a moment for any startup
    print("Waiting for application to be ready...")
    time.sleep(2)
    
    # Test web endpoints
    try:
        test_web_endpoints()
    except Exception as e:
        print(f"Web endpoint test failed: {e}")
    
    print("\n" + "=" * 60)
    
    # Test adding sample data
    try:
        test_add_sample_stocks()
    except Exception as e:
        print(f"Sample stocks test failed: {e}")
    
    print("\n" + "=" * 60)
    
    # Test creating sample alerts
    try:
        test_create_sample_alerts()
    except Exception as e:
        print(f"Sample alerts test failed: {e}")
    
    print("\n" + "=" * 60)
    print("Test suite completed!")
    print("\nNext steps:")
    print("1. Open http://127.0.0.1:5000 in your browser")
    print("2. Enable browser notifications when prompted")
    print("3. Monitor real-time stock updates and alerts")
    print("4. Try adding/removing stocks and creating alerts")

if __name__ == "__main__":
    main()
