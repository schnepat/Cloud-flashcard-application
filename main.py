from flask import Flask, request, jsonify, render_template
from google.cloud import firestore
from google.cloud import aiplatform
from google.cloud import storage
# note that the vertex ai library below is using a preview 
from vertexai.preview.generative_models import GenerativeModel
import os
import datetime
import uuid

app = Flask(__name__)

# Initialize Firestore client
db = firestore.Client()

# Initialize Cloud Storage client
storage_client = storage.Client()
bucket_name = os.environ.get('CLOUD_STORAGE_BUCKET')
bucket = storage_client.bucket(bucket_name)

# Initialize Vertex AI
aiplatform.init(
    project=os.environ.get('GOOGLE_CLOUD_PROJECT'),
    location='us-central1'
)

# Gemini model setup
model = GenerativeModel('gemini-pro')

# Routes for Deck CRUD operations (Still needs edit deck name functionality)
@app.route('/api/decks', methods=['GET'])
def get_decks():
    decks_ref = db.collection('decks')
    decks = [doc.to_dict() for doc in decks_ref.stream()]
    
    return jsonify(decks)

@app.route('/api/decks', methods=['POST'])
def create_deck():
    data = request.get_json()
    
    # Validate input
    if 'name' not in data:
        return jsonify({'error': 'Deck name is required'}), 400
    
    deck_id = str(uuid.uuid4())
    timestamp = datetime.datetime.now()
    
    deck = {
        'id': deck_id,
        'name': data['name'],
        'description': data.get('description', ''),
        'created_at': timestamp,
        'updated_at': timestamp
    }
    
    # Save to Firestore
    db.collection('decks').document(deck_id).set(deck)
    
    return jsonify(deck), 201

@app.route('/api/decks/<deck_id>', methods=['PUT'])
def update_deck(deck_id):
    data = request.get_json()
    
    # Get existing deck
    deck_ref = db.collection('decks').document(deck_id)
    deck = deck_ref.get()
    
    if not deck.exists:
        return jsonify({'error': 'Deck not found'}), 404
    
    # Update fields
    updates = {
        'updated_at': datetime.datetime.now()
    }
    
    for field in ['name', 'description']:
        if field in data:
            updates[field] = data[field]
    
    # Update in Firestore
    deck_ref.update(updates)
    
    # Return updated deck
    updated = deck_ref.get().to_dict()
    return jsonify(updated)

@app.route('/api/decks/<deck_id>', methods=['DELETE'])
def delete_deck(deck_id):
    # Delete from Firestore
    deck_ref = db.collection('decks').document(deck_id)
    if not deck_ref.get().exists:
        return jsonify({'error': 'Deck not found'}), 404
    
    # Delete all flashcards in the deck
    flashcards_ref = db.collection('flashcards').where('deck_id', '==', deck_id)
    for doc in flashcards_ref.stream():
        flashcard_data = doc.to_dict()
        
        # Delete image from Cloud Storage if it exists
        if 'image_url' in flashcard_data and flashcard_data['image_url']:
            try:
                # Extract image filename from URL
                filename = flashcard_data['image_url'].split('/')[-1]
                blob = bucket.blob(f"flashcard-images/{filename}")
                blob.delete()
            except Exception as e:
                print(f"Error deleting image: {e}")
        
        # Delete flashcard document
        doc.reference.delete()
    
    # Delete the deck
    deck_ref.delete()
    
    return jsonify({'message': 'Deck and all its flashcards deleted successfully'})

# Routes for CRUD operations on flashcards
@app.route('/api/flashcards', methods=['GET'])
def get_flashcards():
    deck_id = request.args.get('deck_id')
    
    if deck_id:
        # Get flashcards for a specific deck
        flashcards_ref = db.collection('flashcards').where('deck_id', '==', deck_id)
    else:
        # Get all flashcards
        flashcards_ref = db.collection('flashcards')
    
    flashcards = [doc.to_dict() for doc in flashcards_ref.stream()]
    
    return jsonify(flashcards)

@app.route('/api/flashcards', methods=['POST'])
def create_flashcard():
    data = request.get_json()
    
    # Validate input
    if not all(k in data for k in ('question', 'answer', 'deck_id')):
        return jsonify({'error': 'Missing required fields (question, answer, deck_id)'}), 400
    
    # Check if deck exists
    deck_ref = db.collection('decks').document(data['deck_id'])
    if not deck_ref.get().exists:
        return jsonify({'error': 'Deck not found'}), 404
    
    flashcard_id = str(uuid.uuid4())
    timestamp = datetime.datetime.now()
    
    # Flashcard structure - possible spot to add fields for AI to generate new flashcards or ML to tailor a smart review 
    flashcard = {
        'id': flashcard_id,
        'deck_id': data['deck_id'],
        'question': data['question'],
        'answer': data['answer'],
        'created_at': timestamp,
        'updated_at': timestamp,
        'tags': data.get('tags', [])
    }
    
    # Add image URL if provided
    if 'image_url' in data and data['image_url']:
        flashcard['image_url'] = data['image_url']
    
    # Save to Firestore
    db.collection('flashcards').document(flashcard_id).set(flashcard)
    
    return jsonify(flashcard), 201

@app.route('/api/flashcards/<flashcard_id>', methods=['PUT'])
def update_flashcard(flashcard_id):
    data = request.get_json()
    
    # Get existing flashcard
    flashcard_ref = db.collection('flashcards').document(flashcard_id)
    flashcard = flashcard_ref.get()
    
    if not flashcard.exists:
        return jsonify({'error': 'Flashcard not found'}), 404
    
    # Update fields
    updates = {
        'updated_at': datetime.datetime.now()
    }
    
    for field in ['question', 'answer', 'tags', 'image_url']:
        if field in data:
            updates[field] = data[field]
    
    # Update in Firestore
    flashcard_ref.update(updates)
    
    # Return updated flashcard
    updated = flashcard_ref.get().to_dict()
    return jsonify(updated)

@app.route('/api/flashcards/<flashcard_id>', methods=['DELETE'])
def delete_flashcard(flashcard_id):
    # Get flashcard reference
    flashcard_ref = db.collection('flashcards').document(flashcard_id)
    flashcard = flashcard_ref.get()
    
    if not flashcard.exists:
        return jsonify({'error': 'Flashcard not found'}), 404
    
    # Check if flashcard has an image to delete
    flashcard_data = flashcard.to_dict()
    if 'image_url' in flashcard_data and flashcard_data['image_url']:
        try:
            # Extract image filename from URL
            filename = flashcard_data['image_url'].split('/')[-1]
            blob = bucket.blob(f"flashcard-images/{filename}")
            blob.delete()
        except Exception as e:
            print(f"Error deleting image: {e}")
    
    # Delete flashcard document
    flashcard_ref.delete()
    
    return jsonify({'message': 'Flashcard deleted successfully'})

# Image upload endpoint
@app.route('/api/upload-image', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No image selected'}), 400
    
    # Check file type
    allowed_extensions = {'jpg', 'jpeg', 'png', 'gif'}
    file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if file_extension not in allowed_extensions:
        return jsonify({'error': 'Invalid file type. Only jpg, jpeg, png, and gif files are allowed.'}), 400
    
    # Create unique filename
    new_filename = f"{str(uuid.uuid4())}.{file_extension}"
    
    # Upload to Cloud Storage
    blob = bucket.blob(f"flashcard-images/{new_filename}")
    blob.upload_from_file(file)
    
    # Make the image publicly accessible
    blob.make_public()
    image_url = blob.public_url
    
    return jsonify({
        'image_url': image_url
    })

# Gemini AI integration for generating answers to flashcard questions
@app.route('/api/generate-answer', methods=['POST'])
def generate_answer():
    data = request.get_json()
    question = data.get('question')
    
    if not question:
        return jsonify({'error': 'Question is required'}), 400
    
    try:
        # Query Gemini
        prompt = f"""
        Question: {question}
        
        Please provide a comprehensive and accurate answer to this question. 
        Include key facts and concepts that would be useful in a learning context.
        Your answer can include formatting such as bullet points, numbered lists, 
        or paragraphs if that helps organize the information better.
        """
        
        response = model.generate_content(prompt)
        ai_answer = response.text
        
        # this is an optional log for the ai answers
        # db.collection('ai_answers').add({
        #        
        #         'question': question,
        #         'ai_answer': ai_answer,
        #         'timestamp': datetime.datetime.now()
        #     })
        
        return jsonify({
            'question': question,
            'answer': ai_answer
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Frontend routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/deck/<deck_id>')
def deck_view(deck_id):
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=True)
