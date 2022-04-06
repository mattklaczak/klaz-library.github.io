# Matthew Klaczak
# mck70@pitt.edu

from flask import Flask, request, session, url_for, redirect, render_template, abort, g, flash
import os

# necessary flask starter code
app = Flask(__name__)

# configuration information
PER_PAGE = 30
DEBUG = False
SECRET_KEY = 'development key'
DATABASE_NAME = 'library.db'

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(app.root_path, DATABASE_NAME) # create a path sqlite:///...database.db
SQLALCHEMY_TRACK_MODIFICATIONS = False

app.config.from_object(__name__)