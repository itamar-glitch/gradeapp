from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from flask_bcrypt import Bcrypt
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/gradeapp'

mongo = PyMongo(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User class to handle user login and session
class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']
        self.password = user_data['password']

@login_manager.user_loader
def load_user(user_id):
    user_data = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if user_data:
        return User(user_data)
    return None

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = mongo.db.users.find_one({'username': username})
        if user:
            flash('Username already exists!', 'danger')
        else:
            # Hash the password before saving to the database
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            user_id = mongo.db.users.insert_one({'username': username, 'password': hashed_password}).inserted_id
            
            # Initialize averages in a new collection for the user
            semester_averages = {
                'user_id': str(user_id),  # Include the user ID
                'averages': {
                    'year_1': {'semester_1':{'Points':0,'AP':0}, 'semester_2':{'Points':0,'AP':0}, 'semester_3': {'Points':0,'AP':0}},
                    'year_2': {'semester_1': {'Points':0,'AP':0}, 'semester_2': {'Points':0,'AP':0}, 'semester_3': {'Points':0,'AP':0}},
                    'year_3': {'semester_1': {'Points':0,'AP':0}, 'semester_2': {'Points':0,'AP':0}, 'semester_3': {'Points':0,'AP':0}},
                    'year_4': {'semester_1': {'Points':0,'AP':0}, 'semester_2': {'Points':0,'AP':0}, 'semester_3': {'Points':0,'AP':0}}
                }
            }

            # Insert the averages into the averages collection
            mongo.db.averages.insert_one(semester_averages)

            flash('Your account has been created!', 'success')
            return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_data = mongo.db.users.find_one({'username': username})
        if user_data and bcrypt.check_password_hash(user_data['password'], password):
            user = User(user_data)  # Create a User object
            login_user(user)  # Log in the user
            return redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html')

@app.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/get_courses', methods=['GET'])
@login_required
def get_courses():
    year = int(request.args.get('year'))
    semester = int(request.args.get('semester'))
    
    # Fetch courses based on the selected year and semester
    courses = mongo.db.courses.find({'user_id': current_user.id, 'year': year, 'semester': semester})
    courses_list = [{'name': course['name'], 'grade': course['grade'], 'Academic_point': course['Academic_point']} for course in courses]
    
    return jsonify({'courses': courses_list})

@app.route('/add_course', methods=['POST'])
@login_required
def add_course():
    course_name = request.form['course_name']
    grade = request.form['grade']
    nakaz = int(request.form['nakaz'])
    year = int(request.form['year'])
    semester = int(request.form['semester'])
    
    # Insert the new course into the database
    mongo.db.courses.insert_one({
        'name': course_name, 
        'Academic_point': nakaz,
        'grade': grade, 
        'year': year, 
        'semester': semester, 
        'user_id': current_user.id
    })
    
    # Update averages
    mongo.db.averages.update_one(
        {'user_id': str(current_user.id)},  # Find the averages document by user ID
        {'$inc': {
            f'averages.year_{year}.semester_{semester}.Points': int(grade)*int(nakaz),
            f'averages.year_{year}.semester_{semester}.AP': int(nakaz)
        }}
    )
    
    return jsonify({'message': 'Course added successfully!'})

@app.route('/get_avg', methods=['GET'])
@login_required
def get_avg():
    logging.debug("Fetching courses for user: %s", current_user.id) 
    courses = mongo.db.courses.find({'user_id': current_user.id})
    avg = mongo.db.averages.find_one({"user_id": current_user.id}, {"averages": 1})

    if avg and "averages" in avg:
        total_points_by_year = 0
        total_ap_by_year = {}
        yearly_average=[]
        count=0
        AP=0
        average_grade=[]
        for year in avg['averages']:
            count,AP,total_points_by_year=0,0,0
            for semester in avg['averages'][year]:
                count+=1
                total_points_by_year +=int(avg['averages'][year][semester]['Points'])
                AP+=avg['averages'][year][semester]['AP']
                if count==2 and AP!=0:
                    average_grade.append(total_points_by_year/AP)
                elif count==2:
                    average_grade.append(0)
    # Return the average as JSON
    return jsonify({'average_grade': average_grade})

@app.route('/get_semester_averages', methods=['GET'])
@login_required
def get_semester_averages():
    averages = mongo.db.averages.find_one({'user_id': str(current_user.id)})
    
    if averages:
        semester_averages = averages['averages']
        return jsonify({'averages': semester_averages})
    else:
        return jsonify({'message': 'No averages found for this user.'}), 404

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host="192.168.56.101", port=8081, debug=True)
