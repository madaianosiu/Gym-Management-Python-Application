# GYM+ (Flask)

Modern gym web app (user area + public pages + auth), built with Flask using a clean blueprint structure.
Firebase and AI integrations are planned for later.

## Run

1. Create a virtual environment
2. Install dependencies
3. Start the server

Example (PowerShell):

- `python -m venv .venv`
- `.venv\Scripts\Activate.ps1`
- `pip install -r requirements.txt`
- `python run.py`

Open:

- `http://127.0.0.1:5000/`

Health check:

- `http://127.0.0.1:5000/health`

## Demo accounts (mock auth)

- user@gym.com / 1234
- admin@gym.com / 1234

## Planned integrations

- Firebase (Auth + Firestore)
- AI Coach (chat/workout plan generator)
- Real payment provider (Stripe/Netopia/etc.)
