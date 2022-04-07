# Matthew Klaczak
# mck70@pitt.edu

from flask import Flask, request, session, url_for, redirect, render_template, abort, g, flash
from app import *
from models import db, User, Book
import re
import datetime

################################################
# Utilities
################################################

# Method that is given a username, gives user id or none if none found
def get_user_id(username):
	rv = User.query.filter_by(username=username).first()
	return rv.user_id if rv else None

# Decorator to check whether use is logged in, so that we don't have to check on every page
@app.before_request
def before_request():
	# Here, 'g' is a general purpose global variable. Exists for one session.
	g.user = None
	if 'user_id' in session:
		g.user = User.query.filter_by(user_id=session['user_id']).first()

################################################
# User account management page routes
################################################

# Method for logging a user in. Validates user credentials and if correct, logs them in and commits to database
@app.route('/login', methods=['GET', 'POST'])
def login():
	if g.user: # Are we already logged in?
		return redirect(url_for('home'))
	
	error = None
	if request.method == 'POST': # HTTP POST method
		user = User.query.filter_by(username=request.form['username']).first() # Grab first part of input, like LIMIT 1
		if user is None:
			error = 'Invalid username'
		elif user.password != request.form['password']: # Incorrect password
			error = 'Invalid password'
		else:
			flash('You were logged in')
			session['user_id'] = user.user_id
			user.lastlogin = datetime.datetime.now() # Get current time
			db.session.commit() # database commit
			return redirect(url_for('home')) # Send to account home

	return render_template('login.html', error=error)

# Method for registering a new user
@app.route('/register', methods=['GET', 'POST'])
def register():
	if g.user: # Checks to see whether we are logged in
		return redirect(url_for('home'))

	error = None
	if request.method == 'POST': # HTTP POST method
		if not request.form['username']: # Begin checks for data validity
			error = 'You have to enter a username'
		elif not request.form['email'] or '@' not in request.form['email']: # Invalid email format
			error = 'You have to enter a valid email address'
		elif not request.form['password']:
			error = 'You have to enter a password'
		elif request.form['password'] != request.form['password2']: # Mismatching passes
			error = 'The two passwords do not match'
		elif get_user_id(request.form['username']) is not None:
			error = 'The username is already taken'
		else: # Data is valid, now add to databaes accordingly
			db.session.add(User(
				username = request.form['username'],
				email = request.form['email'],
				password = request.form['password'],
				timeadded = datetime.datetime.now(),
				librarian = False))
			db.session.commit() # Commit to database
			flash('You were successfully registered! Please log in.')
			return redirect(url_for('login'))

	return render_template('register.html', error=error)

# Method that logs the user out and removes User element from session dict
@app.route('/logout')
def logout():
	flash('You were logged out. Thanks!')
	session.pop('user_id', None)
	return redirect(url_for('home'))

################################################
# Other page routes
################################################

# The home page shows a listing of books
@app.route('/', methods=['GET', 'POST'])
def home():
	# 'Rent' or 'Return' button pushed on /home page
	if request.method == 'POST':
		bid = request.form.get('book_id')
		someBook = Book.query.filter_by(book_id=bid).first()
		# Wants to return a book
		if someBook in g.user.borrows:
			g.user.borrows.remove(someBook)
		# Wants to rent a book
		elif someBook is not None:
		 	g.user.borrows.append(someBook)
	db.session.commit()
	books1 = Book.query.order_by(Book.title).all()
	return render_template('home.html', books=books1)

# Routes for the 'manage books' section of the site
@app.route('/books/', methods=['GET', 'POST'])
@app.route('/books/<book_id>', methods=['GET', 'POST'])
def books(book_id=None):
	# If not a librarian (administrator)
	if g.user is None or g.user.librarian is False:
		return redirect(url_for('home'))
	# Generic /books/<book_id> page
	if book_id is None:
		# 'Create Book' button pushed on /books/<book_id> page
		if request.method == 'POST':
			btitle = request.form.get('title')
			bauthor = request.form.get('author')
			if Book.query.filter_by(title=btitle).first() is None: # make sure book doesnt already exist
				db.session.add(Book(title=btitle, author=bauthor))
				db.session.commit()
				flash('Successfully added book to library.')
				return redirect(url_for('home'))
			else:
				flash('Sorry, that book is already in the library.')
		return render_template('new_book.html')
	# Specific books/<book_id> page
	else:
		book = Book.query.filter_by(book_id=book_id).first()
		# 'No Book Found' page
		if book is None:
			abort(404)
		# Populate all who are renting
		else:
			Users = User.query.all()
			patrons = []
			for u in Users:
				if book in u.borrows:
					patrons.append(u.username)
			return render_template('book_details.html', b=book, p=patrons)

# routes for the 'accounts' portion of the site
@app.route('/accounts/', methods=['GET', 'POST'])
@app.route('/accounts/<user_id>', methods=['GET', 'POST'])
def accounts(user_id=None):
	# If not a libraian
	if g.user is None or g.user.librarian is False:
		return redirect(url_for('home'))
	# Generic /accounts page
	if user_id is None:
		error = None
		if request.method == 'POST':
			# Create librarian button
			# check for form contents for creating a librarian 
			if not request.form['username']:
				error = 'You have to enter a username'
			elif not request.form['email'] or '@' not in request.form['email']:
				error = 'You have to enter a valid email address'
			elif not request.form['password']:
				error = 'You have to enter a password'
			elif request.form['password'] != request.form['password2']:
				error = 'The two passwords do not match'
			elif get_user_id(request.form['username']) is not None:
				error = 'The username is already taken'
			else:
				db.session.add(User(
					username = request.form['username'],
					email = request.form['email'],
					password = request.form['password'],
					timeadded = datetime.datetime.now(),
					librarian = True))
				db.session.commit()
				flash('Librarian account successfully created.')
				return redirect(url_for('accounts'))
			# in case an 'error' occured with the form
			return render_template('accounts.html', error=error)
		else:
			# HTTP GET method
			patrons = User.query.order_by(User.username).filter_by(librarian=False).all()
			librarians = User.query.order_by(User.username).filter_by(librarian=True).all()
			return render_template('accounts.html', pats=patrons, libs=librarians)
	# Specific /accounts/<user_id> page
	else:
		# Delete button pushed /accounts/<user_id> page
		if request.method == 'POST':
			userToDelete = request.form.get('deleted_user')
			if userToDelete == 'owner':
				abort(401)
			else:
				userObj = User.query.filter_by(username=userToDelete).first()
				db.session.delete(userObj)
				db.session.commit()
				flash('Account successfully deleted.')
				return redirect(url_for('accounts'))
		else:
			# HTTP GET method /accounts/<user_id> page
			user = User.query.filter_by(user_id=user_id).first()
			if user is None:
				abort(404) # no valid user
			books = Book.query.all()
			userHas = []
			for book in books: # populate books that are borrowed
				if book in user.borrows:
					userHas.append(book)
			return render_template('user_id.html', u=user, b=userHas)

# Method that routes for the 'search books' portion, returns page with found books
@app.route('/search', methods=['GET', 'POST'])
def search(user_id=None):
	if request.method == 'POST':
		error = None
		criteria = False # used to make sure the user entered search criteria
		toReturn = set()
		list_books = Book.query.all()
		# search titles
		if request.form['search_title']:
			to_search_title = request.form['search_title']
			for b in list_books: # grab portions of book titles
				tokens = b.title.split() # match parts of TITLE
				for t in tokens:
					if to_search_title.upper() == t.upper(): # ignore case
						toReturn.add(b)
			criteria = True # so we know proper search terms were found
		# search authors
		if request.form['search_author']:
			to_search_author = request.form['search_author']
			for b in list_books: # grab portions of book authors
				tokens = b.author.split() # match certain parts of name
				for t in tokens:
					if to_search_author.upper() == t.upper(): # ignore case
						toReturn.add(b)
			criteria = True
		# search keyword
		if request.form['search_keyword']:
			to_search_keyword = request.form['search_keyword']
			for b in list_books: # this can match any part of book
				if re.findall(to_search_keyword, b.author, re.I) or re.findall(to_search_keyword, b.title, re.I):
					toReturn.add(b)
			criteria = True
		# determine if the user entered any search criteria
		if criteria:
			return render_template('search.html', books=toReturn)
		else:
			error = 'Please enter search criteria'
			return render_template('search.html', error=error)
	else:
		return render_template('search.html')

# 'Order by' routing methods
# Method to route by username alphabetically ASCENDING
@app.route('/accounts/sort?=username_ascending', methods=['GET', 'POST'])
def user_list_ascend():
	return order_by(User.username.desc())

# Method to route by username alphabetically DESCENDING
@app.route('/accounts/sort?=username_descending', methods=['GET', 'POST'])
def user_list_descend():
	return order_by(User.username)

# Method to route by email address alphabetically DESCENDING
@app.route('/accounts/sort?=email_descending', methods=['GET', 'POST'])
def user_list_e_descend():
	return order_by(User.email)

# Method to route by email address alphabetically ASCENDING
@app.route('/accounts/sort?=email_ascending', methods=['GET', 'POST'])
def user_list_e_ascend():
	return order_by(User.email.desc())

# Method to route by user added LONGEST ago
@app.route('/accounts/sort?=dateadded_longest', methods=['GET', 'POST'])
def user_list_dateadded_longest():
	return order_by(User.timeadded)

# Method to route by user added MOST recently
@app.route('/accounts/sort?=dateadded_shortest', methods=['GET', 'POST'])
def user_list_dateadded_shortest():
	return order_by(User.timeadded.desc())

# Method to route by logins that were MOST recent
@app.route('/accounts/sort?=login_mostrecent', methods=['GET', 'POST'])
def user_list_login_mostrecent():
	return order_by(User.lastlogin.desc())

# Method to route by logins that were LEAST recent
@app.route('/accounts/sort?=login_leastrecent', methods=['GET', 'POST'])
def user_list_login_leastrecent():
	return order_by(User.lastlogin)

# this 'helper' function assists in all the ordering routing functions by being a generic template
def order_by(search_params):
	patrons = User.query.order_by(search_params).filter_by(librarian=False).all()
	librarians = User.query.order_by(search_params).filter_by(librarian=True).all()
	#print(patrons)
	return render_template('user_list.html', pats=patrons, libs=librarians)
