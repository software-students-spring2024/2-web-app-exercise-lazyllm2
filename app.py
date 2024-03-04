from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from bson.objectid import ObjectId
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId
import ssl
from dotenv import load_dotenv
import os


# Load environment variables
load_dotenv()

# Flask application instance
app = Flask(__name__)

# Secret key
app.secret_key = os.getenv('SECRET_KEY', 'a_default_fallback_secret_key')


# Setup MongoDB connection

mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri, tls=True, tlsAllowInvalidCertificates=True)
db = client['FitnessTracker']  
workouts = db.workouts     

# Initialize Flask-Login

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Specify what view handles logins

# Initialize Flask-Bcrypt for password hashing
bcrypt = Bcrypt(app)

class User(UserMixin):
    def __init__(self, user_id, username):
        self.id = str(user_id)
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    user = db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return None
    return User(user['_id'], user['username'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = db.users.find_one({"username": username})
        if user and bcrypt.check_password_hash(user['password'], password):
            user_obj = User(user['_id'], username)
            login_user(user_obj)
            return redirect(url_for('home'))
        else:
            return 'Invalid username or password'
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        db.users.insert_one({"username": username, "password": hashed_password})
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

# Home route
@app.route('/')
@login_required
def home():
    # Filter workouts by the current user's ID
    user_workouts = workouts.find({'user_id': current_user.id}).sort('date',-1)
    return render_template('home.html', workouts=user_workouts)

# Add workout form
@app.route('/add-workout', methods=['GET', 'POST'])
@login_required
def add_workout():
    if request.method == 'POST':
        work_type = request.form.get('type')
        duration = int(request.form.get('duration'))
        # Extract form data and include user_id
        calories_per_minute = {
            'Running': 12,  
            'Spinning': 10,   
            'Jump Rope': 15, 
            'Swimming': 12,
            'Rowing': 11,  
            'Weight Lifting': 4,   
            'Push-ups': 8, 
            'Pull-ups': 9,
            'Squats': 8,
            'Deadlifts': 8
        }
        calories_burned = duration * calories_per_minute.get(work_type, 5)
        workout_data = {
            'type': work_type,
            'duration': duration,
            'calories': calories_burned,
            'date': request.form.get('date'),
            'user_id': current_user.id  # Associate workout with the current user's ID
        }
        workouts.insert_one(workout_data)
        return redirect(url_for('home'))
    return render_template('add_workout.html')



# Edit workout form
@app.route('/edit/<workout_id>', methods=['GET', 'POST'])
@login_required
def edit_workout(workout_id):
    # Fetch the workout only if it belongs to the current user
    workout = workouts.find_one({'_id': ObjectId(workout_id), 'user_id': current_user.id})
    
    if request.method == 'POST':
        updates = {
            'type': request.form.get('type'),
            'duration': int(request.form.get('duration')),
            'calories': int(request.form.get('calories')),
            'date': request.form.get('date'),
            # user_id remains unchanged to maintain the ownership of the workout
            'user_id': current_user.id  
        }
        # Update the workout with the new values, belongs to the current user
        workouts.update_one({'_id': ObjectId(workout_id), 'user_id': current_user.id}, {'$set': updates})
        return redirect(url_for('home'))

    return render_template('edit_workout.html', workout=workout)

# Delete workout
@app.route('/delete/<workout_id>', methods=['POST'])
@login_required
def delete_workout(workout_id):
    # delete the workout only if it belongs to the current user
    workouts.delete_one({'_id': ObjectId(workout_id), 'user_id': current_user.id})
    return redirect(url_for('home'))

# Search workouts for individual users
@app.route('/filter', methods=['GET'])
@login_required  # Ensure only authenticated users can search
def filter_workouts():
    filter_date = request.args.get('filter_date')
    filter_type = request.args.get('filter_type')
    query = {"user_id": current_user.id}

    if filter_date:
        datetime.strptime(filter_date, '%Y-%m-%d')
        query["date"] = filter_date

    if filter_type:
        query["type"] = filter_type

    search_results = workouts.find(query)

    return render_template('search_results.html', workouts=search_results)


# Start the application
if __name__ == '__main__':
    app.run(debug=True)
