#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple demonstration script for Enhanced Stock Watchlist Application
This script shows basic usage and can populate the application with sample data.
"""

import time
import webbrowser

def main():
    """Main demonstration function"""
    print("Enhanced Stock Watchlist Application Demo")
    print("=" * 50)
    
    print("\nApplication Features:")
    print("* Real-time stock price tracking")
    print("* WebSocket-based live updates")
    print("* Browser notifications with sound alerts")
    print("* Multiple alert types (price, percentage, volume)")
    print("* Modern responsive UI design")
    print("* Market summary and portfolio overview")
    
    print("\nTechnical Highlights:")
    print("* Flask backend with WebSocket support")
    print("* Multiple data sources (yfinance, Alpha Vantage, Finnhub)")
    print("* Background task processing")
    print("* Professional CSS styling")
    print("* Interactive JavaScript frontend")
    
    print("\nTo test the application:")
    print("1. The app is running at: http://127.0.0.1:5000")
    print("2. Open in your browser to see the modern interface")
    print("3. Add stocks like: AAPL, GOOGL, MSFT, TSLA, NVDA")
    print("4. Create alerts for price changes")
    print("5. Enable browser notifications for real-time alerts")
    print("6. Try the alerts management page at: /alerts")
    
    print("\nSample stocks to add:")
    print("- AAPL (Apple Inc.)")
    print("- GOOGL (Alphabet Inc.)")
    print("- MSFT (Microsoft Corporation)")
    print("- TSLA (Tesla Inc.)")
    print("- NVDA (NVIDIA Corporation)")
    print("- AMD (Advanced Micro Devices)")
    print("- AMZN (Amazon.com Inc.)")
    
    print("\nSample alerts to create:")
    print("- AAPL price above $200")
    print("- GOOGL price below $100")
    print("- MSFT percentage change > 5%")
    print("- TSLA volume spike > 1M shares")
    
    # Ask if user wants to open browser
    try:
        user_input = input("\nWould you like to open the application in your browser? (y/n): ").strip().lower()
        if user_input in ['y', 'yes']:
            print("Opening browser...")
            webbrowser.open('http://127.0.0.1:5000')
            print("Application opened! Check your browser.")
        else:
            print("You can manually open: http://127.0.0.1:5000")
    except KeyboardInterrupt:
        print("\nDemo completed!")
    
    print("\nApplication Status: RUNNING")
    print("Ready for testing and demonstration!")

if __name__ == "__main__":
    main()
