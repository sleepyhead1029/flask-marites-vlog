import os
import secrets
from flask import (render_template, url_for, 
                   flash, redirect, 
                   request, abort)
from app import app, db, bcrypt, cache, mail
from app.forms import(RegistrationForm, LoginForm, 
                      UpdateAccountForm, PostForm, 
                      RequestResetForm, ResetPasswordForm)
from app.models import User, Post
from flask_login import (login_user, current_user, 
                         logout_user, login_required)
from flask_mail import Message
def displayUser():
    displayUser = User.query.count()
    return displayUser

def displayPost():
    displayPost = Post.query.count()
    return displayPost

def displayBannedPost():
    all_posts = Post.query.all()
    
    banned_contents = [post for post in all_posts if post.is_banned]

    return banned_contents

def displayBannedUser():
    all_users = User.query.all()

    banned_users = [user for user in all_users if user.is_banned]
    return banned_users

def countBannedUser():
    countBannedUser = User.query.filter(User.is_banned == 1).count()

    return countBannedUser

def countBannedPost():
    banned_post = Post.query.filter(Post.is_banned == 1).count()

    return banned_post

@app.route("/")
@app.route("/home")
def home():
    allpost = Post.query.all()
    return render_template('home.html', posts=allpost)


@app.route("/about")
def about():
    allpost = Post.query.all()
    return render_template('about.html', title='About', posts=allpost)

@app.route("/admin_login",methods = ['GET','POST'])
def login_admin():
    if current_user.is_authenticated and current_user.is_moderator:
        return redirect(url_for('admin'))

    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data) and user.is_moderator:
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('admin'))
        else:
            flash('Login Unsuccessful. Please check email, password, and moderator status', 'danger')

    return render_template('admin/admin_login.html', title='Login Admin', cache = cache, form = form, displayPost = displayPost(), displayUser = displayUser(), displayBannedPost = displayBannedPost(), countBannedPost = countBannedPost(), countBannedUser = countBannedUser())

@app.route("/admin")
def admin():
    if current_user.is_authenticated:
        # Filter the user by the currently logged-in user
        user = current_user
        return render_template('admin/index.html', title='Admin',user = user,displayPost = displayPost(), displayUser = displayUser(), displayBannedPost = displayBannedPost(), countBannedPost = countBannedPost(), countBannedUser = countBannedUser(), cache = cache)
    else:
        return render_template('admin/index.html', title='Admin',displayPost = displayPost(), displayUser = displayUser(), displayBannedPost = displayBannedPost(), countBannedPost = countBannedPost(), countBannedUser = countBannedUser(), cache = cache)

@app.route("/users")
def users():
    users = User.query.all()
    user = current_user
    images = os.listdir(os.path.join(app.static_folder, "images"))
    if current_user.is_authenticated:
        return render_template('admin/users.html', title='User', users = users,user = user,images = images, displayPost = displayPost(), displayUser = displayUser(), countBannedPost = countBannedPost(), countBannedUser = countBannedUser(), cache = cache)
    else:
        return redirect(url_for('admin'))
    
@app.route("/posts")
def posts():
    users = User.query.all()
    user = current_user
    posts = Post.query.all()
    if current_user.is_authenticated:
        return render_template('admin/posts.html', title='Posts',user = user,users = users, posts = posts,displayPost = displayPost(), displayUser = displayUser(), countBannedPost = countBannedPost(), countBannedUser = countBannedUser(), cache = cache)
    else:
        return redirect(url_for('admin'))

@app.route("/banned_users")
def banned_users():
    user = current_user
    return render_template('admin/banned_users.html', title='Banned Users',user = user, displayPost = displayPost(), displayUser = displayUser(), countBannedPost = countBannedPost(), countBannedUser = countBannedUser(), users = displayBannedUser(), cache = cache)

@app.route("/banned_contents")
def banned_contents():
    user = current_user
    return render_template('admin/banned_contents.html', title='Banned Content',user = user ,posts = displayBannedPost(), displayPost = displayPost(), displayUser = displayUser(), countBannedPost = countBannedPost(), countBannedUser = countBannedUser(), cache = cache)

@app.route('/banned_contents/<int:id>', methods=['GET','POST'])
def banned_content(id):
    post = Post.query.get_or_404(id)

    # Toggle the value of is_banned
    post.is_banned = not post.is_banned

    db.session.commit()

    action = "unbanned" if not post.is_banned else "banned"
    flash(f'You have just {action} post titled {post.title}', 'success')

    existing_messages = cache.get('latest_flash_messages') or []
    existing_messages.append(f'You have just {action} post titled {post.title}')
    cache.set('latest_flash_messages', existing_messages)

    # Update the notification count
    notification_count = cache.get('notification_count') or 0
    cache.set('notification_count', notification_count + 1)

    return redirect(url_for('banned_contents'))

@app.route('/banned_users/<int:id>', methods=['GET','POST'])
def banned_user(id):
    user = User.query.get_or_404(id)

    # Toggle the value of is_banned
    user.is_banned = not user.is_banned

    db.session.commit()

    action = "unbanned" if not user.is_banned else "banned"
    flash(f'You have just {action} user {user.username}', 'success')

    existing_messages = cache.get('latest_flash_messages') or []
    existing_messages.append(f'You have just {action} user {user.username}')
    cache.set('latest_flash_messages', existing_messages)

    # Update the notification count
    notification_count = cache.get('notification_count') or 0
    cache.set('notification_count', notification_count + 1)

    return redirect(url_for('banned_users'))

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password,is_moderator = 0,is_banned = 0)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data) and not user.is_banned:
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password, or you have been banned.', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()


    return redirect(url_for('home'))

@app.route("/logout_admin")
def logoutadmin():
    logout_user()


    return redirect(url_for('admin'))
def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
    form_picture.save(picture_path)
    return picture_fn

@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    latest_post = Post.query.filter_by(author=current_user).order_by(Post.date_posted.desc()).all()
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Account updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form,posts = latest_post)

@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    allpost = Post.query.all()
    form = PostForm()
    if form.validate_on_submit():
            post = Post(title=form.title.data, content=form.content.data, author=current_user, is_banned = 0)
            db.session.add(post)
            db.session.commit()
            flash('Posted!', 'success')
            return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post',form=form, legend='New Post',posts = allpost)

@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)

@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    allpost = Post.query.all()
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Post updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post',
                           form=form, legend='Update Post', posts = allpost)

@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request', 
                  sender = "hardwellapollo1029@yahoo.com",
                  recipients=[user.email])
    msg.body = f''' To reset your password, visit the following link:
    {url_for('reset_token', token = token, _external=True)}
    If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)
    pass

@app.route("/reset_password", methods=['GET','POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', Title = 'Reset Password', form=form)

@app.route("/reset_password/<token>", methods=['GET','POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)

    if user is None:
        flash('That is an invalid or expired token.','warning')
        return redirect(url_for('reset_request'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html',title='Reset Password', form=form)