up:
\tcd ../infra && docker compose up -d

down:
\tcd ../infra && docker compose down

logs:
\tcd ../infra && docker compose logs -f

migrate:
\tcd ../app && uv run python manage.py migrate

run:
\tcd ../app && uv run python manage.py runserver 0.0.0.0:8000

seed:
\tcd ../app && uv run python manage.py seed
