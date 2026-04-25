from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
import time
import random
from datetime import datetime
import csv
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

DATA_FILE = 'users.json'

def read_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def write_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

CSV_FILE = 'users.csv'

def write_csv(db):
    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Name', 'Age', 'Hobbies', 'Favorites', 'Skills', 'SuccessMetric', 'CreatedAt', 'UpdatedAt'])
        for user_id, data in db.items():
            writer.writerow([
                data.get('id', ''),
                data.get('name', ''),
                data.get('age', ''),
                ', '.join(data.get('hobbies', [])) if isinstance(data.get('hobbies'), list) else data.get('hobbies', ''),
                data.get('favorites', ''),
                ', '.join(data.get('skills', [])) if isinstance(data.get('skills'), list) else data.get('skills', ''),
                data.get('successMetric', ''),
                data.get('createdAt', ''),
                data.get('updatedAt', '')
            ])

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    if os.path.exists(path):
        return send_from_directory('.', path)
    elif os.path.exists(path + '.html'):
        return send_from_directory('.', path + '.html')
    return "Not found", 404

@app.route('/api/onboarding/step1', methods=['POST'])
def step1():
    data = request.json or {}
    name = data.get('name')
    age = data.get('age')
    hobbies = data.get('hobbies', [])
    favorites = data.get('favorites')

    user_id = f"user_{int(time.time())}{random.randint(100, 999)}"
    
    db = read_data()
    db[user_id] = {
        'id': user_id,
        'name': name,
        'age': age,
        'hobbies': hobbies,
        'favorites': favorites,
        'createdAt': datetime.utcnow().isoformat() + "Z"
    }
    
    write_data(db)
    write_csv(db)
    return jsonify({"success": True, "userId": user_id, "user": db[user_id]})

@app.route('/api/onboarding/step2', methods=['POST'])
def step2():
    data = request.json or {}
    user_id = data.get('userId')
    goals = data.get('goals')
    skills = data.get('skills', [])
    success_metric = data.get('successMetric')

    if goals:
        skills.append(goals)

    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
        
    db = read_data()
    if user_id not in db:
        return jsonify({"error": "User not found"}), 404
        
    db[user_id]['skills'] = skills
    db[user_id]['successMetric'] = success_metric
    db[user_id]['updatedAt'] = datetime.utcnow().isoformat() + "Z"
    
    write_data(db)
    write_csv(db)
    return jsonify({"success": True, "user": db[user_id]})

@app.route('/api/roadmap/<user_id>', methods=['GET'])
def generate_roadmap(user_id):
    db = read_data()
    if user_id not in db:
        return jsonify({"error": "User not found"}), 404
    
    user = db[user_id]
    skills = ", ".join(user.get('skills', [])) if isinstance(user.get('skills'), list) else user.get('skills', '')
    goal = user.get('successMetric', '')
    
    # If the user has already generated a roadmap, we could return it, but here we generate a fresh one
    prompt = f"""
    You are an expert learning coach. The user wants to learn: {skills}.
    Their success metric is: {goal}.
    
    Create a professional, highly-structured learning curriculum divided into three expertise sections: Beginner, Advanced, and Expert.
    Focus purely on the technical/skill progression required to reach the goal.
    
    For each section, provide:
    1. A clear, professional title and a summary description of what will be mastered.
    2. A list of specific 'topics'.
    3. Each topic should have multiple 'sub_topics'.
    4. Each sub_topic should have a 'status' (initialize all as 'Not Started').
    
    Return ONLY a valid JSON object with this exact structure:
    {{
        "beginner": {{
            "title": "...",
            "description": "...",
            "topics": [
                {{
                    "title": "Topic Name",
                    "sub_topics": [
                        {{ "title": "Sub-topic Name", "status": "Not Started" }}
                    ]
                }}
            ]
        }},
        "advanced": {{ ... same structure ... }},
        "expert": {{ ... same structure ... }}
    }}
    """
    
    try:
        model = genai.GenerativeModel('gemini-flash-latest')
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:-3].strip()
        elif text.startswith("```"):
            text = text[3:-3].strip()
            
        roadmap = json.loads(text)
        
        # Save to db
        db[user_id]['roadmap'] = roadmap
        write_data(db)
        
        return jsonify({"success": True, "roadmap": roadmap})
    except Exception as e:
        print("Error generating roadmap:", str(e))
        return jsonify({"error": "Failed to generate roadmap. Did you set GEMINI_API_KEY?"}), 500

@app.route('/api/   ', methods=['POST'])
def concept_explainer_metaphor_engine():
    data = request.json or {}
    user_id = data.get('userId')
    topic = data.get('topic')
    is_alternative = data.get('isAlternative', False)
    
    if not user_id or not topic:
        return jsonify({"error": "User ID and Topic are required"}), 400
        
    db = read_data()
    if user_id not in db:
        return jsonify({"error": "User not found"}), 404
        
    user = db[user_id]
    hobbies = ", ".join(user.get('hobbies', [])) if isinstance(user.get('hobbies'), list) else user.get('hobbies', '')
    favorites = user.get('favorites', '')
    age = user.get('age', '')
    goal = user.get('successMetric', '')

    if is_alternative:
        prompt = f"""
        The user didn't quite understand the first explanation of '{topic}'. 
        Try a DIFFERENT central metaphor related to their hobbies ({hobbies}).
        
        Since this is a multimodal follow-up:
        1. Provide a new, even simpler explanation.
        2. Describe a highly effective visual or diagram that would explain this concept using the metaphor.
        
        User Context: Age {age}, Hobbies {hobbies}, Goal {goal}.
        
        Return ONLY a JSON object:
        {{
            "title": "A Different Look at ...",
            "explanation": "...",
            "takeaway": "...",
            "visual_prompt": "A detailed descriptive prompt for an AI image generator to create a visual for this metaphor. Be specific and artistic."
        }}
        """
    else:
        prompt = f"""
        Act as a brilliant and creative teacher. Explain the following concept: '{topic}'.
        
        User Context:
        - Age: {age}
        - Hobbies/Interests: {hobbies}
        - Favorite things: {favorites}
        - Learning Goal: {goal}
        
        CRITICAL INSTRUCTION:
        Use a central metaphor or series of similes directly related to the user's hobbies ({hobbies}) to explain the concept. 
        Avoid technical jargon unless you explain it through the metaphor.
        Make it engaging, encouraging, and easy to understand for someone their age.
        
        Structure your response with:
        1. A 'title' (a creative name for this lesson).
        2. The 'explanation' (the core content with metaphors).
        3. A 'takeaway' (one key sentence to remember).
        
        Return ONLY a valid JSON object with these keys: "title", "explanation", "takeaway".
        """
    
    try:
        model = genai.GenerativeModel('gemini-flash-latest')
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Clean up JSON formatting
        if text.startswith("```json"):
            text = text[7:-3].strip()
        elif text.startswith("```"):
            text = text[3:-3].strip()
            
        explanation_data = json.loads(text)
        
        # If alternative, generate a multimodal image URL
        if is_alternative and "visual_prompt" in explanation_data:
            # Use a public AI image generation placeholder for "multimodal" effect
            encoded_prompt = explanation_data["visual_prompt"].replace(" ", "%20")
            explanation_data["image_url"] = f"https://pollinations.ai/p/{encoded_prompt}?width=1080&height=720&seed={random.randint(1,1000)}"
            
        return jsonify({"success": True, "explanation": explanation_data})
    except Exception as e:
        print("Error in metaphor engine:", str(e))
        return jsonify({"error": "The Metaphor Engine is momentarily stalled. Check your API key."}), 500

@app.route('/api/user/<user_id>', methods=['GET'])
def get_user(user_id):
    db = read_data()
    if user_id not in db:
        return jsonify({"error": "User not found"}), 404
        
    return jsonify({"success": True, "user": db[user_id]})

if __name__ == '__main__':
    # Cloud Run provides the PORT environment variable
    port = int(os.environ.get("PORT", 3000))
    print(f"Backend server running at http://localhost:{port}")
    app.run(host='0.0.0.0', port=port)
