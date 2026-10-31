# GYM+ – Smart Gym System (Python)

Fitness management web application built with Python (Flask), Firebase and an AI Coach module. Developed as a Master's dissertation project at Transilvania University of Brașov.

The application has three areas: a public area, a member area and an admin area, with role-based access control (USER / ADMIN).

## Features

**Public area**
- Home, pricing, about, contact form and public store

**Member area**
- Registration and login with Firebase Authentication
- Profile and membership management
- Class booking (with duplicate-booking checks)
- Online store with shopping cart
- Simulated checkout flow, payment history and receipts
- AI Coach: fitness and nutrition guidance, with saved plans

**Admin area**
- Overview dashboard (members, active memberships, orders, messages, revenue)
- Customer, booking and payment monitoring
- Contact message management with replies
- Store management (create, edit, delete products)

## AI Coach

- Extracts profile data (weight, height, goal, training days, level) from free text using regular expressions
- Calculates protein targets, calorie estimates, weekly and yearly training plans
- Generates answers through the OpenAI API
- Falls back to rule-based logic when the API is unavailable or disabled
- Keeps short conversation history and saves plans to Cloud Firestore

## Tech stack

- **Backend:** Python, Flask (blueprints, service layer, access-control middleware)
- **Authentication:** Firebase Authentication, server-side token verification (Firebase Admin SDK)
- **Database:** Cloud Firestore (NoSQL)
- **AI:** OpenAI API with rule-based fallback
- **Frontend:** HTML templates, CSS, JavaScript

## Run locally

1. Create and activate a virtual environment (PowerShell):
   - `python -m venv .venv`
   - `.venv\Scripts\Activate.ps1`
2. Install dependencies: `pip install -r requirements.txt`
3. Add your Firebase service account key at `app/firebase/serviceAccountKey.json` (not included in the repository).
4. Create a `.env` file (see `.env.example`):
   - `SECRET_KEY=`
   - `AI_ENABLED=1`
   - `OPENAI_API_KEY=`
   - `OPENAI_MODEL=gpt-5-mini`
5. Start the server: `python run.py`

Open `http://127.0.0.1:5000/`. Health check: `http://127.0.0.1:5000/health`

If `AI_ENABLED` is not set to `1` or no API key is provided, the AI Coach runs in rule-based mode.

## Screenshots

<img width="503" height="350" alt="image" src="https://github.com/user-attachments/assets/4964365e-1bd8-40bd-a80e-21571b2f42fc" />

<img width="525" height="332" alt="image" src="https://github.com/user-attachments/assets/33974889-986c-4a32-8e11-b1908ac2b366" />

<img width="489" height="284" alt="image" src="https://github.com/user-attachments/assets/6d2deb8a-9981-4b2f-ad43-bfa34115aa9b" />

<img width="488" height="317" alt="image" src="https://github.com/user-attachments/assets/8ae1b2c4-5f61-4851-af44-6991dde67c98" />


