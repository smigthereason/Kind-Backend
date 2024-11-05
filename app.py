from flask import Flask
from flask_mail import Mail, Message
from flask_migrate import Migrate
from models import db
from config import Config
from flask_cors import CORS
import os

app = Flask(__name__)


app.config.from_object(Config)

# Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'your-email@gmail.com'  # Your email address
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_DEFAULT_SENDER'] = 'victor.dmaina@gmail.com'  # Updated sender address

mail = Mail(app)

db.init_app(app)
migrate = Migrate(app, db)

CORS(app, supports_credentials=True, origins=["http://localhost:5173"])
CORS(app, resources={r"/api/*": {"origins": "*"}})
CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": "http://localhost:5173"}})
CORS(app, resources={r"/charity": {"origins": "http://localhost:5173"}})
 

from routes import *

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
