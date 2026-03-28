from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

class GeminiInterpreter:
    def __init__(self):
        # API Key checking and client initialization
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set! Please check your .env file.")
            
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-1.5-flash"

    def generate_standard_report(self, chart_data: list, profile_name: str):
        # legend: chart_data is a list of dicts with keys: name, sign, degree_in_sign
        data_summary = "\n".join([
            f"- {p['name']}: {p['sign']} ({p['degree_in_sign']} degrees)" 
            for p in chart_data
        ])

        # Prompt Engineering: we want a structured, insightful report. The prompt should guide the model to produce the desired output.
        prompt = f"""
        You are a professional, analytical psychological astrologer.
        Profile Name: {profile_name}
        Birth Chart Data:
        {data_summary}

        Please provide a detailed birth chart analysis in the following structure:
        1. **Identity & Core Personality**: Focus on the Sun and Moon.
        2. **Communication & Intellect**: Focus on Mercury.
        3. **Drive & Energy**: Focus on Mars.
        4. **Summary**: A professional conclusion about the native's potential.

        Use a serious and insightful tone. Avoid spiritual clichés.
        """

        try:
            # we can also experiment with different parameters like temperature for more creativity or top_p for more focused responses
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )
            return response.text
        except Exception as e:
            # log the error for debugging purposes, but return a user-friendly message
            print(f"Logging Error: {str(e)}") 
            return f"An error occurred while generating the report."