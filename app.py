from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_socketio import SocketIO, emit
from stock_manager import StockManager, AlertType, AlertStatus
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import os
from dotenv import load_dotenv
import threading
import time

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'supersecretkey_change_in_production')

# Initialize SocketIO for real-time communication
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize StockManager
stock_manager = StockManager()

# Background scheduler for periodic price checks
scheduler = BackgroundScheduler()
scheduler.start()

# Global variables for real-time updates
connected_clients = set()


@app.route("/")
def index():
    """Main dashboard showing all stocks"""
    stocks = stock_manager.get_all_stocks()
    active_alerts = stock_manager.get_active_alerts()
    return render_template("index.html", stocks=stocks, active_alerts=active_alerts)


@app.route("/add_stock", methods=["POST"])
def add_stock():
    """Add a new stock to the watchlist"""
    symbol = request.form.get("symbol", "").strip()
    
    if not symbol:
        flash("Please enter a stock symbol.", "error")
        return redirect(url_for("index"))
    
    success = stock_manager.add_stock(symbol)
    if success:
        flash(f"Successfully added {symbol.upper()} to your watchlist!", "success")
        # Emit real-time update to all connected clients
        socketio.emit('stock_added', {'symbol': symbol.upper()})
    else:
        flash(f"Failed to add {symbol.upper()}. Check if the symbol is valid or already exists.", "error")
    
    return redirect(url_for("index"))


@app.route("/remove_stock/<symbol>", methods=["POST"])
def remove_stock(symbol):
    """Remove a stock from the watchlist"""
    success = stock_manager.remove_stock(symbol)
    if success:
        flash(f"Removed {symbol} from your watchlist.", "success")
        socketio.emit('stock_removed', {'symbol': symbol})
    else:
        flash(f"Failed to remove {symbol}.", "error")
    
    return redirect(url_for("index"))


@app.route("/alerts")
def alerts():
    """Alerts management page"""
    active_alerts = stock_manager.get_active_alerts()
    triggered_alerts = stock_manager.get_triggered_alerts()
    alert_types = [alert_type.value for alert_type in AlertType]
    
    return render_template("alerts.html", 
                         active_alerts=active_alerts,
                         triggered_alerts=triggered_alerts,
                         alert_types=alert_types)


@app.route("/add_alert", methods=["POST"])
def add_alert():
    """Add a new price alert"""
    try:
        symbol = request.form.get("symbol", "").strip().upper()
        alert_type = AlertType(request.form.get("alert_type"))
        threshold = float(request.form.get("threshold"))
        sound_enabled = request.form.get("sound_enabled") == "on"
        notification_enabled = request.form.get("notification_enabled", "on") == "on"
        message = request.form.get("message", "").strip()
        
        alert_id = stock_manager.add_alert(
            symbol=symbol,
            alert_type=alert_type,
            threshold=threshold,
            sound_enabled=sound_enabled,
            notification_enabled=notification_enabled,
            message=message
        )
        
        flash(f"Alert created successfully! Alert ID: {alert_id}", "success")
        
    except ValueError as e:
        flash(f"Invalid input: {str(e)}", "error")
    except Exception as e:
        flash(f"Error creating alert: {str(e)}", "error")
    
    return redirect(url_for("alerts"))


@app.route("/disable_alert/<alert_id>", methods=["POST"])
def disable_alert(alert_id):
    """Disable an alert"""
    success = stock_manager.disable_alert(alert_id)
    if success:
        flash("Alert disabled successfully.", "success")
    else:
        flash("Failed to disable alert.", "error")
    
    return redirect(url_for("alerts"))


@app.route("/api/stock/<symbol>")
def get_stock_data(symbol):
    """API endpoint to get current stock data"""
    stock_data = stock_manager.fetch_comprehensive_stock_data(symbol)
    if stock_data:
        return jsonify(stock_data.__dict__)
    else:
        return jsonify({"error": "Stock not found"}), 404


@app.route("/api/stock/<symbol>/history")
def get_stock_history(symbol):
    """API endpoint to get stock price history"""
    period = request.args.get('period', '1mo')
    history = stock_manager.get_stock_history(symbol, period)
    if history:
        return jsonify(history)
    else:
        return jsonify({"error": "History not available"}), 404


@app.route("/api/search")
def search_stocks():
    """API endpoint to search for stocks"""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    
    results = stock_manager.search_stocks(query)
    return jsonify(results)


@app.route("/api/watchlist")
def get_watchlist():
    """API endpoint to get current watchlist"""
    stocks = stock_manager.get_all_stocks()
    return jsonify(stocks)


@app.route("/api/alerts/check")
def check_alerts_api():
    """API endpoint to manually check alerts"""
    triggered_alerts = stock_manager.check_alerts()
    
    # Send real-time notifications for triggered alerts
    for alert in triggered_alerts:
        socketio.emit('alert_triggered', {
            'symbol': alert.symbol,
            'message': alert.message,
            'threshold': alert.threshold,
            'alert_type': alert.alert_type.value,
            'sound_enabled': alert.sound_enabled,
            'notification_enabled': alert.notification_enabled,
            'triggered_at': alert.triggered_at
        })
    
    return jsonify([{
        'id': alert.id,
        'symbol': alert.symbol,
        'message': alert.message,
        'triggered_at': alert.triggered_at
    } for alert in triggered_alerts])


# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    connected_clients.add(request.sid)
    emit('connected', {'message': 'Connected to stock watchlist'})
    print(f"Client {request.sid} connected")


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    connected_clients.discard(request.sid)
    print(f"Client {request.sid} disconnected")


@socketio.on('request_update')
def handle_update_request():
    """Handle manual update request from client"""
    stocks = stock_manager.get_all_stocks()
    emit('stocks_updated', stocks)


def check_alerts_background():
    """Background task to check alerts periodically"""
    while True:
        try:
            triggered_alerts = stock_manager.check_alerts()
            
            if triggered_alerts and connected_clients:
                for alert in triggered_alerts:
                    socketio.emit('alert_triggered', {
                        'symbol': alert.symbol,
                        'message': alert.message,
                        'threshold': alert.threshold,
                        'alert_type': alert.alert_type.value,
                        'sound_enabled': alert.sound_enabled,
                        'notification_enabled': alert.notification_enabled,
                        'triggered_at': alert.triggered_at
                    })
            
            time.sleep(30)  # Check every 30 seconds
        except Exception as e:
            print(f"Error in background alert checking: {e}")
            time.sleep(60)  # Wait longer on error


def update_prices_background():
    """Background task to update stock prices periodically"""
    while True:
        try:
            if connected_clients:
                stocks = stock_manager.get_all_stocks()
                socketio.emit('stocks_updated', stocks)
            
            time.sleep(60)  # Update every minute
        except Exception as e:
            print(f"Error in background price update: {e}")
            time.sleep(120)  # Wait longer on error


# Start background threads
if __name__ == "__main__":
    # Start background tasks
    alert_thread = threading.Thread(target=check_alerts_background, daemon=True)
    price_thread = threading.Thread(target=update_prices_background, daemon=True)
    
    alert_thread.start()
    price_thread.start()
    
    # Run the app
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)