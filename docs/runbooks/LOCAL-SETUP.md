# Local developer setup
Copy `.env.example` to `.env`, set development-only secrets, then `docker compose up --build`. Inspect `docker compose logs -f backend`. Run test suite using `docker compose exec backend python manage.py test`. No seed accounts are created automatically.
