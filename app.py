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
        try:
            cursor = db.cursor(dictionary=True)
            query = '''
                SELECT posts.id, posts.title, posts.content, users.username 
                FROM posts 
                JOIN users ON posts.user_id = users.id
            '''
            cursor.execute(query)
            posts = cursor.fetchall()
            cursor.close()
            username = session['username']
            return render_template('index.html', username=username, posts=posts)
        except mysql.connector.Error as err:
            print("MySQL Error:", err)
            return "An error occurred while fetching posts."
        except Exception as e:
            print("Error:", e)
            return "An error occurred while processing your request."
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

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'username' in session:
        if request.method == 'POST':
            new_username = request.form['new_username']
            new_password = request.form['new_password']
            new_email = request.form['new_email']

            try:
                cursor = db.cursor()

                # Update username if it's not empty
                if new_username:
                    cursor.execute("UPDATE users SET username = %s WHERE username = %s", (new_username, session['username']))
                    session['username'] = new_username  # Update session with new username

                # Update password if it's not empty
                if new_password:
                    cursor.execute("UPDATE users SET password = %s WHERE username = %s", (new_password, session['username']))

                # Update email if it's not empty
                if new_email:
                    cursor.execute("UPDATE users SET email = %s WHERE username = %s", (new_email, session['username']))

                cursor.commit()  # Commit the changes
                return redirect(url_for('profile'))  # Redirect to the profile page
            except Exception as e:
                print("Error:", e)
                cursor.rollback()  # Rollback in case of an error
                return "An error occurred while updating profile."
            finally:
                cursor.close()
        else:
            # Fetch user details for displaying on the profile page
            cursor.execute("SELECT username, email FROM users WHERE username = %s", (session['username'],))
            user_details = cursor.fetchone()
            cursor.close()
            
            return render_template('profile.html', user_details=user_details)
    else:
        return redirect(url_for('login'))
  

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            cursor = db.cursor()
            # Insert new user data into the database
            cursor.execute("INSERT INTO users (username, password, email) VALUES (%s, %s, %s)", (username, password, email))
            db.commit()  # Commit changes to the database
            cursor.close()
            return redirect(url_for('login'))  # Redirect to login page after successful registration
                
        except Exception as e:
            print("Error:", e)
            return "An error occurred while registering the user."
            
    return render_template('register.html')
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
        if 'username' in session:
            title = request.form['title']
            content = request.form['content']

            try:
                # Fetch user ID associated with the current session
                cursor = db.cursor()
                cursor.execute("SELECT id FROM users WHERE username = %s", (session['username'],))
                user_id = cursor.fetchone()[0]

                # Insert the post into the database
                insert_query = "INSERT INTO posts (user_id, title, content) VALUES (%s, %s, %s)"
                cursor.execute(insert_query, (user_id, title, content))
                db.commit()  # Commit the changes

                return redirect(url_for('dashboard'))  # Redirect to the dashboard or any other page
            except Exception as e:
                print("Error:", e)
                db.rollback()  # Rollback in case of an error
                return "An error occurred while adding the post."
            finally:
                cursor.close()
        else:
            return redirect(url_for('login'))  # Redirect to login if the user is not logged in
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
