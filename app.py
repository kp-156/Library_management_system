from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://username:password@localhost/library_management'
db = SQLAlchemy(app)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    outstanding_debt = db.Column(db.Float, default=0.0)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    issue_date = db.Column(db.Date)
    return_date = db.Column(db.Date)
    fee = db.Column(db.Float)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/books', methods=['GET', 'POST'])
def manage_books():
    if request.method == 'GET':
        books = Book.query.all()
        book_list = [{'id': book.id, 'title': book.title, 'author': book.author, 'quantity': book.quantity} for book in books]
        return jsonify(book_list)
    elif request.method == 'POST':
        data = request.json
        new_book = Book(title=data['title'], author=data['author'], quantity=data['quantity'])
        db.session.add(new_book)
        db.session.commit()
        return jsonify({'message': 'Book added successfully'})

@app.route('/api/members', methods=['GET', 'POST'])
def manage_members():
    if request.method == 'GET':
        members = Member.query.all()
        member_list = [{'id': member.id, 'name': member.name, 'outstanding_debt': member.outstanding_debt} for member in members]
        return jsonify(member_list)
    elif request.method == 'POST':
        data = request.json
        new_member = Member(name=data['name'], outstanding_debt=data['outstanding_debt'])
        db.session.add(new_member)
        db.session.commit()
        return jsonify({'message': 'Member added successfully'})

@app.route('/api/transactions/issue', methods=['POST'])
def issue_book():
    data = request.json
    book_id = data['book_id']
    member_id = data['member_id']

    book = Book.query.get(book_id)
    member = Member.query.get(member_id)

    if not book or not member:
        return jsonify({'error': 'Book or member not found'}), 404

    if book.quantity <= 0:
        return jsonify({'error': 'Book is out of stock'}), 400

    # Issue the book and update quantities
    book.quantity -= 1
    db.session.add(Transaction(book_id=book_id, member_id=member_id, issue_date=datetime.now()))
    db.session.commit()

    return jsonify({'message': 'Book issued successfully'})

@app.route('/api/transactions/return', methods=['POST'])
def return_book():
    data = request.json
    transaction_id = data['transaction_id']
    return_date = datetime.now()

    transaction = Transaction.query.get(transaction_id)
    if not transaction:
        return jsonify({'error': 'Transaction not found'}), 404

    # Calculate and charge fees
    days_delayed = (return_date - transaction.issue_date).days
    fee = 0.0

    if days_delayed > 7:
        fee = (days_delayed - 7) * 10  # Assuming Rs. 10 fee per day after 7 days

    transaction.return_date = return_date
    transaction.fee = fee
    db.session.commit()

    return jsonify({'message': 'Book returned successfully'})

if __name__ == '__main__':
    app.run(debug=True)
