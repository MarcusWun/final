from helpers import login_required, usd
from flask import Flask, jsonify, render_template, redirect, render_template, session, flash, url_for, request
from flask_session import Session
from flask_bcrypt import Bcrypt
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from cs50 import SQL
# from werkzeug.security import check_password_hash, generate_password_hash
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
# fd_database has two tables as follows:
# schema CREATE TABLE users (
# id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT NOT NULL, hash TEXT NOT NULL, 
# cash_funded NUMERIC NOT NULL DEFAULT 10000.00, cash_available NUMERIC DEFAULT 10000.00)
# schema CREATE TABLE history (
# transaction_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, symbol TEXT, shares INTEGER, price NUMERIC, 
# created_at DATETIME DEFAULT TIMESTAMP)
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


@app.route("/quote")
@login_required
def quote():
    return render_template("quote.html", title="Market Quote")


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

        # You can customize these fields as you wish
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
        }

        return jsonify(stock_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500




if __name__ == "__main__":
    app.run(debug=True)
