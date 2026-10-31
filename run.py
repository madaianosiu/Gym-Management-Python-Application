import os
from dotenv import load_dotenv

load_dotenv()

from app import create_app  # noqa: E402
from app.config import Config  # noqa: E402

app = create_app(Config)

if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "5000"))
    app.run(host=host, port=port, debug=app.config.get("DEBUG", False))