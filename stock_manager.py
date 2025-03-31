import csv
import yfinance as yf
from datetime import datetime

class StockManager:
    def __init__(self, csv_file="data/stocks.csv"):
        self.csv_file = csv_file
        self.stocks = self.load_stocks() #Loads stocks from CSV on start up

    def load_stocks(self):
        try:
            with open(self.csv_file, mode="r", newline="") as file:
                reader = csv.DictReader(file) #Reads CSV into a list of dictionary
                return list(reader)
        except FileNotFoundError:
            return [] #Returns empty list if file doesn't exist yet

    def save_stocks(self):
        with open(self.csv_file, mode="w", newline="") as file:
            fieldnames = ["symbol", "target_price", "current_price", "last_updated", "trend"] #For CSV rows
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader() #Write CSV Header
            writer.writerows(self.stocks) #Write all stock data

    def fetch_price(self, symbol):
        try:
            stock = yf.Ticker(symbol)
            price = stock.history(period="1d")["Close"].iloc[-1] #Get latest closing price
            return round(price, 2)
        except Exception as e:
            print(f"Error fetching price for {symbol}: {e}")
            return None

    def add_stock(self, symbol, target_price):
        symbol = symbol.upper()
        current_price = self.fetch_price(symbol)
        last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        trend = "up" if current_price > target_price else "down" #Simple trend indicator
        new_stock = {
            "symbol": symbol,
            "target_price": float(target_price),
            "current_price": current_price,
            "last_updated": last_updated,
            "trend": trend
            }
        self.stocks.append(new_stock)
        self.save_stocks()

    def get_alerts(self):
        alerts = []
        for stock in self.stocks:
            current_price = self.fetch_price(stock["symbol"])
            if current_price is None: #skip if price fetch failed
                continue
            stock["current_price"] = current_price #Updates current price
            stock["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if current_price >= float(stock["target_price"]):
                alerts.append(stock)
        self.save_stocks() #Saves updated prices
        return alerts

    def get_all_stocks(self):
        for stock in self.stocks:
            current_price = self.fetch_price(stock["symbol"])
            if current_price is None: #SKip if price fetch failed
                continue
            stock["current_price"] = current_price #Use the already fetched price.
            stock["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            stock["trend"] = "up" if stock["current_price"] > float(stock["target_price"]) else "down"
        self.save_stocks()
        return self.stocks
