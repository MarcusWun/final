# Project PRO Trader

#### Video demo (to come)

#### Description

This project is a Flask-based web application designed to provide live market data and manage user interactions effectively. It leverages several key technologies, including the `yfinance` library for fetching live stock market data, `sqlite3` for database management of user account and portfolio related data, and `Flask-WTF` for handling forms with the option to provide feedback related to user input, such as missing or non-matchiong passwords. 

I reused some of the frameworks of the last CS50x project, finance, with the intention to improve its shortcomings.  Examples include:

- I wanted all relevant information on each page even if a user makes a mistake or doesn't fill in the required information.  I didn't like the grumpy cat page in finance, which gives you very basic information and then you have to navigate back to the original page and try again.  In my app, everything happens on the same page until the users succeeds.  This is accoomplished using the flash() function which comes with flask.

User input verification is accomplished by flask-wtf: https://pypi.org/project/Flask-WTF/

Note that WTForms is a flexible forms validation and rendering library for Python web development.

- Stock data should be updated live with real market information.  Yfinance offers an API free of charge to pull market data given a certain ticker symbol.  On my index.html page is a Javascript function that is triggered every 5 seconds and pulls live data through the Yfinance API and then updates the table with stocks.  This even works outside of the normal trading hours of the stock exchanges, 9:30am to 4:00pm ET, in which case the API provides data at close of the previous trading session.

The documentation is here: https://yfinance-python.org/index.html

- The same idea of providing real market data applies to providing a quote for a given stock symbol.  Quote.html pulls a lot of market data through the Yfinance API that may be of interest for a potential investor using the platform, such as target price for a stock and also a 6-month price chart allowing the user to make an informed decision when contemplating a stock purchase.

Below is a detailed summary of the project's components:

## Flask `app.py`
The `app.py` file is the backbone of the application. It initializes the Flask server, defines the routes, and facilitates the integration of various libraries and tools. Key functionalities include:
- **Routing**: The file defines routes for rendering HTML templates and handling user requests.
- **Database Integration**: It connects to an SQLite3 database to store and retrieve user data,hashed passwords, stock preferences, and historical price chart information.
- **Market Data Fetching**: Using the `yfinance` library, it fetches live stock data and processes it for display on the web interface.
- **Form Handling**: It integrates Flask-WTF forms for user input validation and secure data handling.

## Use of `sqlite3` Database
The application uses SQLite as its database solution due to its lightweight and serverless nature. Key aspects include:
- **User Data Management**: The database stores user profiles, login credentials, cash deposited and available, and all stock transactions (purchase and sell)
- **Integration**: The `app.py` file includes functions to interact with the database, such as adding, updating, and querying records.

## Use of `yfinance` Library
The `yfinance` library is a critical component for fetching live market data. Its usage includes:
- **Real-Time Data Retrieval**: The library pulls live stock prices, historical data, and other financial metrics.
- **Data Processing**: The fetched data is processed and formatted for display on the web interface.  I am using two Javascript files, portfolio.js and quote.js, to retrieve data using JSON functionality.
- **Customization**: App users can specify stock symbols, and the application dynamically fetches the corresponding data.

## Use of Flask-WTF Forms
Flask-WTF is used to handle user input securely and efficiently. Key features include:
- **Form Validation**: Ensures that user inputs, such as stock symbols or login credentials, are valid and sanitized.
- **CSRF Protection**: Provides built-in protection against cross-site request forgery attacks.
- **Dynamic Forms**: Enables the creation of dynamic forms for user interactions, such as stock searches or account management.

