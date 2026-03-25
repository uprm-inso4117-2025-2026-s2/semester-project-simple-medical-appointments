from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

# models/ — define your database models (tables) here.
# Each model typically maps to one database table.
#
# Example using Flask-SQLAlchemy (install it first: pip install flask-sqlalchemy):
#
# from flask_sqlalchemy import SQLAlchemy
# db = SQLAlchemy()
#
# class Appointment(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     patient_name = db.Column(db.String(100), nullable=False)
#     date = db.Column(db.DateTime, nullable=False)
#
# After creating models, import db and call db.init_app(app) in app/__init__.py,
# and run db.create_all() inside an app context to create the tables.

# This is the single shared database connection for the whole project.
# Every model file imports `db` from here: from . import db
