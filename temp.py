from flask import Flask, request, redirect, jsonify, render_template, session, url_for
import random
import string
import pymongo
import os

app = Flask(__name__, static_folder='static')
app.secret_key = os.environ['secret_key']

# Initialize MongoDB connection (local hosted in this example)
username = os.environ['username']
password = os.environ['password']
url = os.environ['url']
client = pymongo.MongoClient(f"mongodb+srv://{username}:{password}@{url}/")
db = client["link_shortener"]
collection = db["links"]

def authenticate(username, password):
    # Replace with your own username and password
    valid_username = os.environ['dashboard-username']
    valid_password = os.environ['dashboard-password']
    return username == valid_username and password == valid_password

def generate_short_key():
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(6))

@app.route('/shorten', methods=['POST'])
def shorten_url():
    data = request.get_json()
    long_url = data.get('long_url')
    
    if not long_url:
        return jsonify({'error': 'Invalid input'}), 400

    short_key = generate_short_key()

    # Store the mapping in MongoDB with initial visit count and empty IP log array
    link_entry = {
        "short_key": short_key,
        "long_url": long_url,
        "visit_count": 0,
        "ip_log": []
    }
    collection.insert_one(link_entry)

    short_url = f'https://link-shortner.mochirondesu.repl.co/{short_key}'  # Replace with your actual domain
    return jsonify({'short_url': short_url})

@app.route('/<short_key>')
def redirect_to_original(short_key):
    link_entry = collection.find_one({"short_key": short_key})
    
    if link_entry:
        long_url = link_entry["long_url"]
        
        # Increment visit count and log IP
        link_entry["visit_count"] += 1
        link_entry["ip_log"].append(request.remote_addr)
        collection.update_one({"short_key": short_key}, {"$set": link_entry})
        
        return redirect(long_url, code=302)
    
    return jsonify({'error': 'Short URL not found'}), 404

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if authenticate(username, password):
            session['authenticated'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error='Invalid credentials')
    return render_template('admin_login.html', error=None)

@app.route('/admin')
def admin_dashboard():
    if not session.get('authenticated'):
        return redirect(url_for('admin_login'))
    # Fetch all shortened URLs with visit counts and IP logs
    all_links = list(collection.find({}, {"_id": 0}))
    return render_template('admin.html', links=all_links)

@app.route('/admin/logout')
def admin_logout():
    session.pop('authenticated', None)
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
