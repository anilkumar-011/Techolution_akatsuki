from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from pymongo import MongoClient

from eye_tracker import eye_tracker_func
from ATT import transcribe
from scrappers import activate_scrappers

app = Flask(__name__)
CORS(app)

upload_folder = "D://Hackathon//github//Techolution_akatsuki//backend//uploaded_files"
app.config['UPLOAD_FOLDER'] = upload_folder

# MongoDB connection
mongo_uri = "mongodb+srv://Admin:Password@cluster0.qyexdxz.mongodb.net/"  # Replace with your MongoDB connection string
# Connect to MongoDB using the connection string
client = MongoClient(mongo_uri)
db = client["Results"]



def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg', 'png'}

@app.route('/signup', methods=['POST'])
def signup():
    print("----------entered-------------")
    data = request.json
    if data:
        # Create a user object
        user = {
            "name": data.get('name'),
            "email": data.get('email'),
            "password": data.get('password'),
            "qualification": data.get('qualification'),
            "github": data.get('github'),
            "linkedin": data.get('linkedin'),
            "leetcode": data.get('leetcode'),
            "user_details" : True
        }

        print(user)

        user_collection = db[user.get("name")]
        # Insert the user object into the database
        user_id = user_collection.insert_one(user).inserted_id
        return jsonify({"message": f"User registered with ID: {user_id}"}), 201
    else:
        return jsonify({"error": "Invalid data"}), 400
    

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        # username = request.get('username')
        # print(username)
        if 'video' not in request.files:
            print("file not returned")
            return "No file part"

        file = request.files['video']

        if file.filename == '':
            return "No selected file"

        file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
        print("File saved as:", os.path.join(app.config['UPLOAD_FOLDER'], file.filename))

        #  Assuming you have 'app' and 'file' defined earlier
        uploaded_file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename).replace('/', '\\')

        # Extract the last part of the file path (the file name)
        file_name = os.path.basename(uploaded_file_path)

        # Split the file name using the underscore character
        name_parts = file_name.split('_')
        name_parts[-1] = name_parts[-1].split('.')[0]

        eye_contact_time = eye_tracker_func(uploaded_file_path)
        print("eye_contact_time :",eye_contact_time)

        score = transcribe(uploaded_file_path)
        print("Jd_score", score)

        github_link = "https://github.com/PavanSETTEM-003"
        leetcode_link = "https://leetcode.com/2010040084__pavan/"
        stats = activate_scrappers(github_link, leetcode_link)
        print("stats :",stats)

        db = client["utils"]
        collections = db['job_description']

        data ={
            "job_d" : name_parts[-1],
            "username" : name_parts[0],
            'company': collections.find_one({"id": name_parts[-1]}).get("company"),
            "results": True,
            "eye_contact_time": eye_contact_time,
            "Jd_score": score,
            'leetcode': {
                'problem_sloved': stats[-2],
                'active days': stats[-1],
            },
            'github': {
                'username': stats[0],
                'contributions': stats[1],
            },
        }

        print(data)

        # collection = db[name_parts[0]]
        # user_id = db[name_parts[0]].insert_one(data)
        # return jsonify({"message": f"User registered with ID: {user_id}"}), 201

        db[name_parts[0]].insert_one(data)
        return jsonify(data)
    
    except Exception as error:
        print(error)
    
    return "unsucessful please reach again"


@app.route('/get_user_results', methods=['GET'])
def get_user_data():
    collection = db["user_1"]
    # Retrieve all entries from the collection
    user_data = list(collection.find({}))

    # Convert MongoDB documents to a JSON response
    response = jsonify(user_data)
    
    # Optionally, you can set the response's content type to JSON
    response.headers['Content-Type'] = 'application/json'
    print(response)
    
    return jsonify(response)

@app.route('/get_jd', methods=['GET'])
def get_data():
    # Query the collection to retrieve all documents
    db = client["utils"]
    collections = db['job_description']
    all_documents = collections.find()
    
    # Convert the cursor to a list of dictionaries
    document_list = list(all_documents)
    
    # Return the list of dictionaries as JSON
    return jsonify(document_list)

if __name__ == '__main__':
    app.run(debug=True, port=8000)