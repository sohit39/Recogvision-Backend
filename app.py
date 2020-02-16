# app.py

# Required imports
import os
from flask import Flask, request, jsonify
from firebase_admin import credentials, firestore, initialize_app
import face_recognition
import base64
from PIL import Image
from io import BytesIO

# Initialize Flask app
app = Flask(__name__)

# Initialize Firestore DB
cred = credentials.Certificate('key.json')
default_app = initialize_app(cred)
db = firestore.client()
people_ref = db.collection('PEOPLE')

@app.route('/add', methods=['POST'])
def create():
    """
        create() : Add document to Firestore collection with request body.
        Ensure you pass a custom ID as part of json body in post request,
        e.g. json={'name': 'Bob', 'description': 'i am 25'}
    """
    try:
        id = request.json['name']
        people_ref.document(id).set(request.json)
        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/list', methods=['GET'])
def read():
    """
        read() : Fetches documents from Firestore collection as JSON.
        todo : Return document that matches query ID.
        all_todos : Return all documents.
    """
    try:
        # Check if ID was passed to URL query
        todo_id = request.args.get('id')
        if todo_id:
            todo = people_ref.document(todo_id).get()
            return jsonify(todo.to_dict()), 200
        else:
            all_todos = [doc.to_dict() for doc in people_ref.stream()]
            return jsonify(all_todos), 200
    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/update', methods=['POST', 'PUT'])
def update():
    """
        update() : Update document in Firestore collection with request body.
        Ensure you pass a custom ID as part of json body in post request,
        e.g. json={'id': '1', 'title': 'Write a blog post today'}
    """
    try:
        id = request.json['name']
        people_ref.document(id).update(request.json)
        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/delete', methods=['GET', 'DELETE'])
def delete():
    """
        delete() : Delete a document from Firestore collection.
    """
    try:
        # Check for ID in URL query
        todo_id = request.args.get('id')
        people_ref.document(todo_id).delete()
        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/match', methods=['POST'])
def match():
    try:
        img_string = request.json['base64']
        img_data = base64.b64decode(img_string)
        filename = 'unknown.jpg'
        with open(filename, 'wb') as f:
            f.write(img_data)
        unknown_image = face_recognition.load_image_file(filename)

        known_images = []
        for person in people_ref.stream():
            img_data = base64.b64decode(person['base64'])
            filename = person['name'] + '.jpg'
            with open(filename, 'wb') as f:
                f.write(img_data)
            known_images.append(face_recognition.load_image_file(filename))

        known_encodings = []
        try:
            for image in known_images:
                known_encodings.append(face_recognition.face_encodings(image)[0])
            unknown_encoding = face_recognition.face_encodings(unknown_image)[0]
        except IndexError:
            print("I wasn't able to locate any faces in at least one of the images. Check the image files. Aborting...")
            quit()

        results = face_recognition.compare_faces(known_encodings, unknown_encoding)
        i = 0
        for r in results:
            if r == True:
                return jsonify({"name": get_known_faces()[i][:-4]}), 200
            i += 1
        if True not in results:
            return jsonify({"name": "Unknown"}), 200

    except Exception as e:
        return f"An Error Occurred: {e}"

port = int(os.environ.get('PORT', 8080))
if __name__ == '__main__':
    app.run(threaded=True, host='0.0.0.0', port=port)