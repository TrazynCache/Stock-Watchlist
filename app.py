from flask import Flask, render_template, request, redirect, url_for, flash
from stock_manager import StockManager

app = Flask(__name__) #Creates Flask app instance.
app.secret_key = "supersecretkey"
stock_manager = StockManager() #Initalises StockManager class from stock_manager.py.

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        symbol = request.form["symbol"] #Get form data
        try:
            target_price = float(request.form["target_price"])
            stock_manager.add_stock(symbol, target_price)
            return redirect(url_for("index")) # Redirect to refresh page
        except ValueError:
            flash("Invalid target price. Please enter a valid number.")
            return redirect(url_for("index"))
    stocks = stock_manager.get_all_stocks()
    return render_template("index.html", stocks=stocks)

@app.route("/alerts")
def alerts():
    alerts = stock_manager.get_alerts()
    return render_template("alerts.html", alerts=alerts)

if __name__ == "__main__":
    app.run(debug=True)