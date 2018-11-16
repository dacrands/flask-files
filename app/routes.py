import os
from flask import render_template, redirect, flash, request, \
    url_for, send_from_directory
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.utils import secure_filename
from werkzeug.urls import url_parse
from app import app, db
from app.models import User, File
from app.forms import LoginForm, RegistrationForm, DeleteUserForm

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'docx', 'xlsx'])


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    files = current_user.files
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # see if user has file of same name
            # if so, prompt them to rename the file
            print(filename)
            print([file.name for file in files])
            for f in files:                
                if f.name == filename:
                    flash('You already have a file with that name! Please rename your file and upload.')
                    return redirect(url_for('index'))
            # make user's dir using ID
            if not os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], str(current_user.id))):
                os.mkdir(os.path.join(
                    app.config['UPLOAD_FOLDER'], str(current_user.id)))
            user_file_path = os.path.join(
                app.config['UPLOAD_FOLDER'], str(current_user.id))
            file.save(os.path.join(user_file_path, filename))
            user_file = File(path=os.path.join(user_file_path, filename),
                             rel_path=os.path.join(
                                 str(current_user.id), filename),
                             name=filename,
                             user_id=current_user.id)
            db.session.add(user_file)
            db.session.commit()
            flash('File uploaded!')
            return redirect(request.url)
    return render_template('index.html', files=files, user=current_user)


@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], str(current_user.id)),
                               filename)


@app.route('/delete/<filename>')
@login_required
def delete_file(filename):
    files = current_user.files
    for f in files:
        if f.name == filename:
            db.session.delete(f)
            db.session.commit()
            os.remove(f.path)
            flash('Removed file')
            return redirect('/')
    flash('File not found')
    return redirect('/')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Thanks!')
        return(redirect(url_for('login')))
    return render_template('register.html', form=form)

@app.route('/delete_user', methods=['GET', 'POST'])  
@login_required  
def delete_user():
    form = DeleteUserForm()
    if form.validate_on_submit():
        if current_user.check_password(form.password.data):
            user = User.query.filter_by(id=current_user.id).first()
            db.session.delete(user)
            db.session.commit()
            flash('Account deleted.')
            return(redirect('/'))
        flash('That password does not seem to match')
        return render_template('delete_user.html', form=form)        
    return render_template('delete_user.html', form=form)