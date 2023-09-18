from flask import Flask, request, redirect, jsonify
import random
import string
import pymongo

app = Flask(__name__)

# Initialize MongoDB connection (local hosted in this example)
username = ""
password = ""
url = ""
client = pymongo.MongoClient(f"mongodb+srv://{username}:{password}@{url}/")
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

    # Store the mapping in MongoDB
    link_entry = {
        "short_key": short_key,
        "long_url": long_url
    }
    collection.insert_one(link_entry)

    short_url = f'http://127.0.0.1:5000/{short_key}'  # Replace with your actual domain
    return jsonify({'short_url': short_url})

@app.route('/<short_key>')
def redirect_to_original(short_key):
    link_entry = collection.find_one({"short_key": short_key})
    
    if link_entry:
        long_url = link_entry["long_url"]
        return redirect(long_url, code=302)
    
    return jsonify({'error': 'Short URL not found'}), 404

if __name__ == '__main__':
    app.run()
