from dotenv import load_dotenv
import google.generativeai as genai
import os

# Firebase configuration
FIREBASE_DATABASE_URL = "https://data-retech-80d38-default-rtdb.asia-southeast1.firebasedatabase.app/"

load_dotenv()

api_key = os.getenv('GEMINI_API_KEY')
print(f"API Key found: {'Yes' if api_key else 'No'}")

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content('Hello!')
    print("Test response:", response.text)
    print("API is working correctly!")
except Exception as e:
    print("Error:", str(e))
