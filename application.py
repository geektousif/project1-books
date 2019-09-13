import os

import requests
from flask import Flask, session, render_template,request,redirect,url_for,flash, get_flashed_messages, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    if not session.get("logged_in"):
        flash('Login to Review')
        return render_template("index.html")
    else:
        books = db.execute("SELECT * FROM books").fetchall()
        return render_template("dashboard.html", name=session["user_name"],books=books)


#Register Page
@app.route("/register")
def register():
    return render_template("register.html", title='register')

#Registration
@app.route("/registration", methods=["POST"])
def registration():
    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")
    if db.execute("SELECT * FROM users WHERE email = :email", {"email":email}).fetchone() is not None:
                    return render_template("login.html", message="User Already Exist, Please Login")
    db.execute("INSERT INTO users (name, email, password) VALUES (:name, :email, :password)",
                   {"name": name, "email": email, "password": password})
    db.commit()
    return render_template("success.html",message='You Have Successfully Registered', title='register')


@app.route("/login", methods=["POST","GET"])
def login():
    return render_template('login.html')

@app.route("/dashboard",methods=['POST','GET'])
def dashboard():
    email = request.form.get("email")
    password = request.form.get("password")
    user = db.execute("SELECT * FROM users WHERE email = :email", {"email":email}).fetchone()
    if request.method == "GET":
        if session.get("logged_in"):
            flash("You are already logged in")
            return redirect(url_for('index'), "303")
        else:
            flash("You are not logged in")
            return render_template("login.html")
    if request.method == "POST":
        if user is None:
            return render_template("register.html", message="User Doesn't Exist, Please Register", title="Error")
        if email == user.email and password == user.password:
            session["logged_in"] = True
            session["user_id"] = user.id
            session["user_name"] = user.name
            session["user_email"] = user.email
            flash("Logged in successful")
            return redirect(url_for('index'), "303")
        else:
            flash('Invalid Credentials')
            return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session["logged_in"]=False
    session["user_id"] = None
    return redirect(url_for('index'))

@app.route('/search')
def search():
    param = request.args.get("search_param")
    query = request.args.get("query")
    text = query.lower()
    text = '%'+text+'%'
    if param == "Title":
        result = db.execute("SELECT * FROM books WHERE LOWER(title) LIKE :title", {"title":text}).fetchall()
    elif param == "Author":
        result = db.execute("SELECT * FROM books WHERE LOWER(author) LIKE :author", {"author":text}).fetchall()
    elif param == "ISBN":
        result = db.execute("SELECT * FROM books WHERE LOWER(isbn) LIKE :isbn", {"isbn":text}).fetchall()

    if len(result):
        return render_template('searchlist.html',books=result)
    elif len(result)==0:
        flash('No Matches Found')
        return redirect(url_for('index'))

@app.route('/id/<int:id>',methods=['POST','GET'])
def book_details(id):
    user_id = session["user_id"]
    book = db.execute("SELECT * FROM books WHERE id = :id",{"id":id}).fetchone()
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "09121sQ8cGN6mhLi4WZtQ", "isbns": book.isbn})
    session["reviews"]=[]
    if request.method== "POST":
        stars = request.form.get("stars")
        review = request.form.get("review")
        if db.execute("SELECT id FROM reviews WHERE user_id = :user_id AND book_id = :book_id",
                      {"user_id": user_id, "book_id": book.id}).fetchone() is None:
            db.execute(
                "INSERT INTO reviews (user_id, book_id, rating, review) VALUES (:user_id, :book_id, :rating, :review)",
                {"book_id": book.id, "user_id": user_id, "rating": stars, "review": review})
        else:
            db.execute(
                "UPDATE reviews SET review = :review, rating = :rating WHERE user_id = :user_id AND book_id = :book_id",
                {"review": review, "rating": stars, "user_id": user_id, "book_id": book.id})
        db.commit()
    try:
        avg_rating=res.json()['books'][0]['average_rating']
        ratings_count=res.json()['books'][0]['work_ratings_count']
        reviews = db.execute("SELECT * FROM reviews WHERE book_id = :book_id",{"book_id":id}).fetchall()
        for y in reviews:
            session["reviews"].append(y)

        if avg_rating and ratings_count is not None:
            return render_template("bookpage.html",book=book, name=session["user_name"],avg_rating=avg_rating, ratings_count=ratings_count,reviews=reviews)
    except ValueError:
        reviews = db.execute("SELECT * FROM reviews WHERE book_id = :book_id",{"book_id":id}).fetchall()
        for y in reviews:
            session["reviews"].append(y)
        return render_template("bookpage.html",book=book, name=session["user_name"],avg_rating='', ratings_count='',reviews=session['reviews'])

@app.route('/api/<isbn>',methods=['GET'])
def api(isbn):
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn",{"isbn":isbn}).fetchone()
    if book is None:
        return render_template("error.html", error_message="We got an invalid ISBN.Please check for the errors and try again.")
    reviews = db.execute("SELECT * FROM reviews WHERE book_id = :book_id", {"book_id": book.id}).fetchall()
    count = 0
    rating = 0
    for review in reviews:
        count += 1
        rating += review.rating
    if count:
        average_rating = rating / count
    else:
        average_rating = 0
    return jsonify(
        title=book.title,
        author=book.author,
        year=book.year,
        isbn=book.isbn,
        review_count=count,
        average_score=average_rating
    )

if __name__ == "__main__":
    app.run(debug=True)
