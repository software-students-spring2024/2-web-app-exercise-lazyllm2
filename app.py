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

# Setup MongoDB connection

mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri, tls=True, tlsAllowInvalidCertificates=True)
db = client['FitnessTracker']  
workouts = db.workouts     

# @app.route('/')
# def home():
#     return "Hello, Fitness Tracker!"


# Define a list of workouts to insert
initial_workouts = [
    {"type": "Running", "duration": 30, "calories": 300, "date": "2024-02-27"},
    {"type": "Cycling", "duration": 45, "calories": 450, "date": "2024-02-26"},
    {"type": "Swimming", "duration": 30, "calories": 330, "date": "2024-02-25"},
    {"type": "Walking", "duration": 60, "calories": 200, "date": "2024-02-24"},
]

# Insert the workouts into the collection
workouts.insert_many(initial_workouts)

print("Initial data added to the FitnessTracker database.")


# Home route
@app.route('/')
def home():
    all_workouts = workouts.find()
    return render_template('home.html', workouts=all_workouts)

# Add workout form
@app.route('/add-workout', methods=['GET', 'POST'])
def add_workout():
    if request.method == 'POST':
        # Extract form data
        workout_data = {
            'type': request.form.get('type'),
            'duration': int(request.form.get('duration')),
            'calories': int(request.form.get('calories')),
            'date': request.form.get('date')
        }
        workouts.insert_one(workout_data)
        return redirect(url_for('home'))
    return render_template('add_workout.html')

# Edit workout form
@app.route('/edit/<workout_id>', methods=['GET', 'POST'])
def edit_workout(workout_id):
    workout = workouts.find_one({'_id': ObjectId(workout_id)})
    if request.method == 'POST':
        updates = {
            'type': request.form.get('type'),
            'duration': int(request.form.get('duration')),
            'calories': int(request.form.get('calories')),
            'date': request.form.get('date')
        }
        workouts.update_one({'_id': ObjectId(workout_id)}, {'$set': updates})
        return redirect(url_for('home'))
    return render_template('edit_workout.html', workout=workout)

# Delete workout
@app.route('/delete/<workout_id>', methods=['POST'])
def delete_workout(workout_id):
    workouts.delete_one({'_id': ObjectId(workout_id)})
    return redirect(url_for('home'))

# Search workouts
@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        query = request.form.get('search_term', '')
        if query:  # Check if search_term is not empty
            search_results = workouts.find({"type": {"$regex": query, "$options": "i"}})
        else:
            search_results = []  # No search term provided, so no results
        return render_template('search_results.html', workouts=search_results)
    return render_template('search.html')


# Start the application
if __name__ == '__main__':
    app.run(debug=True)
