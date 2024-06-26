from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from prodpublish import publish
import threading
from models import create_database
import os
import dotenv

dotenv.load_dotenv()
create_database()

app = Flask(__name__)
app.secret_key = os.environ['SUPERSECRET']

# Flask Login Configuration
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin):
    def __init__(self, id, username, discord_username, password, bio = '', avatar_url = 'https://innostudio.de/fileuploader/images/default-avatar.png', banned = False):
        self.id = id
        self.username = username
        self.discord_username = discord_username
        self.password = password
        self.bio = bio
        self.avatar_url = avatar_url
        self.banned = banned


@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('prompts.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return User(row[0], row[1], row[2], row[3], row[4], row[5], row[6])
    return None



# Helpers
def query_database(query, args=(), one=False):
    conn = sqlite3.connect('prompts.db')
    cursor = conn.cursor()
    cursor.execute(query, args)
    rv = cursor.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv


def execute_database(query, args=()):
    conn = sqlite3.connect('prompts.db')
    cursor = conn.cursor()
    cursor.execute(query, args)
    conn.commit()
    cursor.close()
    conn.close()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        discord_username = request.form.get('discord_username')
        password = request.form.get('password')

        if len(username) > 100:
            flash("Username too long.")
            return redirect(url_for('register'))
        if len(password) > 600:
            flash("Password too long.")
            return redirect(url_for('register'))
        # check if username contains illegal characters
        if not username.isalnum():
            flash("Username contains illegal characters.")
            return redirect(url_for('register'))
        # check if discord username contains illegal characters (can contain alnum and _)
        if not discord_username.replace('_', '').isalnum():
            flash("Discord username contains illegal characters.")
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)

        try:
            execute_database('''
                INSERT INTO users (username, discord_username, password)
                VALUES (?, ?, ?)
            ''', (username, discord_username, hashed_password))

            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or Discord Username already exists')
            return redirect(url_for('register'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user_data = query_database('SELECT * FROM users WHERE username = ?', (username,), one=True)
        if user_data and check_password_hash(user_data[3], password):
            user = User(user_data[0], user_data[1], user_data[2], user_data[3])
            if user_data[6]:
                flash('You are banned from the platform')
                return redirect(url_for('login'))
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Wrong Username or Password')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.banned:
        flash('You are banned from the platform')
        return redirect(url_for('logout'))
    prompts = query_database('SELECT * FROM prompts WHERE user_id = ?', (current_user.id,))
    return render_template('dashboard.html', prompts=prompts)


@app.route('/explore')
def explore():
    sort_by = request.args.get('sort_by', 'latest')
    prompts = []

    if sort_by == 'most_liked':
        prompts = query_database('SELECT * FROM prompts ORDER BY upvotes - downvotes DESC LIMIT 40')
    elif sort_by == 'most_viewed':
        prompts = query_database('SELECT * FROM prompts ORDER BY views DESC LIMIT 40')
    else:
        prompts = query_database('SELECT * FROM prompts ORDER BY id DESC LIMIT 40')

    return render_template('explore.html', prompts=prompts, sort_by=sort_by)


@app.route('/load_more_prompts', methods=['POST'])
def load_more_prompts():
    offset = int(request.form['offset'])
    sort_by = request.form['sort_by']
    prompts = []

    if sort_by == 'most_liked':
        prompts = query_database('SELECT * FROM prompts ORDER BY upvotes - downvotes DESC LIMIT 40 OFFSET ?', (offset,))
    elif sort_by == 'most_viewed':
        prompts = query_database('SELECT * FROM prompts ORDER BY views DESC LIMIT 40 OFFSET ?', (offset,))
    else:
        prompts = query_database('SELECT * FROM prompts ORDER BY id DESC LIMIT 40 OFFSET ?', (offset,))

    return jsonify(prompts)


@app.route('/prompt/<int:prompt_id>', methods=['GET', 'POST'])
def prompt_page(prompt_id):
    prompt = query_database('SELECT * FROM prompts WHERE id = ?', (prompt_id,), one=True)

    if not prompt:
        return redirect(url_for('explore'))

    execute_database('UPDATE prompts SET views = views + 1 WHERE id = ?', (prompt_id,))

    creator = query_database('SELECT * FROM users WHERE id = ?', (prompt[1],), one=True)
    comments = query_database('SELECT * FROM comments WHERE prompt_id = ? ORDER BY created_at ASC', (prompt_id,))

    votes = query_database('SELECT * FROM votes WHERE prompt_id = ?', (prompt_id,))
    user_vote = query_database('SELECT * FROM votes WHERE prompt_id = ? AND user_id = ?', (prompt_id, current_user.id), one=True) if current_user.is_authenticated else None

    comment_usernames = {
        comment[2]: query_database('SELECT username FROM users WHERE id = ?', (comment[2],), one=True)[0]
        for comment in comments
    }

    return render_template(
        'prompt_single.html',
        prompt=prompt, creator=creator,
        comments=comments, comment_usernames=comment_usernames,
        votes=votes, user_vote=user_vote
    )


@app.route('/add_prompt', methods=['POST'])
@login_required
def add_prompt():
    if current_user.banned:
        flash('You are banned from the platform')
        return redirect(url_for('logout'))
    title = request.form.get('title')
    content = request.form.get('content')

    if len(content) > 1000:
        flash("Content is too long")
        return redirect(url_for('dashboard'))
    
    if len(title) > 100:
        flash("Title is too long")
        return redirect(url_for('dashboard'))

    execute_database('INSERT INTO prompts (user_id, title, content) VALUES (?, ?, ?)', (current_user.id, title, content))
    return redirect(url_for('dashboard'))


@app.route('/delete_prompt/<int:prompt_id>')
@login_required
def delete_prompt(prompt_id):
    if current_user.banned:
        flash('You are banned from the platform')
        return redirect(url_for('logout'))
    prompt = query_database('SELECT * FROM prompts WHERE id = ? AND user_id = ?', (prompt_id, current_user.id), one=True)
    
    if prompt:
        execute_database('DELETE FROM prompts WHERE id = ?', (prompt_id,))
        execute_database('DELETE FROM comments WHERE prompt_id = ?', (prompt_id,))

    return redirect(url_for('dashboard'))


@app.route('/edit_prompt', methods=['POST'])
@login_required
def edit_prompt():
    if current_user.banned:
        flash('You are banned from the platform')
        return redirect(url_for('logout'))
    prompt_id = int(request.form.get('prompt_id'))
    title = request.form.get('title')
    content = request.form.get('content')

    prompt = query_database('SELECT * FROM prompts WHERE id = ? AND user_id = ?', (prompt_id, current_user.id), one=True)

    if len(content) > 1000:
        flash("Content is too long")
        return redirect(url_for('dashboard'))
    
    if len(title) > 100:
        flash("Title is too long")
        return redirect(url_for('dashboard'))

    if prompt:
        execute_database('''
            UPDATE prompts SET title = ?, content = ? WHERE id = ? AND user_id = ?
        ''', (title, content, prompt_id, current_user.id))

    return redirect(url_for('dashboard'))


@app.route('/vote', methods=['POST'])
@login_required
def vote():
    if current_user.banned:
        flash('You are banned from the platform')
        return redirect(url_for('logout'))
    prompt_id = int(request.form['prompt_id'])
    vote_type = int(request.form['vote_type'])

    user_vote = query_database('SELECT * FROM votes WHERE prompt_id = ? AND user_id = ?', (prompt_id, current_user.id), one=True)

    if user_vote:
        if user_vote[3] == vote_type:
            execute_database('DELETE FROM votes WHERE prompt_id = ? AND user_id = ?', (prompt_id, current_user.id))
        else:
            execute_database('UPDATE votes SET vote = ? WHERE prompt_id = ? AND user_id = ?', (vote_type, prompt_id, current_user.id))
    else:
        execute_database('INSERT INTO votes (prompt_id, user_id, vote) VALUES (?, ?, ?)', (prompt_id, current_user.id, vote_type))

    upvotes = len(query_database('SELECT id FROM votes WHERE prompt_id = ? AND vote = 1', (prompt_id,)))
    downvotes = len(query_database('SELECT id FROM votes WHERE prompt_id = ? AND vote = -1', (prompt_id,)))

    execute_database('UPDATE prompts SET upvotes = ?, downvotes = ? WHERE id = ?', (upvotes, downvotes, prompt_id))

    return jsonify({'upvotes': upvotes, 'downvotes': downvotes, 'total': upvotes - downvotes})


@app.route('/add_comment', methods=['POST'])
@login_required
def add_comment():
    if current_user.banned:
        flash('You are banned from the platform')
        return redirect(url_for('logout'))
    prompt_id = request.form.get('prompt_id')
    message = request.form.get('message')

    if len(message) > 500:
        flash("Comment too long.")
        return redirect(url_for('prompt_page', prompt_id=prompt_id))

    execute_database('INSERT INTO comments (prompt_id, user_id, message) VALUES (?, ?, ?)', (prompt_id, current_user.id, message))
    return redirect(url_for('prompt_page', prompt_id=prompt_id))


@app.route('/edit_comment', methods=['POST'])
@login_required
def edit_comment():
    if current_user.banned:
        flash('You are banned from the platform')
    comment_id = int(request.form.get('comment_id'))
    message = request.form.get('message')

    comment = query_database('SELECT * FROM comments WHERE id = ? AND user_id = ?', (comment_id, current_user.id), one=True)

    if len(message) > 500:
        flash("Comment too long.")
        return redirect(url_for('prompt_page', prompt_id=comment[1]))

    if comment:
        execute_database('UPDATE comments SET message = ? WHERE id = ? AND user_id = ?', (message, comment_id, current_user.id))

    return redirect(url_for('prompt_page', prompt_id=comment[1]))


@app.route('/delete_comment/<int:comment_id>')
@login_required
def delete_comment(comment_id):
    if current_user.banned:
        flash('You are banned from the platform')
    comment = query_database('SELECT * FROM comments WHERE id = ? AND user_id = ?', (comment_id, current_user.id), one=True)

    if comment:
        execute_database('DELETE FROM comments WHERE id = ?', (comment_id,))

    return redirect(url_for('prompt_page', prompt_id=comment[1]))

@app.route('/join')
def join():
    return render_template('jointos.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/profile')
@login_required
def profile():
    if current_user.banned:
        flash('You are banned from the platform')
        return redirect(url_for('logout'))
    # Get user_id from URL
    user_id = request.args.get('user_id')

    # If user_id is not provided, show current user's profile
    if not user_id:
        user_id = current_user.id
    
    # Get user data
    user_data = query_database('SELECT * FROM users WHERE id = ?', (user_id,), one=True)

    # Get user's prompts
    prompts = query_database('SELECT * FROM prompts WHERE user_id = ?', (user_id,))

    # Display user profile
    return render_template('profile.html', user=user_data, prompts=prompts)

@app.route('/edit_profile', methods=['POST'])
@login_required
def edit_profile():
    if current_user.banned:
        flash('You are banned from the platform')
        return redirect(url_for('logout'))
    bio = request.form.get('bio')
    avatar_url = request.form.get('avatar_url')
    if len(bio) > 1000:
        flash("Bio too long.")
        return redirect(url_for('settings'))

    execute_database('UPDATE users SET bio = ?, avatar_url = ? WHERE id = ?', (bio, avatar_url, current_user.id))

    return redirect(url_for('profile'))

@app.route('/settings')
@login_required
def settings():
    if current_user.banned:
        flash('You are banned from the platform')
        return redirect(url_for('logout'))
    print(current_user.__dict__)
    return render_template('settings.html', user=current_user)

@app.route('/search')
def search():
    query = request.args.get('query')
    if not query:
        return redirect(url_for('explore'))
    if len(query) > 100:
        flash("Query too long.")
        return redirect(url_for('explore'))
    # search by title
    prompts = query_database('SELECT * FROM prompts WHERE title LIKE ? ORDER BY upvotes DESC', ('%' + query + '%',))
    return render_template('search.html', prompts=prompts, query=query)

@app.route('/search_load_more', methods=['POST'])
def search_load_more():
    query = request.form['query']
    offset = int(request.form['offset'])
    if len(query) > 100:
        flash("Query too long.")
        return redirect(url_for('explore'))
    prompts = query_database('SELECT * FROM prompts WHERE title LIKE ? ORDER BY upvotes DESC LIMIT 40 OFFSET ?', ('%' + query + '%', offset))
    return jsonify(prompts)


if __name__ == '__main__':
    threading.Thread(target=publish).start()
    app.run(debug=False, host='0.0.0.0', port=8080)