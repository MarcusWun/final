The investment app uses the yfinance libray, which can be installed with "pip install yfinance".
In order to retrieve current market price information for a certain stock, the following code will do:

The project also uses sqlite3 with the following tables in a file called fp_database.db:

schema CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT NOT NULL, hash TEXT NOT NULL, cash_funded NUMERIC NOT NULL DEFAULT 10000.00, cash_available NUMERIC DEFAULT 10000.00)

schema CREATE TABLE history (transaction_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, symbol TEXT, shares INTEGER, price NUMERIC, created_at DATETIME DEFAULT TIMESTAMP)

schema CREATE TABLE watchlist (watchlist_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, symbol TEXT,created_at DATETIME DEFAULT TIMESTAMP)


