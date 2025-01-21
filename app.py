from flask import Flask, request, jsonify, render_template, session
from dotenv import load_dotenv
import os
import google.generativeai as genai
from werkzeug.utils import secure_filename
import PyPDF2
import requests
from dotenv import load_dotenv

# Load environment variables from app.env file
load_dotenv(dotenv_path='app.env')

# Initialize the Flask app
app = Flask(__name__)

# Set a secret key for session management (needed for Flask session storage)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key')  # Ensure you have a secret key in your .env

# Set Gemini API key from environment variable
api_key = os.getenv('GEMINI_API_KEY')  # Make sure your app.env has GEMINI_API_KEY

# Configure Gemini API
genai.configure(api_key=api_key)

# File upload settings
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'png', 'jpg', 'jpeg', 'txt'}

# Check allowed file extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Route for rendering the HTML page
@app.route('/')
def index():
    return render_template('chat.html')

# Function to assign emojis based on message content
def assign_emoji_based_on_content(text):
    if "fun" in text.lower() or "cake" in text.lower():
        return "🍰"  # For fun or food-related content
    elif "help" in text.lower() or "question" in text.lower():
        return "❓"  # For help or question-related content
    elif "serious" in text.lower() or "important" in text.lower():
        return "🧐"  # For serious content
    elif "thank" in text.lower() or "thanks" in text.lower():
        return "🙏"  # For gratitude
    elif "file" in text.lower() or "upload" in text.lower():
        return "📁"  # For file uploads
    else:
        return "💬"  # Default message emoji


@app.route('/get', methods=['POST'])
def get_bot_response():
    user_message = request.form['msg']


    # List of possible questions asking for the bot's name
    name_queries = [
        "what is your name", "who are you", "tell me your name", 
        "what should I call you", "who are you talking to", 
        "can you introduce yourself", "what's your name", "who is this"
    ]
    
    # Check if the user asks for the bot's name in any form
    if any(query in user_message.lower() for query in name_queries):
        return jsonify({'response': "My name is Bobdx!"})

    # Check if the user asks about the bot's creator
    creator_queries = [
        "who created you", "who made you", "who is the creator of this bot", 
        "who built you", "who developed you", "who is your creator", "who is your owner"
    ]
    
    if any(query in user_message.lower() for query in creator_queries):
        return jsonify({'response': "I was created by Emaan Fatima!"})

    file = request.files.get('file')

    # Initialize session memory if not already set
    if 'conversation_memory' not in session:
        session['conversation_memory'] = []

    # Process the file if uploaded
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Check the file type and process it
        if filename.endswith('.pdf'):
            # Extract text from PDF using PyPDF2
            with open(file_path, 'rb') as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)
                text = ''
                for page in reader.pages:
                    text += page.extract_text()
            file_content = text.strip() if text else "No readable text found."
        else:
            # Handle other file types (e.g., images, text)
            file_content = f"File {filename} uploaded successfully. It is a {file.filename.split('.')[-1]} file."

        # Store the file upload content in session memory
        session['conversation_memory'].append({'user_message': f"File uploaded: {file_content}", 'bot_response': file_content})

        # Respond with the extracted or file-related content
        return jsonify({'response': file_content})

    # If no file is uploaded, proceed to generate response using Gemini API
    if user_message:
        try:
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(user_message)

            # Extract and return the bot's response
            bot_message = response.text.strip()

            # Assign an emoji based on the content
            emoji = assign_emoji_based_on_content(bot_message)

            # Format the response (HTML/Markdown formatting)
            bot_message = bot_message.replace("\n", "<br>")
            bot_message = bot_message.replace("**", "<b>").replace("**", "</b>")  # Bold formatting
            bot_message = bot_message.replace("*", "<i>").replace("*", "</i>")  # Italics formatting
            bot_message = f"{emoji} {bot_message}"  # Add emoji prefix

            # Store the user message and bot response in session memory
            session['conversation_memory'].append({'user_message': user_message, 'bot_response': bot_message})

            return jsonify({'response': bot_message})
        except Exception as e:
            return jsonify({'response': f"An error occurred: {str(e)}"})

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
