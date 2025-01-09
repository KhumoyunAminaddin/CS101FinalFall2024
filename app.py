from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import google.auth
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from authlib.integrations.flask_client import OAuth
from functools import wraps


app = Flask(__name__)

# Google Sheets configuration
FORM_LINKS_SHEET_ID = '10vbil8nZ9r5Bc7_C6P_SURtpJUKwWbZ0DJBw8htVe9A'
STUDENT_LIST_SHEET_ID = '1n1NuVGxO4J3Ek2XGnVvyFArXvzW_FjsicBHhz8oCUXQ'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SERVICE_ACCOUNT_FILE = 'config.json'

credentials = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
service = build('sheets', 'v4', credentials=credentials)

app.secret_key = 'f9b12a0e4d8f1e3728c63474d4cba213'
app.config['GOOGLE_ID'] = '125277176981-ircgal3rl11munr9kr3vbfc3hst9vmu5.apps.googleusercontent.com'
app.config['GOOGLE_SECRET'] = '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'

oauth = OAuth(app)

google = oauth.register(
    name='google',
    client_id='125277176981-ircgal3rl11munr9kr3vbfc3hst9vmu5.apps.googleusercontent.com',
    client_secret='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',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
    api_base_url='https://www.googleapis.com/oauth2/v1/'  # Correct base URL
)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'email' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def home():
    return 'Welcome! <a href="/login">Login with Google</a>'


@app.route('/login')
def login():
    redirect_uri = url_for('authorized', _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route('/login/authorized')
def authorized():
    # Fetch the access token
    token = google.authorize_access_token()
    # Fetch user information using the correct API base URL
    user_info = google.get('userinfo').json()
    examdata = get_student_info(user_info['email'])
    session['email'] = user_info['email']  # Save email in session
    session['form_url'] = examdata['form_url']
    session['partIILink'] = examdata['part_ii_link']
    session['student_name'] = examdata['student_name']

    return redirect(url_for('protected'))


@app.route('/logout')
def logout():
    session.pop('email', None)
    session.pop('form_url', None)
    session.pop('partIILink', None)
    session.pop('student_name', None)
    return redirect(url_for('home'))


@app.route('/protected')
@login_required
def protected():
    email = session.get('email')
    if not email:
        return redirect(url_for('login'))
    return render_template('index.html',
                           form_url=session['form_url'],
                           partIILink=session['partIILink'],
                           student_name=session['student_name'])


def get_student_info(email):
    sheet = service.spreadsheets()
    students_data = sheet.values().get(
        spreadsheetId=STUDENT_LIST_SHEET_ID,
        range='Students'
    ).execute().get('values', [])

    for row in students_data[1:]:
        if str(row[2]) == str(email):
            return {
                "id": row[0],
                "form_url": row[3],
                "part_ii_link": row[5],
                "student_name": row[1]
            }
    return None


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
