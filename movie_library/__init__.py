import os
from flask import Flask
from dotenv import load_dotenv
from pymongo import MongoClient

from movie_library.routes import pages

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config["MONGODB_URL"] = os.environ.get("MONGODB_URL")
    app.config["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY", "pf9Wkove4IKEAXvy-cQkeDPhv9Cb3Ag-wyJILbq_dFw"
    )
    app.db = MongoClient(app.config["MONGODB_URL"]).get_default_database()

    app.register_blueprint(pages)
    return app
