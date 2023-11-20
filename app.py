from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Dummy admin credentials (in a real app, use a more secure method for storing credentials)
admin_password = 'password'

# Dummy posts data
posts = [
    {'title': 'Blog Post Title', 'content': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam convallis turpis eget enim lacinia, vel vestibulum elit laoreet.'},
    {'title': 'Another Blog Post Title', 'content': 'Phasellus congue libero at magna imperdiet, vitae consectetur libero rutrum.'}
]

@app.route('/')
def index():
    return render_template('index.html', posts=posts)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        password = request.form['password']
        if password == admin_password:
            return render_template('admin.html')
        else:
            return render_template('login.html', message='Invalid password. Please try again.')
    else:
        return render_template('login.html', message='')

@app.route('/add_post', methods=['POST'])
def add_post():
    if request.method == 'POST':
        try:
            title = request.form['title']
            content = request.form['content']
            new_post = {'title': title, 'content': content}
            posts.append(new_post)
            print("Post added successfully:", new_post)  # Print the newly added post
        except Exception as e:
            print("Error adding post:", e)  # Print any exception/error that occurs while adding the post
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
