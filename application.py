from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import gettempdir
from pytz import timezone

from helpers import *

# configure application
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# custom filter
app.jinja_env.filters["usd"] = usd

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = gettempdir()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

@app.route("/")
@login_required
def index():
    
    id = session.get("user_id")
        
    current_balance = db.execute("SELECT cash FROM users WHERE id = :id", id=id)[0]["cash"]
    value = 0
    
    if db.execute("SELECT * FROM portfolio"):
        stocks = db.execute("SELECT stock, SUM(share_number) as share_sum, symbol FROM portfolio WHERE id = :id GROUP BY id,symbol", id=id)
        
        for stock in stocks:
            stock["price"] = lookup(stock["symbol"])["price"]
            stock["holding_value"] = stock["price"]*stock["share_sum"]
            if stock["holding_value"] < 0:
                stock["holding_value"] = 0
            stock["price"] = usd(stock["price"])
            value = value + stock["holding_value"]
            stock["holding_value"] = usd(stock["holding_value"])
            
        grand_total = value + current_balance

    else:
        stocks = {0}
        final_total = current_balance
        
    return render_template("index.html", stocks=stocks, current_balance=usd(current_balance), grand_total=usd(grand_total))

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    
    if request.method == "POST":
        
        if not request.form.get("symbol"):
            return apology("symbol required")
            
        elif not request.form.get("share_number"):
            return apology("number of shares required")
            
        elif int(request.form.get("share_number")) <= 0:
            return apology("number of shares must be positive integer")
    
        quote = lookup(request.form.get("symbol"))
        if quote == None:
            return apology("symbol not recognised")
        
        today = datetime.datetime.now(timezone('Europe/London')).strftime("%e/%m/%Y %H:%M")
        id = session.get("user_id")
        cash = db.execute("SELECT cash FROM users WHERE id = :id", id=id)[0]["cash"]
        share_number = int(request.form.get("share_number"))
        cost = quote["price"]*share_number
        
        if cash < quote["price"]:
            return apology("not enough cash")
            
        if cash >= quote["price"]:
            result = db.execute("INSERT INTO portfolio (id, stock, price, date, share_number, symbol) VALUES(:id, :stock, :price, :date, :share, :symbol)", id=id, stock=quote["name"], price=quote["price"], date=today, share=share_number, symbol=quote["symbol"])
        if not result:
            return apology("unable to complete transaction")
            
        cash_update = db.execute("UPDATE users SET cash = cash - :cost WHERE id = :id", cost=cost, id=id)
        if not cash_update:
            return apology("unable to update cash")
        
        return redirect(url_for("index"))
            
    else:
        return render_template("buy.html")

@app.route("/history")
@login_required
def history():
    """Show history of transactions."""
    
    id = session.get("user_id")
    
    result = db.execute("SELECT stock, price, date, share_number, symbol FROM portfolio WHERE id = :id", id=id)
    print(result)
    for res in result:
        if res["share_number"] < 0:
            res["buy_sell"] = 'SELL'
        else:
            res["buy_sell"] = 'BUY'
            
    return render_template("history.html", result=result)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))
 
        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
            return apology("invalid username and/or password")

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))

@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    
    if request.method == "POST":
        """Get stock quote."""
        if not request.form.get("symbol"):
            return apology("symbol required")
        
        quote = lookup(request.form.get("symbol"))
        if quote == None:
            return apology("symbol not recognised")
        else:
            return render_template("stock.html", quote=quote)
    
    else:
        return render_template("quote.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user."""
    
    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")
            
        # check password confirmation
        elif request.form.get("password") != request.form.get("password confirmation"):
            return apology("confirmation must match password")

        hash = pwd_context.encrypt(request.form.get("password"))
        
        result = db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)", username=request.form.get("username"), hash=hash)
        if not result:
            return apology("user already exists")
       
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))
        
        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    
    """Sell shares of stock."""
    id = session.get("user_id")
    
    if request.method == "POST":
        
        if not request.form.get("symbol"):
            return apology("symbol required")
            
        elif not request.form.get("share_number"):
            return apology("number of shares required")
        
        today = datetime.datetime.now(timezone('Europe/London')).strftime("%e/%m/%Y %H:%M")
        quote = lookup(request.form.get("symbol"))
        name = quote["name"]
        price = quote["price"]
        share_number = int(request.form.get("share_number"))
            
        result = db.execute("SELECT SUM(price) as total_price, SUM(share_number) as total_shares FROM portfolio WHERE id = :id AND stock = :name", id=id, name=name)
        if result == None:
            return apology("stock not in portfolio")
            
        if int(request.form.get("share_number")) > result[0]["total_shares"]:
            return apology("not enough shares owned")
            
        sale = db.execute("INSERT INTO portfolio (id, stock, price, date, share_number, symbol) VALUES(:id, :stock, :price, :date, :share, :symbol)", id=id, stock=name, price=-price, date=today, share=-share_number, symbol=quote["symbol"])
        if sale == None:
            return apology("unable to sell stock")
        else:
            cash_update = db.execute("UPDATE users SET cash = cash + :price WHERE id = :id", price=price, id=id)
        
        return redirect(url_for("index"))
    
    else:
        return render_template("sell.html")
        
@app.route("/credit", methods=["GET", "POST"])
@login_required
def credit():
    
    id = session.get("user_id")
    
    if request.method == "POST":
        
        if not request.form.get("cash"):
            return apology("cash required")
        else:
            credit = request.form.get("cash")
            add_cash = db.execute("UPDATE users SET cash = cash + :credit WHERE id = :id", credit=credit, id=id)
            if add_cash:
                return redirect(url_for("index"))
            else:
                return apology("cash could not be added")
    
    else:
        return render_template("credit.html")
