✦ AstroLogic: Celestial Insights with AI
A modern, full-stack Astrology application that combines ancient wisdom with modern Artificial Intelligence. This project provides personalized birth chart interpretations,
planetary positions, and an AI-driven chat interface to explore your cosmic blueprint.

🚀 Key Features
Birth Chart Generation: Precise calculation of planetary positions and aspects.

AI Interpretations: Detailed natal report generation using Google Gemini-2.5-flash-lite.

Smart Caching: Optimized backend that stores previous analyses to save API quotas and reduce latency.

Interactive AI Chat: A specialized chat interface to ask specific questions about your birth chart.

Secure Authentication: JWT-based user login and profile management system.

Responsive Mistik UI: A unique, dark-themed interface designed with a focus on "Celestial Aesthetics."

Frontend:  Vanilla JavaScript (ES6+ Modules), Custom CSS3 (Celestial UI components), HTML5

Backend: FastAPI (Python), SQLAlchemy (Database ORM), Google Gemini API (Generative AI), Pydantic (Data validation)

------------------------------------------------------
Backend Setup 
# Navigate to backend folder
cd backend

# Create a virtual environment
python3 -m venv venv_linux
source venv_linux/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up your .env file
echo "GEMINI_API_KEY=your_key_here" > .env
POSTGRES_USER
POSTGRES_PASSWORD
POSTGRES_DB
DATABASE_URL
GEMINI_API_KEY
SECRET_KEY

# Run the server
uvicorn main:app --reload
------------------------------------------------------
Frontend Setup
Since the frontend uses ES6 Modules, it must be served via a web server (not just opening the file).

# From the root directory (venus/)
python3 -m http.server 5500

<img width="619" height="652" alt="image" src="https://github.com/user-attachments/assets/ff4209b7-d12a-42f4-8242-856b03e2d23b" />
<img width="356" height="295" alt="image" src="https://github.com/user-attachments/assets/017c2dc1-8be1-493c-ab4b-c34245f63139" />
<img width="582" height="585" alt="image" src="https://github.com/user-attachments/assets/c2ba486a-43d2-477d-8633-22f344cf3a8b" />
<img width="846" height="813" alt="image" src="https://github.com/user-attachments/assets/eafed532-ccde-4e88-9708-b131b0192d97" />
<img width="1919" height="592" alt="image" src="https://github.com/user-attachments/assets/8e1b29bd-c757-4658-99b8-9fbe8fce8334" />
<img width="1912" height="903" alt="image" src="https://github.com/user-attachments/assets/a34f3053-13f7-4247-872e-348fa49116a4" />





