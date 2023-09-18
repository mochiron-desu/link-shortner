from flask import Flask, request, redirect, jsonify, render_template
import random
import string
import pymongo

app = Flask(__name__, static_folder='static')

# Initialize MongoDB connection (local hosted in this example)
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["link_shortener"]
collection = db["links"]

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

    short_url = f'http://127.0.0.1:5000/{short_key}'  # Replace with your actual domain
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

if __name__ == '__main__':
    app.run()