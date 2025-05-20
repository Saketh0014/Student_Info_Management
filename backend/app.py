from flask import Flask, request, jsonify, send_from_directory
from flask_restx import Api, Resource, fields
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__, static_folder='../frontend', static_url_path='/')
CORS(app)  # Enable CORS for all routes
api = Api(app, version='1.0', title='Student Admission API',
          description='A simple Student Admission API')

# Database setup
DB_NAME = 'backend/database.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Check if students table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='students'")
    if not cursor.fetchone():
        cursor.execute('''
            CREATE TABLE students (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                class TEXT NOT NULL,
                grade TEXT NOT NULL,
                email TEXT,
                phone TEXT
            )
        ''')
        conn.commit()
    else:
        # Check if email column exists
        cursor.execute("PRAGMA table_info(students)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'email' not in columns:
            cursor.execute("ALTER TABLE students ADD COLUMN email TEXT")
        if 'phone' not in columns:
            cursor.execute("ALTER TABLE students ADD COLUMN phone TEXT")
        conn.commit()
    conn.close()

init_db()

student_model = api.model('Student', {
    'id': fields.String(required=True, description='Student ID'),
    'name': fields.String(required=True, description='Student Name'),
    'age': fields.Integer(required=True, description='Student Age'),
    'class': fields.String(required=True, description='Student Class'),
    'grade': fields.String(required=True, description='Student Grade'),
    'email': fields.String(required=False, description='Student Email'),
    'phone': fields.String(required=False, description='Student Phone Number'),
})

search_parser = api.parser()
search_parser.add_argument('id', type=str, required=False, help='Student ID')
search_parser.add_argument('name', type=str, required=False, help='Student Name')
search_parser.add_argument('age', type=int, required=False, help='Student Age')

@api.route('/students')
class StudentList(Resource):
    @api.expect(search_parser)
    def get(self):
        args = search_parser.parse_args()
        id_ = args.get('id')
        name = args.get('name')
        age = args.get('age')

        query = "SELECT id, name, age, class, grade, email, phone FROM students WHERE 1=1"
        params = []

        if id_:
            query += " AND id = ?"
            params.append(id_)
        if name:
            query += " AND name = ?"
            params.append(name)
        if age is not None:
            query += " AND age = ?"
            params.append(age)

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return {'message': 'No student found'}, 404

        students = []
        for row in rows:
            students.append({
                'id': row[0],
                'name': row[1],
                'age': row[2],
                'class': row[3],
                'grade': row[4],
                'email': row[5] if len(row) > 5 else None,
                'phone': row[6] if len(row) > 6 else None
            })
        return students


    @api.expect(student_model)
    def post(self):
        data = api.payload
        id_ = data.get('id')
        name = data.get('name')
        age = data.get('age')
        class_ = data.get('class')
        grade = data.get('grade')
        email = data.get('email')
        phone = data.get('phone')

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO students (id, name, age, class, grade, email, phone) VALUES (?, ?, ?, ?, ?, ?, ?)',
                           (id_, name, age, class_, grade, email, phone))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return {'message': 'Student with this ID already exists'}, 400
        conn.close()
        return {'message': 'Student created successfully'}, 201

@app.route('/search')
def serve_search():
    return send_from_directory(app.static_folder, 'search.html')

@app.route('/new_admission')
def serve_new_admission():
    return send_from_directory(app.static_folder, 'new_admission.html')

@api.route('/students/<string:id>')
class Student(Resource):
    @api.expect(student_model)
    def put(self, id):
        data = api.payload
        name = data.get('name')
        age = data.get('age')
        class_ = data.get('class')
        grade = data.get('grade')
        email = data.get('email')
        phone = data.get('phone')

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM students WHERE id = ?', (id,))
        if not cursor.fetchone():
            conn.close()
            return {'message': 'Student not found'}, 404

        cursor.execute('''
            UPDATE students
            SET name = ?, age = ?, class = ?, grade = ?, email = ?, phone = ?
            WHERE id = ?
        ''', (name, age, class_, grade, email, phone, id))
        conn.commit()
        conn.close()
        return {'message': 'Student updated successfully'}, 200

if __name__ == '__main__':
    app.run(debug=True)
