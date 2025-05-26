import csv
import yfinance as yf
import requests
import finnhub
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from alpha_vantage.timeseries import TimeSeries
from dataclasses import dataclass, asdict
from enum import Enum


class AlertType(Enum):
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    PERCENTAGE_CHANGE = "percentage_change"
    VOLUME_SPIKE = "volume_spike"
    RSI_OVERSOLD = "rsi_oversold"
    RSI_OVERBOUGHT = "rsi_overbought"


class AlertStatus(Enum):
    ACTIVE = "active"
    TRIGGERED = "triggered"
    DISABLED = "disabled"


@dataclass
class StockAlert:
    id: str
    symbol: str
    alert_type: AlertType
    threshold: float
    status: AlertStatus
    created_at: str
    triggered_at: Optional[str] = None
    sound_enabled: bool = True
    notification_enabled: bool = True
    message: str = ""


@dataclass
class StockData:
    symbol: str
    current_price: float
    previous_close: float
    day_change: float
    day_change_percent: float
    volume: int
    market_cap: Optional[float]
    pe_ratio: Optional[float]
    dividend_yield: Optional[float]
    week_52_high: Optional[float]
    week_52_low: Optional[float]
    last_updated: str
    exchange: str = ""
    company_name: str = ""


class StockManager:
    def __init__(self, csv_file="data/stocks.csv", alerts_file="data/alerts.csv"):
        self.csv_file = csv_file
        self.alerts_file = alerts_file
        self.stocks = self.load_stocks()
        self.alerts = self.load_alerts()
        
        # Initialize API clients
        self.finnhub_client = None
        self.alpha_vantage_client = None
        self._init_api_clients()
        
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)

    def _init_api_clients(self):
        """Initialize external API clients if API keys are available"""
        try:
            # Initialize Finnhub client (free tier available)
            finnhub_key = os.getenv('FINNHUB_API_KEY', 'demo')  # Use demo key if none provided
            self.finnhub_client = finnhub.Client(api_key=finnhub_key)
            
            # Initialize Alpha Vantage client (optional)
            alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY')
            if alpha_vantage_key:
                self.alpha_vantage_client = TimeSeries(key=alpha_vantage_key, output_format='pandas')
        except Exception as e:
            print(f"API initialization warning: {e}")

    def load_stocks(self) -> List[Dict]:
        """Load stocks from CSV file"""
        try:
            with open(self.csv_file, mode="r", newline="") as file:
                reader = csv.DictReader(file)
                return list(reader)
        except FileNotFoundError:
            return []

    def load_alerts(self) -> List[StockAlert]:
        """Load alerts from CSV file"""
        try:
            with open(self.alerts_file, mode="r", newline="") as file:
                reader = csv.DictReader(file)
                alerts = []
                for row in reader:
                    alert = StockAlert(
                        id=row['id'],
                        symbol=row['symbol'],
                        alert_type=AlertType(row['alert_type']),
                        threshold=float(row['threshold']),
                        status=AlertStatus(row['status']),
                        created_at=row['created_at'],
                        triggered_at=row.get('triggered_at'),
                        sound_enabled=row.get('sound_enabled', 'True').lower() == 'true',
                        notification_enabled=row.get('notification_enabled', 'True').lower() == 'true',
                        message=row.get('message', '')
                    )
                    alerts.append(alert)
                return alerts
        except FileNotFoundError:
            return []

    def save_stocks(self):
        """Save stocks to CSV file"""
        fieldnames = ["symbol", "current_price", "previous_close", "day_change", 
                     "day_change_percent", "volume", "market_cap", "pe_ratio", 
                     "dividend_yield", "week_52_high", "week_52_low", "last_updated",
                     "exchange", "company_name"]
        
        with open(self.csv_file, mode="w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.stocks)

    def save_alerts(self):
        """Save alerts to CSV file"""
        fieldnames = ["id", "symbol", "alert_type", "threshold", "status", 
                     "created_at", "triggered_at", "sound_enabled", 
                     "notification_enabled", "message"]
        
        with open(self.alerts_file, mode="w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for alert in self.alerts:
                writer.writerow(asdict(alert))

    def fetch_comprehensive_stock_data(self, symbol: str) -> Optional[StockData]:
        """Fetch comprehensive stock data from multiple sources"""
        try:
            # Primary data from yfinance
            stock = yf.Ticker(symbol)
            info = stock.info
            hist = stock.history(period="2d")
            
            if hist.empty:
                return None
                
            current_price = round(hist["Close"].iloc[-1], 2)
            previous_close = round(hist["Close"].iloc[-2] if len(hist) > 1 else current_price, 2)
            volume = int(hist["Volume"].iloc[-1])
            
            day_change = current_price - previous_close
            day_change_percent = (day_change / previous_close) * 100 if previous_close > 0 else 0
            
            # Extract additional data from yfinance info
            market_cap = info.get('marketCap')
            pe_ratio = info.get('forwardPE') or info.get('trailingPE')
            dividend_yield = info.get('dividendYield')
            week_52_high = info.get('fiftyTwoWeekHigh')
            week_52_low = info.get('fiftyTwoWeekLow')
            exchange = info.get('exchange', '')
            company_name = info.get('longName', symbol)
            
            return StockData(
                symbol=symbol.upper(),
                current_price=current_price,
                previous_close=previous_close,
                day_change=round(day_change, 2),
                day_change_percent=round(day_change_percent, 2),
                volume=volume,
                market_cap=market_cap,
                pe_ratio=pe_ratio,
                dividend_yield=dividend_yield,
                week_52_high=week_52_high,
                week_52_low=week_52_low,
                last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                exchange=exchange,
                company_name=company_name
            )
            
        except Exception as e:
            print(f"Error fetching comprehensive data for {symbol}: {e}")
            return None

    def add_stock(self, symbol: str) -> bool:
        """Add a stock to the watchlist"""
        symbol = symbol.upper()
        
        # Check if stock already exists
        if any(stock['symbol'] == symbol for stock in self.stocks):
            return False
            
        stock_data = self.fetch_comprehensive_stock_data(symbol)
        if stock_data:
            self.stocks.append(asdict(stock_data))
            self.save_stocks()
            return True
        return False

    def remove_stock(self, symbol: str) -> bool:
        """Remove a stock from the watchlist"""
        symbol = symbol.upper()
        initial_length = len(self.stocks)
        self.stocks = [stock for stock in self.stocks if stock['symbol'] != symbol]
        
        if len(self.stocks) < initial_length:
            self.save_stocks()
            return True
        return False

    def add_alert(self, symbol: str, alert_type: AlertType, threshold: float, 
                  sound_enabled: bool = True, notification_enabled: bool = True,
                  message: str = "") -> str:
        """Add a new alert"""
        alert_id = f"{symbol}_{alert_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        alert = StockAlert(
            id=alert_id,
            symbol=symbol.upper(),
            alert_type=alert_type,
            threshold=threshold,
            status=AlertStatus.ACTIVE,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            sound_enabled=sound_enabled,
            notification_enabled=notification_enabled,
            message=message or f"{symbol} {alert_type.value} alert at {threshold}"
        )
        
        self.alerts.append(alert)
        self.save_alerts()
        return alert_id

    def check_alerts(self) -> List[StockAlert]:
        """Check all active alerts and return triggered ones"""
        triggered_alerts = []
        
        for alert in self.alerts:
            if alert.status != AlertStatus.ACTIVE:
                continue
                
            stock_data = self.fetch_comprehensive_stock_data(alert.symbol)
            if not stock_data:
                continue
                
            triggered = False
            
            if alert.alert_type == AlertType.PRICE_ABOVE:
                triggered = stock_data.current_price >= alert.threshold
            elif alert.alert_type == AlertType.PRICE_BELOW:
                triggered = stock_data.current_price <= alert.threshold
            elif alert.alert_type == AlertType.PERCENTAGE_CHANGE:
                triggered = abs(stock_data.day_change_percent) >= alert.threshold
            elif alert.alert_type == AlertType.VOLUME_SPIKE:
                # Simple volume spike detection (you can enhance this)
                triggered = stock_data.volume >= alert.threshold
                
            if triggered:
                alert.status = AlertStatus.TRIGGERED
                alert.triggered_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                triggered_alerts.append(alert)
        
        if triggered_alerts:
            self.save_alerts()
            
        return triggered_alerts

    def get_all_stocks(self) -> List[Dict]:
        """Get all stocks with updated data"""
        updated_stocks = []
        
        for stock in self.stocks:
            stock_data = self.fetch_comprehensive_stock_data(stock['symbol'])
            if stock_data:
                updated_stocks.append(asdict(stock_data))
            else:
                updated_stocks.append(stock)
                
        self.stocks = updated_stocks
        self.save_stocks()
        return self.stocks

    def get_active_alerts(self) -> List[StockAlert]:
        """Get all active alerts"""
        return [alert for alert in self.alerts if alert.status == AlertStatus.ACTIVE]

    def get_triggered_alerts(self) -> List[StockAlert]:
        """Get all triggered alerts"""
        return [alert for alert in self.alerts if alert.status == AlertStatus.TRIGGERED]

    def disable_alert(self, alert_id: str) -> bool:
        """Disable an alert"""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.status = AlertStatus.DISABLED
                self.save_alerts()
                return True
        return False

    def get_stock_history(self, symbol: str, period: str = "1mo") -> Optional[Dict]:
        """Get historical stock data"""
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period=period)
            
            if hist.empty:
                return None
                
            # Convert to dict format for JSON serialization
            history_data = {
                'dates': [date.strftime('%Y-%m-%d') for date in hist.index],
                'prices': [round(price, 2) for price in hist['Close'].tolist()],
                'volumes': [int(vol) for vol in hist['Volume'].tolist()]
            }
            
            return history_data
        except Exception as e:
            print(f"Error fetching history for {symbol}: {e}")
            return None

    def search_stocks(self, query: str) -> List[Dict]:
        """Search for stocks by symbol or company name"""
        try:
            # Simple search using yfinance
            # This is a basic implementation - you could enhance with dedicated search APIs
            query = query.upper()
            results = []
            
            # Try to get ticker info
            try:
                ticker = yf.Ticker(query)
                info = ticker.info
                if info and 'longName' in info:
                    results.append({
                        'symbol': query,
                        'name': info.get('longName', ''),
                        'exchange': info.get('exchange', ''),
                        'sector': info.get('sector', '')
                    })
            except:
                pass
                
            return results
        except Exception as e:
            print(f"Error searching stocks: {e}")
            return []
