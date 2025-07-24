from flask              import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy   import SQLAlchemy
from werkzeug.security  import generate_password_hash, check_password_hash
from collections        import defaultdict
from datetime           import datetime, date, time, timedelta
import os, getpass

app = Flask(__name__)
app.secret_key = 'tajny_klucz'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///obecnosc.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# MODELE
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    work_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# ROUTY
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('attendance'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            return redirect(url_for('attendance'))
        flash('Nieprawidłowy login lub hasło')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/attendance', methods=['GET', 'POST'])
def attendance():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Wygeneruj opcje co 15 minut
    time_options = [
        f"{(h * 15) // 60:02d}:{(h * 15) % 60:02d}"
        for h in range(0, 96)  # 96 x 15min = 24h
    ]

    user = User.query.get(session['user_id'])

    # Pobierz ostatni wpis użytkownika
    last_entry = Attendance.query.filter_by(user_id=user.id).order_by(Attendance.id.desc()).first()

    default_start = last_entry.start_time.strftime('%H:%M') if last_entry else "08:00"
    default_end = last_entry.end_time.strftime('%H:%M') if last_entry else "16:00"

    if request.method == 'POST':
        data = request.form
        start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        user_description = data.get('description', '').strip()

        work_type = data['work_type']

        if data['work_type'] in ["opieka nad dzieckiem"]:
            start_time = time(8, 0)
            end_time = time(16, 0)
            description = f"Opieka nad dzieckiem - {user_description}"
        elif data['work_type'] in ["urlop"]:
            description = f"Urlop - {user_description}"
        else:
            description = user_description


        if end_time <= start_time:
            flash('Koniec pracy musi być późniejszy niż początek.')
            return redirect(url_for('attendance'))

        entry = Attendance(
            user_id=session['user_id'],
            date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
            start_time=start_time,
            end_time=end_time,
            work_type=data['work_type'],
            description=description
        )
        
        db.session.add(entry)
        db.session.commit()
        flash('Dodano wpis')
        return redirect(url_for('attendance'))

    today = date.today().isoformat()
    
    return render_template('attendance.html', 
                            today=today, 
                            default_start=default_start, 
                            default_end=default_end, 
                            time_options=time_options
    )

@app.route('/raport')
def raport():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    entries = Attendance.query.filter_by(user_id=user.id).order_by(Attendance.date).all()

    # Grupowanie po dacie
    grouped = defaultdict(list)
    for e in entries:
        grouped[e.date].append(e)

    # Sumowanie czasu z przelicznikiem
    raport_data = []
    for date, day_entries in grouped.items():
        total_hours = 0
        details = []

        for e in day_entries:
            start_dt = datetime.combine(e.date, e.start_time)
            end_dt = datetime.combine(e.date, e.end_time)
            duration = (end_dt - start_dt).total_seconds() / 3600  # godziny jako float

            if e.work_type.lower() == "nadgodziny":
                duration *= 1.5  # przelicznik

            total_hours += duration
            details.append(e)

        raport_data.append({
            'date': date,
            'entries': details,
            'total_hours': round(total_hours, 2),
        })

    return render_template('raport.html', raport_data=raport_data, username=user.username, datetime=datetime)

@app.route('/detailraport')
def detailraport():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    entries = Attendance.query.filter_by(user_id=user.id).order_by(Attendance.date).all()

    return render_template('detailraport.html', entries=entries, username=user.username, datetime=datetime)

@app.cli.command('adduser')
def adduser():
    username = input("Login użytkownika: ")
    if User.query.filter_by(username=username).first():
        print("Użytkownik już istnieje.")
        return
    
    password = getpass.getpass("Hasło: ")
    password_hash = generate_password_hash(password)
    user = User(username=username, password_hash=password_hash)
    
    db.session.add(user)
    db.session.commit()
    
    print(f"Dodano użytkownika {username}.")

# KOMENDA INICJALIZUJĄCA
@app.cli.command('initdb')
def initdb():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password_hash=generate_password_hash('admin123'))
        db.session.add(admin)
        db.session.commit()
    print("Zainicjalizowano bazę danych.")

if __name__ == '__main__':
    app.run(host='0.0.0.0')
