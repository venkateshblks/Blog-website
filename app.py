from flask import Flask, render_template, request, redirect, url_for, session,g
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import pytz
import re
import random
from passlib.hash import bcrypt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import jsonify
from werkzeug.utils import secure_filename
from gridfs import GridFS

# import pymysql

app = Flask(__name__)

app.secret_key = 'xyz'
connection_string = MongoDBURI
client = MongoClient(connection_string)
db = client["webdb"]  # Update with your MongoDB database name
users_collection = db["users"]
posts_collection = db["posts"]
comments_collection = db["comment"]
grid_fs = GridFS(db)
########################################-------------------------------------------------
@app.route('/')
def index():
    user_document = None 
     # Initialize user_document as None by default
     
    if 'username' in session:
        try:
            # Fetch user document from MongoDB
            username = session['username']
            posts = posts_collection.find()
            user_document = users_collection.find_one({'username': username})
        except Exception as e:
            print("Error:", e)
            return "An error occurred while fetching user details."
        posts = posts_collection.find()  # Fetch posts
        return render_template('index.html', posts=posts, user_document=user_document)
    else :
        posts = posts_collection.find()#{}, {'_id': 0}
        return render_template('home.html',posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_or_email = request.form['username']
        password = request.form['password']

        # Check user credentials in MongoDB
        # user = users_collection.find_one({'email': username})
        # user = users_collection.find_one({'username': username}) #'password': password})
        user = users_collection.find_one({
            '$or': [
                {'username': username_or_email},
                {'email': username_or_email}
            ]
        })
        
        # print("User:", user)


        if user  and  bcrypt.verify(password, user['password']):
            # print("Login successful!")
            session['logged_in'] = True
            session['username'] = user['username']
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
            uploaded_files = request.files.getlist('file')

            try:
                # Fetch user ID associated with the current session
                user = users_collection.find_one({'username': session['username']})
                user_id = user['_id']
                current_utc_time = datetime.utcnow()
                india_timezone = pytz.timezone('Asia/Kolkata')
                current_india_time = current_utc_time.replace(tzinfo=pytz.utc).astimezone(india_timezone)
                # Insert the post into MongoDB
                content = extract_text_and_images(content)

                # posts_collection.insert_one({'user_id': user_id, 'title': title, 'content': content,'user':session['username'], 'date': current_india_time.strftime('%d %B %Y')  })
                post_id = posts_collection.insert_one({
                    'user_id': user_id,
                    'title': title,
                    'content': content,
                    'user': session['username'],
                    'date': current_india_time.strftime('%d %B %Y'),
                    'images': [] 
                }).inserted_id
                for file in uploaded_files:
                    if file:
                        filename = secure_filename(file.filename)
                        file_id = grid_fs.put(file, filename=filename, post_id=post_id)
                        posts_collection.update_one({'_id': post_id}, {'$push': {'images': file_id}})
                return redirect(url_for('index'))
            except Exception as e:
                print("Error:", e)
                return "An error occurred while adding the post."
        else:
            return redirect(url_for('login'))
    return render_template('add_post.html')
########################################-------------------------------------------------
from flask import send_file

@app.route('/get_image/<image_id>')
def get_image(image_id):
    # Retrieve the image from GridFS based on the image_id
    image_data = grid_fs.get(ObjectId(image_id))

    # Set the appropriate content type
    response = app.make_response(image_data.read())
    response.headers['Content-Type'] = 'image/jpeg'  # Adjust the content type based on your images

    return response
########################################-------------------------------------------------
def generate_otp():
    return str(random.randint(1000, 9999))
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'username' in session:
        if request.method == 'POST':
            new_username = request.form['new_username']
            new_password = request.form['new_password']
            new_password = bcrypt.hash(new_password)
            new_email = request.form['new_email']
            existing_us = users_collection.find_one({'username': new_username})
            existing_u = users_collection.find_one({'email':new_email})
        
            if existing_us:
                return render_template('profile.html', message='Username already taken. Please choose a different one.')
            if existing_u:
                return render_template('profile.html', message='Email already taken. Please choose a different one.')

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
                    # if request.method != 'POST':
        # username = request.form['username']
                    email = new_email
                    otp = generate_otp()
                    print(otp)
                    if send_otp_email(email, otp):
                        session['email'] = email 
                        # session['username'] = username
                        # session['password'] = password
                        session['otp'] = otp
                        return render_template('verify_email.html')
                    else:
                        return 'Failed to send OTP. Please try again.'
                    # return redirect(url_for('update'))
                    # users_collection.update_one({'username': session['username']}, {'$set': {'email': new_email}})

                return redirect(url_for('profile'))  # Redirect to the profile page
            except Exception as e:
                print("Error:", e)
                return "An error occurred while updating profile."

        else:
            # Fetch user details for displaying on the profile page
            user_details = users_collection.find_one({'username': (session['username'])})
           
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
    posts_collection.delete_one({'_id': ObjectId(post_id)})

    return redirect(url_for('index'))

@app.route('/redirect_page/<post_id>', methods=['GET', 'POST'])
def redirect_page(post_id):
    post_id = ObjectId(post_id)
    post = posts_collection.find_one({'_id': post_id})
    username = session.get('username')

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'like' and username:
            user_document = users_collection.find_one({'username': username})

            if user_document:
                liked_posts = user_document.get('liked_posts', [])

                if post_id in liked_posts:
                    # User already liked the post, remove like
                    posts_collection.update_one(
                        {'_id': post_id},
                        {'$inc': {'likes': -1}}
                    )
                    users_collection.update_one(
                        {'_id': user_document['_id']},
                        {'$pull': {'liked_posts': post_id}}
                    )
                else:
                    # User has not liked the post, add like
                    posts_collection.update_one(
                        {'_id': post_id},
                        {'$inc': {'likes': 1}}
                    )
                    users_collection.update_one(
                        {'_id': user_document['_id']},
                        {'$addToSet': {'liked_posts': post_id}}
                    )
            else:
                # User document not found, handle appropriately
                pass  # You may redirect or show an error message

        # Handle comment submission
        comment_content = request.form.get('comment_content')
        if username and comment_content:
            ist = pytz.timezone('Asia/Kolkata')
            current_time = datetime.now(ist)
            is_author = post['user'] == username
            
            comments_collection.insert_one({
                'post_id': post_id,
                'user': username,
                'content': comment_content,
                'date': current_time,
                'Author': is_author
            })

        return redirect(url_for('redirect_page', post_id=post['_id']))

    # Fetch comments for the post
    comments = comments_collection.find({'post_id': post_id})
    files = grid_fs.find()
    # return render_template('dashboard.html', )

    return render_template('dashboard.html', post=post,files=files, comments=comments)

   #u = None
    print(session.get('username'))#'username'])
    # session['username']
    comments = comments_collection.find({'post_id': post_id})
    if username:
        user_document = users_collection.find_one({'username': username})
        if user_document is not None:
            u = user_document.get('_id')
            return render_template('dashboard.html', u=u, user_document=user_document, comments=comments, post=post)
        else:
            # Handle the case where user_document is None
            return render_template('dashboard.html', comments=comments, post=post)
    else:
        return render_template('dashboard.html', comments=comments, post=post)
    # post ={'_id': post_id}

@app.route('/download/<file_id>')
def download_file(file_id):
    try:
        # Retrieve the file from GridFS based on the file_id
        file = grid_fs.get(ObjectId(file_id))
        # print(file)
        mime_type = file.content_type if file.content_type else 'application/octet-stream'

        # Set the appropriate content type
        response = send_file(file, as_attachment=True, mimetype=mime_type, download_name=file.filename)

        return response
    except Exception as e:
        print("Error:", e)
        return "File not found"

@app.route('/like_post/<post_id>', methods=['POST'])
def like_post(post_id):
    post_id = ObjectId(post_id)
    post = posts_collection.find_one({'_id': post_id})

    if post:
        # Increment the likes count for the post
        posts_collection.update_one(
            {'_id': post_id},
            {'$inc': {'likes': 1}}
        )
        return jsonify({'success': True, 'likes': post['likes'] + 1})
    return jsonify({'success': False, 'error': 'Post not found'}), 404


# ////////////////////////////////////
@app.route('/delete_comment/<comment_id>')
def delete_comment(comment_id):
    # Assuming you have a comments_collection for storing comments
    result = comments_collection.delete_one({'_id': ObjectId(comment_id)})
    # Redirect to the same page after deletion
    return redirect(request.referrer)
# ................
def send_otp_email(email, otp):
    sender_email = 'email@gmail.com'  # Replace with your email address
    sender_password = 'passkey'  # Replace with your email password

    subject = 'Your OTP for verification from HC'
    body = f'Your OTP for verification is: {otp}'

    try:
        msg = MIMEMultipart()
        msg['From'] = 'HC <email@gmail.com>'
        msg['To'] = email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, msg.as_string())
        
        return True
    except Exception as e:
        print('Error while sending email:', e)
        return False

# Function to send OTP via email
# def send_otp_email(email, otp):
#     sender_email = 'email@gmail.com'  # Replace with your email address
#     sender_password = 'axla hltg jwrn fygm'  # Replace with your email password

#     subject = 'Your OTP for verification'
#     body = f'Your OTP for verification is: {otp}'

#     try:
#         server = smtplib.SMTP('smtp.gmail.com', 587)  # Gmail SMTP server
#         server.starttls()
#         server.login(sender_email, sender_password)
#         server.sendmail(sender_email, email, f'Subject: {subject}\n\n{body}')
#         server.quit()
#         return True
#     except Exception as e:
#         print('Error while sending email:', e)
#         return False

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        existing_user = users_collection.find_one({'username': username})
        existing_use = users_collection.find_one({'email': email})
        
        if existing_user:
            return render_template('register.html', message='Username already taken. Please choose a different one.')
        if existing_use:
            return render_template('register.html', message='Email already taken. Please choose a different one.')
        
        # if 'otp' in session and 'email' in session:
        #     if session['email'] == email and session['otp'] == request.form['otp']:
        #         user_data = {
        #             "username": username,
        #             "email": email,
        #             "password": password
        #         }
        #         try:
        #             users_collection.insert_one(user_data)
        #             session.pop('otp', None)
        #             session.pop('email', None)
        #             return 'Registration successful!'
        #         except Exception as e:
        #             print('Error while inserting user:', e)
        #             return 'Failed to register. Please try again.'
        #     else:
        #         return 'Invalid OTP. Please try again.'
        
        otp = generate_otp()
        print(otp)
        if send_otp_email(email, otp):
            session['email'] = email 
            session['username'] = username
            session['password'] = password
            session['otp'] = otp
            return render_template('verify_otp.html')
        else:
            return 'Failed to send OTP. Please try again.'

    return render_template('register.html')

# ............................................../////////////
@app.route('/update', methods=['GET', 'POST'])
def update():
    if request.method != 'POST':
        # username = request.form['username']
        email = request.form['email']
        otp = generate_otp()
        print(otp)
        if send_otp_email(email, otp):
            session['email'] = email 
            # session['username'] = username
            # session['password'] = password
            session['otp'] = otp
            return render_template('verify_otp.html')
        else:
            return 'Failed to send OTP. Please try again.'
    return '. Please try again.'
@app.route('/verify_email', methods=['POST'])
def verify_email():
    if request.method == 'POST':
        new_email = session.get('email')
        users_collection.update_one({'username': session['username']}, {'$set': {'email': new_email}})
        return redirect(url_for('profile'))


        # .......................//////////////////////

@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    if request.method == 'POST':
        email = session.get('email')
        user_otp = request.form['otp']
        usename=session.get('username')
        password=session.get('password')

        if 'otp' in session and 'email' in session:
            if session['email'] == email and session['otp'] == user_otp:
                hashed_password = bcrypt.hash(password)
                user_data = {
                    "username":usename ,  # You can uncomment this if needed
                    "email": email,
                    "password": hashed_password
                }
                try:
                    users_collection.insert_one(user_data)
                    session.pop('otp', None)
                    session.pop('email', None)
                    return redirect(url_for('login'))
                    # return 'Registration successful!' 
                except Exception as e:
                    print('Error while inserting user:', e)
                    return 'Failed to register. Please try again.'
            else:
                return 'Invalid OTP. Please try again.'

    # Redirect to registration page if accessed directly
    return render_template('register.html')

    # ......................FORGOT PASS
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']

        # Check if the email exists in the database
        user = users_collection.find_one({'email': email})

        if user:
            # Generate and send OTP
            otp = generate_otp()
            send_otp_email(email, otp)

            # Store OTP in the session for verification
            session['reset_email'] = email
            session['reset_otp'] = otp

            return redirect(url_for('verify_reset_otp'))
        else:
            return render_template('forgot_password.html', message='Invalid email. Please try again.')

    return render_template('forgot_password.html')
# verify...........
# ...

# Route for verifying OTP during password reset
@app.route('/verify_reset_otp', methods=['GET', 'POST'])
def verify_reset_otp():
    if request.method == 'POST':
        entered_otp = request.form['otp']

        # Check if entered OTP matches the stored OTP in the session
        if 'reset_otp' in session and session['reset_otp'] == entered_otp:
            # Redirect to password reset page
            return redirect(url_for('reset_password'))
        else:
            return render_template('verify_reset_otp.html', message='Invalid OTP. Please try again.')

    return render_template('verify_reset_otp.html')


# ...

# Route for resetting password
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        new_password = request.form['new_password']
        new_password = bcrypt.hash(new_password)


        # Update the user's password in the database
        if 'reset_email' in session:
            users_collection.update_one({'email': session['reset_email']}, {'$set': {'password': new_password}})

            # Clear the session variables
            session.pop('reset_email', None)
            session.pop('reset_otp', None)

            return redirect(url_for('login'))

    return render_template('reset_password.html')



    # /////////////////////

if __name__ == '__main__':
    # from waitress import serve
    # serve(app, host="0.0.0.0", port=8080)

    app.run(debug=True, port=5000)
