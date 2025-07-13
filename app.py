from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import csv
import io

app = Flask(__name__)
app.secret_key = 'sygesco_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sygesco.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password_hash = db.Column(db.String(200))
    role = db.Column(db.String(50))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Eleve(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100))
    prenom = db.Column(db.String(100))
    classe = db.Column(db.String(50))

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        pwd = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(pwd):
            session['user_id'] = user.id
            session['role'] = user.role
            flash('Connexion réussie', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Identifiants invalides', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    users_count = User.query.count()
    eleves_count = Eleve.query.count()
    return render_template('dashboard.html', users_count=users_count, eleves_count=eleves_count)

@app.route('/eleves')
def eleves():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    eleves_list = Eleve.query.all()
    return render_template('eleves.html', eleves=eleves_list)

@app.route('/eleves/export')
def export_eleves_csv():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    eleves_list = Eleve.query.all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Nom', 'Prénom', 'Classe'])
    for e in eleves_list:
        writer.writerow([e.id, e.nom, e.prenom, e.classe])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv', download_name='eleves.csv', as_attachment=True)

def init_db():
    db.drop_all()
    db.create_all()
    admin = User(email='admin@sygesco.com', role='admin')
    admin.set_password('sygesco123')
    enseignant = User(email='enseignant@sygesco.com', role='enseignant')
    enseignant.set_password('sygesco123')
    db.session.add_all([admin, enseignant])
    db.session.add_all([
        Eleve(nom='EYEBE', prenom='Joël', classe='Terminale'),
        Eleve(nom='NGUESSAN', prenom='Marie', classe='Première')
    ])
    db.session.commit()

if __name__ == '__main__':
    if not os.path.exists('sygesco.db'):
        init_db()
    app.run(debug=True)
