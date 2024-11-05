from flask import request, jsonify,url_for
from models import User, Testimonial, AidDistribution, Donation,Contact, Charity,Payment # Import Donation model
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from app import app, db  # Ensure these imports are after app.py is set up
from paypalrestsdk import Payment as PayPalPayment
import paypalrestsdk
import time
import logging
from flask_mail import Mail, Message
from flask import render_template
from app import app, mail 
from models import User  # Import your User model
from werkzeug.utils import secure_filename
from flask_bcrypt import Bcrypt
import os
from datetime import datetime



bcrypt = Bcrypt(app)
jwt = JWTManager(app)
# Configure PayPal SDK
paypalrestsdk.configure({
    "mode": "sandbox",
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET",
    "http_timeout": 30  # Set a higher timeout in seconds
})

mail = Mail(app)

logging.basicConfig(level=logging.INFO)

# Set up allowed extensions and upload folder
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'doc', 'docx'}
UPLOAD_FOLDER = 'uploads'

# Ensure upload folders exist
os.makedirs(os.path.join(UPLOAD_FOLDER, 'images'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'documents'), exist_ok=True)

@app.route('/')
def home():
    return jsonify({'message': 'Hello, World!'})

@app.route('/current_user', methods=['GET'])
@jwt_required()
def get_current_user():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    return jsonify(user.to_dict()), 200

@app.route('/users', methods=['GET'])
@jwt_required()
def get_all_users():
    users = User.query.all()
    serialized_users = [{'id': user.id, 'username': user.username, 'email': user.email,
                         'password': user.password, 'user_type': user.user_type} for user in users]
    return jsonify({'users': serialized_users})


@app.route('/login', methods=['POST'])
def login_user():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    
    if user is None:
        return jsonify({"message": "User not found"}), 404
    
    logging.info(f"User found: {user.username}, Hashed Password: {user.password}")
    
    try:
        if bcrypt.check_password_hash(user.password, data['password']):
            access_token = create_access_token(identity=user.id)
            return jsonify({"access_token": access_token, "user_type": user.user_type}), 200
    except Exception as e:
        logging.error(f"Error checking password: {e}")
    
    return jsonify({"message": "Invalid email or password"}), 401




@app.route('/users', methods=['POST'])
def register_user():
    data = request.get_json()

    # Check if the user already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"message": "User with this email already exists"}), 400

    # Create a new user
    new_user = User(
        username=data['username'],
        email=data['email'],
        password=bcrypt.generate_password_hash(data['password']).decode('utf-8'),
        user_type=data['user_type']  # Ensure you handle the user_type appropriately
    )

    # Add the new user to the session and commit
    db.session.add(new_user)
    db.session.commit()

    # Create an access token
    access_token = create_access_token(identity=new_user.id)
    return jsonify({"user_id": new_user.id, "token": access_token}), 201

@app.route('/login', methods=['GET'])
@jwt_required()
def validate_token():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if user:
        return jsonify({
            'message': 'Token is valid',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'user_type': user.user_type  # Include user_type if needed
            }
        }), 200
    else:
        return jsonify({'message': 'User not found'}), 404

@app.route('/update-password', methods=['PATCH'])
@jwt_required()
def update_profile():
    current_user = get_jwt_identity()
    logging.debug(f"PATCH /profile called for user: {current_user}")

    user = User.query.filter_by(id=current_user).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404

    data = request.get_json()
    logging.debug(f"Request data: {data}")


    if 'email' in data:
        user.email = data['email']
    if 'currentPassword' in data and 'newPassword' in data and 'confirmPassword' in data:
        if not bcrypt.check_password_hash(user.password, data['currentPassword']):
            return jsonify({'message': 'Current password is incorrect'}), 400
        if data['newPassword'] != data['confirmPassword']:
            return jsonify({'message': 'New passwords do not match'}), 400
        user.password = bcrypt.generate_password_hash(data['newPassword']).decode('utf-8')

    db.session.commit()

    return jsonify({'message': 'Profile updated successfully'})
@app.route('/update-account', methods=['PATCH'])
@jwt_required()
def update_account():
    current_user = get_jwt_identity()
    logging.debug(f"PATCH /update-account called for user: {current_user}")

    user = User.query.filter_by(id=current_user).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404

    data = request.get_json()
    logging.debug(f"Request data: {data}")

    if 'username' in data:
        user.username = data['username']
    if 'email' in data:
        user.email = data['email']

    db.session.commit()

    return jsonify({'message': 'Account information updated successfully'}), 200
@app.route('/donate', methods=['POST'])
@jwt_required()  # Require the user to be logged in
def donate():
    data = request.json

    # Get the user ID from the JWT token
    user_id = get_jwt_identity()
    if user_id is None:
        return jsonify({"error": "User ID is missing"}), 400

    new_donation = Donation(
        first_name=data['first_name'],
        last_name=data['last_name'],
        email=data['email'],
        user_id=user_id,  # Set user_id from JWT
        donation_amount=data['donation_amount'],
        cause_id=data.get('cause_id'),
        agree_to_terms=data['agree_to_terms'],
        subscribe_monthly=data['subscribe_monthly']
    )
    db.session.add(new_donation)
    db.session.commit()

    return jsonify({"message": "Donation successful"}), 201
@app.route('/donors', methods=['GET'])
def get_donors():
    donations = Donation.query.all()
    serialized_donors = [
        {
            'first_name': donation.first_name,
            'last_name': donation.last_name,
            'email': donation.email,
            'cause_id': donation.cause_id,
            'agree_to_terms': donation.agree_to_terms,
            'subscribe_monthly': donation.subscribe_monthly,
            'donation_amount': donation.donation_amount,
            'created_at': donation.created_at
        }
        for donation in donations
    ]
    return jsonify({'donors': serialized_donors})

@app.route('/donor/<int:user_id>/donations', methods=['GET'])
@jwt_required()
def get_donations_by_donor(user_id):
    # Verify the donor's identity using the JWT
    current_user_id = get_jwt_identity()
    if current_user_id != user_id:
        return jsonify({"message": "Unauthorized"}), 403

    # Retrieve donations for the specified donor
    donations = Donation.query.filter_by(user_id=user_id).all()
    serialized_donations = [
        {
            'id': donation.id,
            'first_name': donation.first_name,
            'last_name': donation.last_name,
            'email': donation.email,
            'cause_id': donation.cause_id,
            'agree_to_terms': donation.agree_to_terms,
            'subscribe_monthly': donation.subscribe_monthly,
            'donation_amount': donation.donation_amount,
            'created_at': donation.created_at
        }
        for donation in donations
    ]
    
    return jsonify({'donations': serialized_donations}), 200


@app.route('/testimonials', methods=['POST'])
def add_testimonial():
    data = request.json
    new_testimonial = Testimonial(
        content=data['content'],
        user_id=data['user_id']
    )
    db.session.add(new_testimonial)
    db.session.commit()
    return jsonify({"message": "Testimonial added"}), 201

@app.route('/testimonials', methods=['GET'])
def get_testimonials():
    testimonials = Testimonial.query.all()
    return jsonify([t.content for t in testimonials])

@app.route('/distributions', methods=['POST'])
def post_aid_distribution():
    data = request.json
    new_aid_distribution = AidDistribution(
        beneficiary_name=data['beneficiary_name'],
        amount=data['amount'],
        description=data['description']
    )
    db.session.add(new_aid_distribution)
    db.session.commit()
    return jsonify({"message": "Aid distribution posted"}), 201

@app.route('/distributions', methods=['GET'])
def get_aid_distributions():
    distributions = AidDistribution.query.all()
    return jsonify([
        {
            'beneficiary_name': d.beneficiary_name,
            'amount': d.amount,
            'description': d.description
        }
        for d in distributions
    ])

@app.route('/contacts', methods=['POST'])
def add_contact():
    data = request.json
    new_contact = Contact(
        first_name=data['first_name'],
        last_name=data['last_name'],
        email=data['email'],
        phonenumber=data.get('phonenumber'),
        description=data['description']
    )
    db.session.add(new_contact)
    db.session.commit()
    return jsonify({"message": "Contact added successfully"}), 201

@app.route('/contacts', methods=['GET'])
def get_contacts():
    contacts = Contact.query.all()
    serialized_contacts = [
        {
            'id': contact.id,
            'first_name': contact.first_name,
            'last_name': contact.last_name,
            'email': contact.email,
            'phonenumber': contact.phonenumber,
            'description': contact.description
        }
        for contact in contacts
    ]
    return jsonify({'contacts': serialized_contacts}), 200

# User Admin
def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

# @app.route('/charity', methods=['POST'])
# def add_charity():
#     data = request.form.to_dict()
#     print("Received data:", data)

#     # Handle image file upload
#     image_file = request.files.get('image')
#     if image_file and allowed_file(image_file.filename, ALLOWED_IMAGE_EXTENSIONS):
#         image_filename = secure_filename(image_file.filename)
#         image_path = os.path.join(UPLOAD_FOLDER, 'images', image_filename)
#         image_file.save(image_path)
#     else:
#         return jsonify({"message": "Invalid image format"}), 400

#     # Handle document file upload
#     document_file = request.files.get('document')
#     if document_file and allowed_file(document_file.filename, ALLOWED_DOCUMENT_EXTENSIONS):
#         document_filename = secure_filename(document_file.filename)
#         document_path = os.path.join(UPLOAD_FOLDER, 'documents', document_filename)
#         document_file.save(document_path)
#     else:
#         return jsonify({"message": "Invalid document format"}), 400

#     user_id = data.get('user_id')
#     if not user_id:
#         return jsonify({'error': 'User ID is required'}), 400

#     # Create a new Charity record in the database
#     new_charity = Charity(
#         first_name=data.get('first_name'),
#         last_name=data.get('last_name'),
#         category=data.get('category'),
#         title=data.get('title'),
#         description=data.get('description'),
#         image=image_path,  # Store the image file path
#         amount=data.get('amount'),
#         email=data.get('email'),
#         created_at=datetime.utcnow(),
#         updated_at=datetime.utcnow(),
#         user_id=user_id, 
#         document=document_path # Store the document file path
#     )
#     db.session.add(new_charity)
#     db.session.commit()

#     return jsonify({"message": "Charity added successfully"}), 201

@app.route('/charity', methods=['POST'])
def add_charity():
    data = request.form.to_dict()
    print("Received data:", data)  # Log the incoming data

    # Validate required fields
    required_fields = ['first_name', 'last_name', 'title', 'description', 'category', 'email', 'amount', 'user_id']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400

    # Handle image file upload
    image_file = request.files.get('image')
    if image_file and allowed_file(image_file.filename, ALLOWED_IMAGE_EXTENSIONS):
        image_filename = secure_filename(image_file.filename)
        image_path = os.path.join(UPLOAD_FOLDER, 'images', image_filename)
        image_file.save(image_path)
    else:
        return jsonify({"message": "Invalid image format"}), 400

    # Handle document file upload
    document_file = request.files.get('document')
    if document_file and allowed_file(document_file.filename, ALLOWED_DOCUMENT_EXTENSIONS):
        document_filename = secure_filename(document_file.filename)
        document_path = os.path.join(UPLOAD_FOLDER, 'documents', document_filename)
        document_file.save(document_path)
    else:
        return jsonify({"message": "Invalid document format"}), 400

    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400

    # Create a new Charity record in the database
    new_charity = Charity(
        first_name=data.get('first_name'),
        last_name=data.get('last_name'),
        category=data.get('category'),
        title=data.get('title'),
        description=data.get('description'),
        image=image_path,
        amount=int(data.get('amount')),  # Ensure amount is an integer
        email=data.get('email'),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        user_id=user_id,
        document=document_path
    )
    db.session.add(new_charity)
    db.session.commit()

    return jsonify({"message": "Charity added successfully"}), 201


@app.route('/charity', methods=['GET'])
def get_charity():
    charity = Charity.query.all()
    serialized_charity = [
        {
            'id': charity.id,
            'first_name': charity.first_name,
            'last_name': charity.last_name,
            'image': charity.image,
            'amount': charity.amount,
            'title': charity.title,  
            'email': charity.email,
            'document': charity.document,
            'category': charity.category,
            'description': charity.description,
            'created_at': charity.created_at,
            'updated_at': charity.updated_at,
            'user_id': charity.user_id  # Include the user ID in the response          
 # Include the user ID in the response
        }
        for charity in charity
    ]
    return jsonify({'charity': serialized_charity}), 200

@app.route('/charity/<int:id>', methods=['DELETE'])
def delete_charity(id):
    try:
        # Find the charity record by ID
        charity = Charity.query.get(id)
        
        # Check if the record exists
        if not charity:
            return jsonify({"error": "Charity not found"}), 404

        # Delete the charity record
        db.session.delete(charity)
        db.session.commit()

        return jsonify({"message": "Charity record deleted successfully!"}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# @app.route('/payment', methods=['POST'])
# def add_payment():
#     data = request.json
#     new_payment = Payment(
#         amount=data.get('amount'),
#         email=data['email'],
      
#     )
#     db.session.add(new_payment)
#     db.session.commit()
#     return jsonify({"message": "Payment added successfully"}), 201
# @app.route('/payment', methods=['POST'])
# @jwt_required()
# def add_payment():
#     data = request.json
#     print("Received payment data:", data)  # Debug: Log received data

#     # Retrieve the email of the logged-in user
#     user_email = get_jwt_identity()  # Assuming your JWT identity is set as the user's email
#     print("Authenticated user's email:", user_email)  # Debug: Log user's email

#     # Create a new payment entry with the provided amount and logged-in user's email
#     new_payment = Payment(
#         amount=data.get('amount'),
#         email=user_email,
#     )

#     try:
#         db.session.add(new_payment)
#         db.session.commit()
#         print("Payment added to the database:", new_payment)  # Debug: Log successful DB addition
#         return jsonify({"message": "Payment added successfully"}), 201
#     except Exception as e:
#         db.session.rollback()
#         print("Error adding payment to the database:", e)  # Debug: Log any errors during DB commit
#         return jsonify({"message": "Failed to add payment"}), 500
# from flask_jwt_extended import get_jwt
# def create_token(user):
#     access_token = create_access_token(
#         identity=user.id,  # Keep user ID as the main identity
#         additional_claims={"email": user.email}  # Add email as an additional claim
#     )
#     return access_token
# @app.route('/payment', methods=['POST'])
# @jwt_required()
# def add_payment():
#     data = request.json
#     print("Received payment data:", data)
#     # Retrieve the email from JWT custom claims
#     jwt_data = get_jwt()
#     user_email = jwt_data.get("email")
#     print("Authenticated user's email:", user_email)

#     # Create a new payment entry
#     new_payment = Payment(
#         amount=data.get('amount'),
#         email=user_email,
#     )

#     try:
#         db.session.add(new_payment)
#         db.session.commit()
#         print("Payment added to the database:", new_payment)
#         return jsonify({"message": "Payment added successfully"}), 201
#     except Exception as e:
#         db.session.rollback()
#         print("Error adding payment to the database:", e)
#         return jsonify({"message": "Failed to add payment"}), 500
@app.route('/payment', methods=['POST'])
def handle_payment():
    try:
        data = request.get_json()
        
        # Extract amount and email
        amount = data.get('amount')
        username= data.get('username')
        email = data.get('email')
        
        if not email or not amount or not username:
            return jsonify({"error": "Amount and email are required"}), 400

        print("Received payment data:", data)
        
        # Add to database (adjust this according to your ORM setup)
        payment = Payment(amount=amount, email=email,username=username)
        db.session.add(payment)
        db.session.commit()

        return jsonify({"message": "Payment recorded successfully"}), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error adding payment to the database: {e}")
        return jsonify({"error": "Failed to process payment"}), 500

@app.route('/payment', methods=['GET'])
def get_payment():
    payment = Payment.query.all()
    serialized_payment = [
        {
            'email': payment.email,
            'amount': payment.amount,
            "username":payment.username,
            "created_at":payment.created_at
            
          
        }
        for payment in payment
    ]
    return jsonify({'charity': serialized_payment}), 200
@app.route('/contact', methods=['POST'])
def submit_contact():
    data = request.get_json()

    # Create a new Contact record in the database
    new_contact = Contact(
        first_name=data.get('firstName'),
        last_name=data.get('lastName'),
        email=data.get('email'),
        phonenumber=data.get('phone'),
        description=data.get('message')
    )
    
    db.session.add(new_contact)
    db.session.commit()

    # Send an email notification
    msg = Message(
        'New Contact Message',
        sender=app.config['MAIL_DEFAULT_SENDER'],
        recipients=['prodbysmig@gmail.com']
    )
    msg.body = f"""
    New message from {data.get('firstName')} {data.get('lastName')}:
    
    Email: {data.get('email')}
    Phone: {data.get('phone')}
    
    Message:
    {data.get('message')}
    """
    
    try:
        mail.send(msg)
        return jsonify({'message': 'Message sent successfully'}), 201
    except Exception as e:
        print(f'Error: {e}')  # Print the error message for debugging
        return jsonify({'message': 'Failed to send email. Please try again later.'}), 500

@app.route('/api/contact', methods=['POST'])
def contact():
    data = request.json
    print(data)  # Add this line for debugging
    try:
        msg = Message(
            subject='Contact Form Submission',
            recipients=['prodbysmig@gmail.com'],
            body=f"""
            From: {data['firstName']} {data['lastName']}
            Email: {data['email']}
            Phone: {data['phone']}

            Message:
            {data['message']}
            """,
            sender=app.config['MAIL_DEFAULT_SENDER']  # Use default sender
        )
        mail.send(msg)
        return jsonify({'message': 'Email sent successfully!'}), 200
    except Exception as e:
        print(f'Error: {e}')  # Print the error message for debugging
        return jsonify({'message': 'Failed to send email. Please try again later.'}), 500

@app.route('/test-email', methods=['POST'])
def test_email():
    try:
        msg = Message(
            subject='Test Email',
            recipients=['prodbysmig@gmail.com'],
            body='This is a test email.',
            sender='your-email@gmail.com'
        )
        mail.send(msg)
        return jsonify({'message': 'Test email sent successfully!'}), 200
    except Exception as e:
        print(f'Error: {e}')
        return jsonify({'message': 'Failed to send test email.'}), 500
    
@app.route('/login', methods=['OPTIONS'])
def options():
    response = flask.make_response()
    response.headers['Access-Control-Allow-Origin'] = 'http://localhost:5173'
    response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response
