from flask import Flask, render_template, url_for, redirect, request, session, flash
from flask_login import current_user, LoginManager, UserMixin
from flask_bootstrap import Bootstrap
from flask_mysqldb import MySQL
from flask_ckeditor import CKEditor
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegistrationForm, LoginForm
import yaml
# import os

app = Flask(__name__)
Bootstrap(app)
login_manager = LoginManager(app)
CKEditor(app)

# configuration for database
db = yaml.load(open('db.yaml'), Loader=yaml.FullLoader)
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

app.config['SECRET_KEY'] = '741852963'
# os.urandom(24)


@app.route('/')
def index():
	return render_template('index.html')

@app.route('/about/')
def about():
	return render_template('about.html')

@app.route('/blogs/')
def blogs():
	cur = mysql.connection.cursor()
	resultData = cur.execute("SELECT * FROM blog")
	if resultData > 0:
		blogs  = cur.fetchall()
		cur.close()
		return render_template('blog.html', blogs=blogs)

@app.route('/register/', methods=['GET', 'POST'])
def register():
	if request.method == 'POST':
		userDetails = request.form
		if userDetails['password'] != userDetails['confirm_password']:
			flash('Password does not match! Try again!', 'danger')
			return render_template('register.html')
		cur = mysql.connection.cursor()
		cur.execute("INSERT INTO user(first_name, last_name, username, email, password) VALUES(%s, %s, %s, %s, %s)", (userDetails['first_name'], userDetails['last_name'], userDetails['username'], userDetails['email'], generate_password_hash(userDetails['password'])))
		mysql.connection.commit()
		cur.close()
		flash('Registration successful! Please login', 'success')
		return redirect('/login')

	return render_template('register.html')

@app.route('/registrationform/', methods=['GET', 'POST'])
def registration():
	form = RegistrationForm()
	cur = mysql.connection.cursor()
	if form.validate_on_submit():
		if form.password.data != form.confirm_password.data:
			flash('Password does not match!', 'danger')
			return redirect(url_for('registration'))
		cur.execute("INSERT INTO user(first_name,  last_name, username, email, password) VALUES(%s, %s, %s, %s, %s)", (form.first_name.data, form.last_name.data, form.username.data, form.email.data, generate_password_hash(form.password.data)))
		mysql.connection.commit()
		cur.close()
		flash('Registration successful! Please Login!', 'success')
		return redirect(url_for('loginForm'))

	return render_template('registrationform.html', title='Register', form=form)

@app.route('/login/', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		userDetails = request.form
		username = userDetails['username']
		cur = mysql.connection.cursor()
		resultData = cur.execute("SELECT * FROM user WHERE username = %s", ([username]))
		if resultData > 0:
			user = cur.fetchone()
			if check_password_hash(user['password'], userDetails['password']):
				session['login'] = True
				session['first_name'] = user['first_name']
				session['last_name'] = user['last_name']
				flash('Welcome '+ session['first_name'] +'! You have been logged in!', 'success')
			else:
				cur.close()
				flash('Password does not match', 'danger')
				return render_template('login.html')
		else:
			cur.close()
			flash('User not found', 'danger')
			return render_template('login.html')
		cur.close()
		return redirect('/')
	
	return render_template('login.html')

@app.route('/loginform/', methods=['GET', 'POST'])
def loginForm():
	form = LoginForm()
	if form.validate_on_submit():
		# userDetails = request.form
		email = form.email.data
		password = form.password.data
		cur = mysql.connection.cursor()
		resultData = cur.execute("SELECT * FROM user WHERE email = %s", ([email]))
		if resultData > 0:
			user = cur.fetchone()
			if check_password_hash(user['password'], password):
				session['login'] = True
				session['first_name'] = user['first_name']
				session['last_name'] = user['last_name']
				flash('Welcome ' + session['first_name'] + '! You have been logged in!', 'success')
			else:
				cur.close()
				flash('Password does not match', 'danger')
				return redirect(url_for('loginForm'))
		else:
			cur.close()
			flash('User not found!', 'danger')
			return redirect(url_for('index'))
		cur.close()
		return redirect(url_for('index'))

		# if form.email.data == user['email'] and form.password.data == user['password']:
		# 	flash('login successful', 'success')
		# 	return redirect(url_for('index'))
		# else:
		# 	# flash('wrong credentials', 'danger')
		# 	return password

	return render_template('loginform.html', title='Login', form=form)

@app.route('/write-blog/', methods=['GET', 'POST'])
def write_blog():
	if request.method == 'POST':
		blogpost = request.form
		title = blogpost['title']
		body = blogpost['body']
		author = session['first_name'] + ' ' + session['last_name']
		cur = mysql.connection.cursor()
		cur.execute("INSERT INTO blog(title, body, author) VALUES(%s, %s, %s)", (title, body, author))
		mysql.connection.commit()
		cur.close()
		flash('Successfully posted a blog!', 'success')
		return redirect('/my-blogs/')
	return render_template('write-blog.html')

@app.route('/my-blogs/')
def my_blogs():
	try:
		author = session['first_name'] + ' ' + session['last_name']
		cur = mysql.connection.cursor()
		resultData = cur.execute("SELECT * FROM blog WHERE author = %s", ([author]))
		if resultData > 0:
			blogs = cur.fetchall()
			cur.close()
			return render_template('my-blogs.html', blogs=blogs)
		cur.close()
		return render_template('my-blogs.html', blogs=None)
	except Exception:
		flash('You are not logged in! Try after log in!', 'info')
		return redirect('/login')

@app.route('/edit-blog/<int:id>/', methods=['GET', 'POST'])
def edit_blog(id):
	if request.method == 'POST':
		cur = mysql.connection.cursor()
		title = request.form['title']
		body = request.form['body']
		cur.execute("UPDATE blog SET title = %s, body = %s WHERE blog_id = %s", (title, body, id))
		mysql.connection.commit()
		cur.close()
		flash('Blog updated Successfully', 'success')
		return redirect('/my-blogs/')

	cur = mysql.connection.cursor()
	resultData = cur.execute("SELECT * FROM blog WHERE blog_id = %s", ([id]))
	# resultData = cur.execute("SELECT * FROM blog WHERE blog_id = {}".format(id))
	if resultData > 0:
		blog = cur.fetchone()
		cur.close()
		return render_template('edit-blog.html', blog=blog)

@app.route('/delete-blog/<int:id>/')
def delete_blog(id):
	cur = mysql.connection.cursor()
	cur.execute("DELETE FROM blog WHERE blog_id = {}".format(id))
	mysql.connection.commit()
	flash('Blod has been deleted!', 'success')
	return redirect('/my-blogs/')

@app.route('/logout/')
def logout():
	session.clear()
	flash('You have been logged out!', 'info')
	return redirect('/')
	
if __name__ == '__main__':
	app.run(debug=True)