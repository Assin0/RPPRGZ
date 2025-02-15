from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Ticket
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Настройка подключения к PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:password@localhost:5432/rggz'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key')
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.json
        new_user = User(username=data['username'], password=data['password'])
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'User registered successfully'}), 201
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json
        user = User.query.filter_by(username=data['username'], password=data['password']).first()
        if user:
            login_user(user)
            return jsonify({'message': 'Login successful'}), 200  # Возвращаем JSON
        return jsonify({'message': 'Invalid credentials'}), 401  # Возвращаем JSON
    return render_template('login.html')

@app.route('/tickets', methods=['GET'])
@login_required
def tickets():
    if current_user.role == 'admin':
        tickets = Ticket.query.all()
    else:
        tickets = Ticket.query.filter_by(user_id=current_user.id).all()
    return render_template('tickets.html', tickets=tickets)

@app.route('/tickets', methods=['POST'])
@login_required
def create_ticket():
    data = request.json
    new_ticket = Ticket(user_id=current_user.id, title=data['title'], description=data['description'])
    db.session.add(new_ticket)
    db.session.commit()
    return jsonify({'message': 'Ticket created successfully', 'id': new_ticket.id}), 201

@app.route('/tickets/<int:ticket_id>', methods=['GET'])
@login_required
def get_ticket(ticket_id):
    ticket = Ticket.query.get(ticket_id)
    if ticket and (ticket.user_id == current_user.id or current_user.role == 'admin'):
        return jsonify({
            'id': ticket.id,
            'title': ticket.title,
            'description': ticket.description,
            'status': ticket.status
        }), 200
    return jsonify({'message': 'Ticket not found or access denied'}), 404

@app.route('/tickets/<int:ticket_id>', methods=['PUT'])
@login_required
def update_ticket(ticket_id):
    ticket = Ticket.query.get(ticket_id)
    if ticket and (ticket.user_id == current_user.id or current_user.role == 'admin'):
        data = request.json
        ticket.title = data.get('title', ticket.title)
        ticket.description = data.get('description', ticket.description)
        ticket.status = data.get('status', ticket.status)
        db.session.commit()
        return jsonify({'message': 'Ticket updated successfully'}), 200
    return jsonify({'message': 'Ticket not found or access denied'}), 404

@app.route('/tickets/<int:ticket_id>', methods=['DELETE'])
@login_required
def delete_ticket(ticket_id):
    ticket = Ticket.query.get(ticket_id)
    if ticket and (ticket.user_id == current_user.id or current_user.role == 'admin'):
        db.session.delete(ticket)
        db.session.commit()
        return jsonify({'message': 'Ticket deleted successfully'}), 200
    return jsonify({'message': 'Ticket not found or access denied'}), 404

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Создание таблиц в базе данных
    app.run(debug=os.environ.get('FLASK_DEBUG', 'False') == 'True')