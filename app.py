from flask import Flask, render_template, request, redirect, url_for, session,g
from pymongo import MongoClient

# import pymysql

app = Flask(__name__)

app.secret_key = 'xyz'
connection_string = 'mongodb+srv://hackers_co:K9mDEAed8NYtQeLd@blog.xk7q6yw.mongodb.net/'
client = MongoClient(connection_string)
db = client["blogdb"]  # Update with your MongoDB database name
users_collection = db["likes"]
posts_collection = db["test"]

# from flask import g  # Import the 'g' object for request context

# def get_db():
#     if 'db' not in g:
#         g.db = db.cursor()
#     return g.db

# def close_db(e=None):
#     db = g.pop('db', None)
#     if db is not None:
#         db.close()

# global cursor
# db = pymysql.connect(
#     host = "hackersco-hackersco.a.aivencloud.com",
#     user = "avnadmin",
#     password = "AVNS__9ztPF5bwUhGW1UDwr6",
#     database = "defaultdb",
#     port = 11183 
# )
# Configure MySQL connection, change according to yours

# cursor =  db.cursor()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')

            # Check if the username is already taken
            existing_user = users_collection.find_one({'username': username})
            if existing_user:
                return render_template('register.html', message='Username already taken. Please choose a different one.')

            # Insert new user data into MongoDB
            user_id = users_collection.insert_one({'username': username, 'password': password, 'email': email}).inserted_id

            return redirect(url_for('login'))

        except Exception as e:
            print("Error:", e)
            return "An error occurred while registering the user."

    return render_template('register.html')
########################################-------------------------------------------------

@app.route('/')
def index():
    if 'username' in session:
        try:
            # Fetch posts from MongoDB
            posts = posts_collection.find({}, {'_id': 0})
            username = session['username']
            return render_template('index.html', username=username, posts=posts)
        except Exception as e:
            print("Error:", e)
            return "An error occurred while fetching posts."
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check user credentials in MongoDB
        user = users_collection.find_one({'username': username, 'password': password})
        
        print("User:", user)

        if user:
            # print("Login successful!")
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('index'))
        else:
            # print("Invalid credentials.")
            return render_template('login.html', message='Invalid username or password. Please try again.')
    else:
        return render_template('login.html', message='')
########################################-------------------------------------------------
@app.route('/add_post', methods=['GET', 'POST'])
def add_post():
    if request.method == 'POST':
        if 'username' in session:
            title = request.form['title']
            content = request.form['content']

            try:
                # Fetch user ID associated with the current session
                user = users_collection.find_one({'username': session['username']})
                user_id = user['_id']

                # Insert the post into MongoDB
                posts_collection.insert_one({'user_id': user_id, 'title': title, 'content': content})

                return redirect(url_for('index'))
            except Exception as e:
                print("Error:", e)
                return "An error occurred while adding the post."
        else:
            return redirect(url_for('login'))
    return render_template('add_post.html')
########################################-------------------------------------------------
########################################-------------------------------------------------
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'username' in session:
        if request.method == 'POST':
            new_username = request.form['new_username']
            new_password = request.form['new_password']
            new_email = request.form['new_email']

            try:
                # Update username if it's not empty
                if new_username:
                    users_collection.update_one({'username': session['username']}, {'$set': {'username': new_username}})
                    session['username'] = new_username  # Update session with new username

                # Update password if it's not empty
                if new_password:
                    users_collection.update_one({'username': session['username']}, {'$set': {'password': new_password}})

                # Update email if it's not empty
                if new_email:
                    users_collection.update_one({'username': session['username']}, {'$set': {'email': new_email}})

                return redirect(url_for('profile'))  # Redirect to the profile page
            except Exception as e:
                print("Error:", e)
                return "An error occurred while updating profile."

        else:
            # Fetch user details for displaying on the profile page
            user_details = users_collection.find_one({'username': (session['username'])}, {'_id': 1})
            return render_template('profile.html', user_details=user_details)
    else:
        return redirect(url_for('login'))
@app.route('/logout')
def logout():
    # Remove user session data
    session.pop('logged_in', None)
    session.pop('username', None)
    
    # Redirect to home page after logout
    return redirect(url_for('index'))
if __name__ == '__main__':
    # from waitress import serve
    # serve(app, host="0.0.0.0", port=8080)

    app.run(debug=True)
    # from waitress import serve
    # serve(app, host="0.0.0.0", port=8080)

    #app.run(debug=True)
