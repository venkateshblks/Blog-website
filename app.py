from flask import Flask, render_template, request, redirect, url_for, session,g
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import pytz
import re



# import pymysql

app = Flask(__name__)

app.secret_key = 'xyz'
connection_string = 'mongodb+srv://hackers_co:K9mDEAed8NYtQeLd@blog.xk7q6yw.mongodb.net/'
client = MongoClient(connection_string)
db = client["blogdb"]  # Update with your MongoDB database name
users_collection = db["likes"]
posts_collection = db["test"]

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
@app.route('/home')
def home():
    posts = posts_collection.find()#{}, {'_id': 0}
    return render_template('home.html',posts=posts)

@app.route('/')
def index():
    if 'username' in session:
        try:
            # Fetch posts from MongoDB
            posts = posts_collection.find()#{}, {'_id': 0}
            username = session['username']
            # user = users_collection.find({}, {'_id': 1})
            user_document = users_collection.find_one({'username': username})
            u=user_document['_id']
            
            return render_template('index.html',username=username,user_document=user_document,u=u, posts=posts)
        except Exception as e:
            print("Error:", e)
            return "An error occurred while fetching posts."
    else:
        return redirect(url_for('home'))


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
def extract_text_and_images(content):
    # Use a regular expression to find URLs in the content
    url_pattern = re.compile(r'https?://\S+')
    matches = url_pattern.finditer(content)

    parts = []
    last_end = 0

    for match in matches:
        start, end = match.span()

        # Add text before the match
        parts.append({'type': 'text', 'content': content[last_end:start]})

        # Add the image link
        parts.append({'type': 'image', 'content': match.group(0)})

        last_end = end

    # Add the remaining text after the last match
    parts.append({'type': 'text', 'content': content[last_end:]})

    return parts
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
                current_utc_time = datetime.utcnow()
                india_timezone = pytz.timezone('Asia/Kolkata')
                current_india_time = current_utc_time.replace(tzinfo=pytz.utc).astimezone(india_timezone)
                # Insert the post into MongoDB
                content = extract_text_and_images(content)

                posts_collection.insert_one({'user_id': user_id, 'title': title, 'content': content,'user':session['username'], 'date': current_india_time.strftime('%d %B %Y')  })

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
@app.route('/delete_post/<post_id>', methods=['POST'])
def delete_post(post_id):
    # Replace this with your actual authorization logic
    # if 'logged_in' not in session or not session['logged_in']:
    #     return redirect(url_for('index'))

    # current_user_id = session['username']  # Replace with your actual user data
    # post = posts_collection.find_one({'_id': ObjectId(post_id)})

    # Check if the current user is the author of the post
    # if post and post['user_id'] == current_user_id:
        # Delete the post from MongoDB
    posts_collection.delete_one({'_id': ObjectId(post_id)})

    return redirect(url_for('index'))
@app.route('/redirect_page/<post_id>')
def redirect_page(post_id):
    # Here, you can retrieve the post information using the post_id
    # For example, you can query the database to get the post details
    # and then pass the necessary data to the template
    # Replace the following line with your logic:
    post_id = ObjectId(post_id)
        
        # ...

    post = posts_collection.find_one({'_id': post_id})
    username=session['username']
    user_document = users_collection.find_one({'username': username})
    u=user_document['_id']
    # post ={'_id': post_id}
    return render_template('dashboard.html',u=u, post=post)
if __name__ == '__main__':
    # from waitress import serve
    # serve(app, host="0.0.0.0", port=8080)

    app.run(debug=True)
