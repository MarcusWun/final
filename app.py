# This is the main flask application for the tradder application. This file contains the main routes and logic for the application.

from helpers import login_required, usd
from flask import Flask, jsonify, render_template, redirect, render_template, session, flash, url_for, request
from flask_session import Session
from flask_bcrypt import Bcrypt
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from cs50 import SQL
from datetime import datetime 
import yfinance as yf
import time
import sqlite3
import requests


# Configure application
app = Flask(__name__)

# Configure session manager
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure password encryption
bcrypt = Bcrypt(app)

# initialize sqlite3 database access
db = SQL("sqlite:///fp_database.db")

# create global list of dictionaries for portfolio and watch list
# portfolio is a dictionaries with each symbol being a key and the value being another dictionary with keys for shares and price
# watchlist is a list of dictionaories with keys: symbol
portfolio = {}
symbol_list = []
watchlist = []

# until registration, login and logout are created, I am using a global variable for user_id
# user_id = 1

# Class for the registration form
class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')
    def validate_username(self, username):
        user = db.execute("SELECT * FROM users WHERE username = ?", username.data)
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')


# Class for login form
class LoginForm(FlaskForm):
    username = StringField(
               'Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


# This is the route for the home page
@app.route("/")
@app.route("/index")
@login_required
def index():

    portfolio.clear()
    symbol_list.clear()
    watchlist.clear()

    # initiallize portfolio which is a dictionary with a key for each symbol
    # initialize stock_list, which is a list with the symbols in the portfolio

    rows = db.execute(
        "SELECT symbol, SUM(shares) AS shares_per_symbol, price FROM history WHERE user_id = ? GROUP BY symbol", session['user_id'])
    
    print(rows)

    for row in rows:
        if int(row['shares_per_symbol']) > 0:
            portfolio[row['symbol']] = {'shares': row['shares_per_symbol'], 'purchasePrice': row['price']}
            symbol_list.append(row['symbol'])

    # initialize list of stocks in watchlist
    rows = db.execute(
        "SELECT symbol FROM watchlist WHERE user_id = ? GROUP BY symbol", session['user_id'])
    for row in rows:
        watchlist.append(row["symbol"])

    return render_template("index.html", title='Portfolio')


# This route will handle the AJAX request for the quote page
@app.route("/quote")
@login_required
def quote():
    return render_template("quote.html", title="Market Quote")


# This route will handle the buy request for a stock
@app.route("/buy", methods=['GET', 'POST'])
@login_required
def buy():

    if request.method == 'POST':
        # Handle the form submission for buying stocks

        symbol = request.form.get('symbol').upper()  # Get the symbol from the request args if available
        if not symbol:
            flash('Please provide a stock symbol.', 'danger')
            return render_template("buy.html", title="Buy Stock")

        shares = int(request.form.get('shares'))  # Get the shares from the request args if available
        if not shares:
            flash('Please provide the number of shares.', 'danger')
            return render_template("buy.html", title="Buy Stock")
        if shares <= 0:
            flash('Shares must be a positive integer.', 'danger')
            return render_template("buy.html", title="Buy Stock")   

        try:
            stock = yf.Ticker(symbol)
            info = stock.info
        except Exception as e:
            flash('Invalid stock symbol. Please try again.', 'danger')
            return render_template("buy.html", title="Buy Stock")

        purchase_price = info.get('regularMarketPrice')
        if purchase_price is None:
            flash('Could not retrieve stock price. Please try again.', 'danger')
            return render_template("buy.html", title="Buy Stock")
        
        query = db.execute("SELECT cash_available FROM users WHERE id = ?", session['user_id'])
        if len(query) != 1:
            flash('User not found.', 'danger')
            return render_template("buy.html", title="Buy Stock")
        cash_available = query[0]['cash_available']
        
        if cash_available is None:
            flash('Could not retrieve user cash available.', 'danger')
            return render_template("buy.html", title="Buy Stock")
        
        if cash_available < float(purchase_price) * int(shares):
            flash('Insufficient funds to complete this transaction.', 'danger')
            return render_template("buy.html", title="Buy Stock")
        
        # Update the user's cash available
        new_cash_available = cash_available - (float(purchase_price) * int(shares))
        db.execute(
            "UPDATE users SET cash_available = ? WHERE id = ?",
            new_cash_available, session['user_id']
        )

        # Insert the transaction into the history table
        db.execute(
            "INSERT INTO history (user_id, symbol, shares, price) VALUES (?, ?, ?, ?)",
            session['user_id'], symbol, int(shares), float(purchase_price)
        )

        flash(
            f'Successfully purchased {shares} shares of {symbol} at {usd(float(purchase_price))}.',
            'success'
        )
        
        return redirect(url_for('index'))  # Redirect to the index page after successful purchase

    cash_available = db.execute(
        "SELECT cash_available FROM users WHERE id = ?",
        session['user_id']
    )
    flash('You have {} available to invest.'.format(usd(cash_available[0]['cash_available'])) 
          if cash_available and len(cash_available) == 1 
          else 'Could not retrieve your cash available.', 'info')
    return render_template("buy.html", title="Buy Stock")


# This is the route for the sell page, which will handle both GET and POST requests
@app.route("/sell", methods=['GET', 'POST'])
@login_required
def sell():

    if request.method == 'POST':
        # Handle the form submission for buying stocks
        symbol = request.form.get('symbol').upper()  # Get the symbol from the request args if available
        if not symbol:
            flash('Please provide a stock symbol.', 'danger')
            return render_template("sell.html", title="Sell Stock")
        
        shares = int(request.form.get('shares'))  # Get the shares from the request args if available
        if not shares:
            flash('Please provide the number of shares.', 'danger')
            return render_template("sell.html", title="Sell Stock")
        if shares <= 0:
            flash('Shares must be a positive integer.', 'danger')
            return render_template("sell.html", title="Sell Stock")
        
        query = db.execute("SELECT SUM(shares) AS total_shares FROM history WHERE user_id = ? AND symbol = ?", session['user_id'], symbol)
        if len(query) != 1 or query[0]['total_shares'] is None:
            flash('You do not own any shares of {}.'.format(symbol), 'danger')
            return render_template("sell.html", title="Sell Stock")

        total_shares = query[0]['total_shares']
        if total_shares < shares:
            flash('You cannot sell more shares than you own. You currently own {} shares.'.format(total_shares), 'danger')
            return render_template("sell.html", title="Sell Stock")

        # Get the current market price for the stock
        stock = yf.Ticker(symbol)
        info = stock.info
        if info is None or info.get('regularMarketPrice') is None:
            flash('Could not retrieve stock price. Please try again.', 'danger')
            return render_template("sell.html", title="Sell Stock")
            
        market_price = info.get('regularMarketPrice')

        # Update the user's cash available
        new_cash_available = db.execute("SELECT cash_available FROM users WHERE id = ?", session['user_id'])[0]['cash_available'] + (float(market_price) * int(shares))
        db.execute("UPDATE users SET cash_available = ? WHERE id = ?", new_cash_available, session['user_id'])

        # Insert the transaction into the history table
        db.execute("INSERT INTO history (user_id, symbol, shares, price) VALUES (?, ?, ?, ?)",session['user_id'], symbol, -int(shares), float(market_price))

        flash(f'Successfully sold {shares} shares of {symbol} at {usd(float(market_price))}.', 'success')
        return redirect(url_for('index'))  # Redirect to the index page after successful sale
    
    rows = db.execute("SELECT symbol FROM history WHERE user_id = ? GROUP BY symbol", session['user_id'])
    ticker_list = []
    if len(rows) > 0:
        # Populate the ticker list with symbols the user owns
        for row in rows:
            ticker_list.append(row['symbol'])
        # Render the sell form with the list of symbols
        return render_template("sell.html", title="Sell Stock", ticker_list=ticker_list)
    else:
        flash('You do not own any stocks to sell.', 'info')
        return redirect(url_for('index'))  # Redirect to the index page if no stocks are owned


@app.route("/history")
@login_required
def history():
    """
    Route to display the user's transaction history.
    """
    # Query the database for the user's transaction history
    transactions = db.execute(
        "SELECT symbol, shares, price, created_at FROM history WHERE user_id = ? ORDER BY created_at DESC",
        session['user_id']
    )

    if len(transactions) == 0:
        flash('No transaction history found.', 'info')
        return redirect(url_for('index'))

    for transaction in transactions:
        if transaction['shares'] < 0:
            # If shares are negative, it indicates a sale
            transaction['action'] = 'Sold'
        else:
            # Otherwise, it's a purchase
            transaction['action'] = 'Purchased' 

    return render_template("history.html", title="Transaction History", transactions=transactions)


# register route
@app.route("/register", methods=['GET', 'POST'])
def register():
    
    form = RegistrationForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        db.execute("INSERT INTO users (username, hash, cash_available, cash_funded) VALUES(?, ?, ?, ?)",
                   form.username.data, hashed_password, 10000, 10000)
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


# login route
@app.route("/login", methods=['GET', 'POST'])
def login():
  
    form = LoginForm()

    if form.validate_on_submit():

        query = db.execute("SELECT * FROM users WHERE username = ?", form.username.data)

        if len(query) == 1 and bcrypt.check_password_hash(query[0]['hash'], form.password.data):            
            session["user_id"] = query[0]["id"]
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')

    return render_template('login.html', title='Login', form=form)


# logout route
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('about'))


# This is just the cash management page, which allows the user to fund their account with cash.
@app.route("/cash_management", methods=['GET', 'POST'])
@login_required
def cash_management():

    if request.method == 'POST':
        # Handle the form submission for funding the account
        amount = request.form.get('amount', type=float)
        if amount is None:
            return redirect(url_for('index'))  # Redirect to home page if no amount is provided
        
        action = request.form.get('action').lower()  # Get the action (add or subtract)
        if action not in ['add', 'subtract']:
            flash('Invalid action specified. Please choose either "add" or "subtract".', 'danger')
            return redirect(url_for('cash_management'))
        
        if action == 'subtract':
            amount = -abs(amount)  # Ensure the amount is negative for subtraction

        query = db.execute("SELECT cash_available, cash_funded FROM users WHERE id = (?)", session["user_id"])
        cash_available = float(query[0]['cash_available']) if len(query) == 1 else None
        cash_funded = float(query[0]['cash_funded']) if len(query) == 1 else None

        if action == "subtract" and (cash_available is None or cash_available < abs(amount)):
            # Prevent subtracting more than available
            flash('Insufficient funds to subtract that amount.', 'danger')
            return redirect(url_for('cash_management'))
        
        cash_available = cash_available + amount
        cash_funded = cash_funded + amount  # Update the cash_funded to reflect the total funds added/subtracted

        db.execute("UPDATE users SET cash_available = ?, cash_funded = ? WHERE id = ?",
                   cash_available, cash_funded, session["user_id"])
        
        flash_message = 'Successfully added ${:.2f} to your account.'.format(amount) if action == 'add' else 'Successfully withdrew ${:.2f} from your account.'.format(abs(amount))
        flash(flash_message, 'success')
        return redirect(url_for('index'))  # Redirect to the index page after successful funding
    
    query = db.execute("SELECT cash_available FROM users WHERE id = (?)", session["user_id"])
    balance = float(query[0]['cash_available']) if len(query) == 1 else None
    flash_message = 'You currently have ${:.2f} available in your account.'.format(balance) if balance is not None else 'Could not retrieve your cash available.'
    if balance is not None:
        flash(flash_message, 'info')
    else:   
        # Handle the case where the user's cash_available could not be retrieved
        flash('Could not retrieve your cash available. Please try again later.', 'danger')
        return redirect(url_for('index'))
    return render_template("cash.html", title="Cash Management", balance=balance)
            

# This is just a dummy page
@app.route("/about")
def about():
    return render_template('about.html', title='About')


# This routine is called from the index page, updates martket information and returns dictionary stocks
@app.route("/api/stock")
def get_stock():

    stocks = {}

    for symbol in symbol_list:

        ticker = yf.Ticker(symbol)
        try:
            stock_info = ticker.info
            regularMarketPrice = stock_info.get('regularMarketPrice')
        except Exception as e:
            regularMarketPrice = None  # Add error handling as needed.

        stocks[symbol] = {
            "marketPrice": usd(regularMarketPrice),
            "purchasePrice": portfolio[symbol]['purchasePrice'],
            "shares": portfolio[symbol]['shares'],
            "gain": usd(float(portfolio[symbol]['shares']) * (regularMarketPrice - float(portfolio[symbol]['purchasePrice']))),
            "total": usd(regularMarketPrice * float(portfolio[symbol]['shares'])),
            "timestamp": time.time()
        }
    return jsonify(stocks)


@app.route("/get_stock_data", methods=["POST"])
def get_stock_data():
    data = request.get_json()
    symbol = data.get("symbol")
    if not symbol:
        return jsonify({"error": "Missing symbol"}), 400

    try:
        stock = yf.Ticker(symbol)
        info = stock.info

        hist = stock.history(period="6mo", interval="1d")
        hist = hist.dropna()
        chart_data = {
            "dates": hist.index.strftime("%Y-%m-%d").tolist(),
            "prices": hist["Close"].round(2).tolist()
        }

        # My own list of fields
        stock_data = {
            "Symbol": symbol.upper(),
            "Name": info.get('longName', 'Name not found'),
            "Current Price": info.get("currentPrice"),
            "Previous Close": info.get("previousClose"),
            "Open": info.get("open"),
            "Volume": info.get("volume"),
            "Average Volume": info.get("averageVolume"),
            "Market Cap": info.get("marketCap"),
            "PE Ratio": info.get("trailingPE"),
            "1Y Target Estimate": info.get("targetMeanPrice"),
            "52 Week High": info.get("fiftyTwoWeekHigh"),
            "chart": chart_data  # Include the chart data in the response
        }

        print(stock_data)  # For debugging purposes, to see the stock data being returned

        return jsonify(stock_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500




if __name__ == "__main__":
    app.run(debug=True)
