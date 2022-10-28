import datetime

from flask import (Blueprint,
                   render_template,
                   session,
                   redirect,
                   request,
                   current_app,
                   url_for,
                   abort,
                   flash)
import uuid
import functools
from dataclasses import asdict
from passlib.hash import pbkdf2_sha256
from movie_library.forms import MovieForm, ExtendedMovieForm, RegisterForm, LoginForm
from movie_library.models import Movie, User

pages = Blueprint(
    "pages", __name__, template_folder="templates", static_folder="static"
)


def login_required(route):
    @functools.wraps(route)
    def route_wrapper(*args, **kwargs):
        if session.get("email") is None:
            return redirect(url_for(".login"))

        return route(*args, **kwargs)

    return route_wrapper


@pages.route("/")
@login_required
def index():
    user_data = current_app.db.user.find_one({"_id": session["user_id"]})
    user = User(**user_data)
    movie_data = current_app.db.movie.find({"_id": {"$in": user.movies}})
    movies = [Movie(**movie) for movie in movie_data]

    return render_template(
        "index.html",
        title="Movies Watchlist",
        movies_data=movies
    )


@pages.route("/register", methods=["GET", "POST"])
def register():
    if session.get("email"):
        return redirect(url_for(".index"))
    else:
        form = RegisterForm()

        if form.validate_on_submit():
            user = User(_id=uuid.uuid4().hex,
                        email=form.email.data,
                        password=pbkdf2_sha256.hash(form.password.data))

            current_app.db.user.insert_one(asdict(user))

            flash("User registered successfully", "success")

            return redirect(url_for(".index"))

        return render_template("register.html",
                               title="Movie WatchList - Register",
                               form=form)


@pages.route("/login", methods=["GET", "POST"])
def login():
    if session.get("email"):
        return redirect(url_for(".index"))

    form = LoginForm()

    if form.validate_on_submit():
        user_data = current_app.db.user.find_one({"email": form.email.data})

        if not user_data or not pbkdf2_sha256.verify(form.password.data, user_data["password"]):
            flash("Login credentials not correct!", category="danger")
            return redirect(url_for(".login"))

        session["user_id"] = user_data["_id"]
        session["email"] = user_data["email"]

        return redirect(url_for(".index"))

    return render_template("login.html", title="Movie WatchList - Login", form=form)


@pages.route("/logout")
def logout():
    del session["user_id"]
    del session["email"]

    return redirect(url_for(".login"))


@pages.route("/add", methods=["GET", "POST"])
@login_required
def add_movie():
    form = MovieForm()

    if form.validate_on_submit():
        movie = Movie(
            _id=uuid.uuid4().hex,
            title=form.title.data,
            director=form.director.data,
            year=form.year.data
        )

        current_app.db.movie.insert_one(asdict(movie))
        current_app.db.user.update_one({"_id": session["user_id"]},
                                       {"$push": {"movies": movie._id}})

        return redirect(url_for(".index"))

    return render_template(
        "new_movie.html",
        title="Movies WatchList - Add Movie",
        form=form
    )


@pages.route("/edit/<string:_id>", methods=["GET", "POST"])
@login_required
def edit_movie(_id: str):
    movie = Movie(**current_app.db.movie.find_one({"_id": _id}))
    form = ExtendedMovieForm(obj=movie)

    if form.validate_on_submit():
        movie.cast = form.cast.data
        movie.series = form.series.data
        movie.tags = form.tags.data
        movie.description = form.description.data
        movie.video_link = form.video_link.data
        movie.title = form.title.data
        movie.director = form.director.data
        movie.year = form.year.data

        current_app.db.movie.update_one({"_id": _id}, {"$set": asdict(movie)})
        return redirect(url_for(".movie", _id=movie._id))

    return render_template("movie_form.html", movie=movie, form=form)


@pages.route("/movie/<string:_id>")
def movie(_id: str):
    movie_data = current_app.db.movie.find_one({"_id": _id})
    if not movie_data:
        abort(404)
    movie_obj = Movie(**movie_data)
    return render_template("movie_details.html", movie=movie_obj)


@pages.route("/movie/<string:_id>/rate")
@login_required
def rate_movie(_id):
    rating = int(request.args.get("rating"))
    current_app.db.movie.update_one({"_id": _id}, {"$set": {"rating": rating}})
    return redirect(url_for(".movie", _id=_id))


@pages.route("/movie/<string:_id>/watch")
@login_required
def watch_today(_id):
    watched_date = datetime.datetime.today()
    current_app.db.movie.update_one({"_id": _id}, {"$set": {"last_watched": watched_date}})
    return redirect(url_for(".movie", _id=_id))


@pages.route("/toggle-theme")
def toggle_theme():
    current_theme = session.get("theme")
    if current_theme == "dark":
        session["theme"] = "light"
    else:
        session["theme"] = "dark"
    return redirect(request.args.get("current_page"))

