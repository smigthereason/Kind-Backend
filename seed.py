from faker import Faker
from models import db, User, Donation, Testimonial, AidDistribution, Contact, Charity, Payment
import random

fake = Faker()

def create_users():
    users = []

    # Ensure at least one charity and one donor user
    charity_user = User(
        username=fake.user_name(),
        email=fake.email(),
        password="Password123!",
        user_type='charity',
        phonenumber=fake.phone_number()
    )
    users.append(charity_user)

    donor_user = User(
        username=fake.user_name(),
        email=fake.email(),
        password="Password123!",
        user_type='donor',
        phonenumber=fake.phone_number()
    )
    users.append(donor_user)

    # Create remaining users with random user types
    for _ in range(3):
        user = User(
            username=fake.user_name(),
            email=fake.email(),
            password="Password123!",
            user_type=random.choice(['donor', 'charity', 'admin']),
            phonenumber=fake.phone_number()
        )
        users.append(user)

    db.session.add_all(users)
    db.session.commit()
    return users

def create_donations(users):
    donations = []

    donor_users = [user for user in users if user.user_type == 'donor']
    if not donor_users:
        print("No donors available to create donations.")
        return

    for _ in range(5):
        donation = Donation(
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            email=fake.email(),
            user_id=random.choice(donor_users).id,
            donation_amount=round(random.uniform(10, 500), 2),
            cause_id=fake.uuid4(),
            agree_to_terms=random.choice([True, False]),
            subscribe_monthly=random.choice([True, False]),
            created_at=fake.date_time_this_year()
        )
        donations.append(donation)

    db.session.add_all(donations)
    db.session.commit()

def create_testimonials(users):
    testimonials = []

    for _ in range(3):
        testimonial = Testimonial(
            content=fake.text(),
            user_id=random.choice([user.id for user in users if user.user_type == 'donor'])
        )
        testimonials.append(testimonial)

    db.session.add_all(testimonials)
    db.session.commit()

def create_aid_distributions():
    distributions = []

    for _ in range(3):
        distribution = AidDistribution(
            beneficiary_name=fake.name(),
            amount=round(random.uniform(50, 1000), 2),
            description=fake.text()
        )
        distributions.append(distribution)

    db.session.add_all(distributions)
    db.session.commit()

def create_contacts():
    contacts = []

    for _ in range(3):
        contact = Contact(
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            email=fake.email(),
            phonenumber=fake.phone_number(),
            description=fake.text()
        )
        contacts.append(contact)

    db.session.add_all(contacts)
    db.session.commit()

def create_charities(users):
    charities = []

    charity_users = [user for user in users if user.user_type == 'charity']
    if not charity_users:
        print("No charity users available to create charities.")
        return

    for _ in range(3):
        charity = Charity(
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            image="example.jpg",
            amount=random.randint(100, 1000),
            email=fake.email(),
            document=fake.text(),
            category=fake.word(),
            title=fake.sentence(),
            description=fake.text(),
            user_id=random.choice(charity_users).id
        )
        charities.append(charity)

    db.session.add_all(charities)
    db.session.commit()

def create_payments():
    payments = []

    for _ in range(3):
        payment = Payment(
            amount=random.randint(10, 500),
            email=fake.email(),
            username=fake.last_name(),
        )
        payments.append(payment)

    db.session.add_all(payments)
    db.session.commit()

def seed_database():
    print("Seeding users...")
    users = create_users()

    print("Seeding donations...")
    create_donations(users)

    print("Seeding testimonials...")
    create_testimonials(users)

    print("Seeding aid distributions...")
    create_aid_distributions()

    print("Seeding contacts...")
    create_contacts()

    print("Seeding charities...")
    create_charities(users)

    print("Seeding payments...")
    create_payments()

if __name__ == "__main__":
    from app import app
    with app.app_context():
        db.drop_all()
        db.create_all()
        seed_database()
