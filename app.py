from flask import Flask, render_template, request, redirect, url_for, session

import mysql.connector

app = Flask(__name__)

app.secret_key = 'xyz'

# Configure MySQL connection
db = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='flask'
)

cursor = db.cursor(buffered=True)

@app.route('/')
def index():
    if 'username' in session:
        cursor = db.cursor(dictionary=True)
        cursor.execute('SELECT * FROM posts')  # Replace 'posts' with your actual table name
        posts = cursor.fetchall()
        cursor.close()
        username = session['username']
        return render_template('index.html', username=username, posts=posts)
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Execute a SELECT query to check user credentials
        query = "SELECT * FROM users WHERE username = %s AND password = %s"
        cursor.execute(query, (username, password))
        user = cursor.fetchone()
        
        if user:
            # User authenticated
            # Perform actions after successful login (e.g., redirect to dashboard)
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', message='Invalid username or password. Please try again.')
    else:
        return render_template('login.html', message='')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if the username already exists
        check_query = "SELECT * FROM users WHERE username = %s"
        cursor.execute(check_query, (username,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            return render_template('register.html', message='Username already exists. Please choose a different one.')
        else:
            # Insert new user data into the database
            insert_query = "INSERT INTO users (username, password) VALUES (%s, %s)"
            cursor.execute(insert_query, (username, password))
            db.commit()  # Commit changes to the database
            
            return redirect(url_for('login'))
    else:
        return render_template('register.html', message='')
    
@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        username = session['username']
        return render_template('dashboard.html', username=username)
    else:
        return redirect(url_for('login'))

@app.route('/add_post', methods=['GET', 'POST'])
def add_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        
        # Insert the post into the database
        insert_query = "INSERT INTO posts (title, content) VALUES (%s, %s)"
        cursor.execute(insert_query, (title, content))
        db.commit()  # Commit the changes
        
        return redirect(url_for('dashboard'))
    return render_template('add_post.html')

@app.route('/logout')
def logout():
    # Remove user session data
    session.pop('logged_in', None)
    session.pop('username', None)
    
    # Redirect to home page after logout
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
