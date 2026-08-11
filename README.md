# KanMind Backend

REST API for the KanMind kanban board, built with Django and Django REST
Framework. It powers the KanMind frontend: user registration and login with
token authentication, boards shared between members, tasks with assignees and
reviewers, and comments on tasks.

The frontend lives in its own repository and is **not** part of this project.

## Requirements

- Python 3.12 or newer (developed and tested on 3.14)
- pip

No database server is needed. The project uses SQLite, which ships with
Python.

## Setup

Clone the repository and change into it:

```bash
git clone https://github.com/larsbeckdev/backend.git
cd backend
```

Create and activate a virtual environment:

```bash
# Windows (PowerShell)
python -m venv env
env\Scripts\Activate.ps1

# macOS / Linux
python3 -m venv env
source env/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Create the database:

```bash
python manage.py migrate
```

Start the development server:

```bash
python manage.py runserver
```

The API is now available at `http://127.0.0.1:8000/api/`.

## Optional: demo data

The project ships with a management command that creates three demo users, a
board with one task per status and a comment on every task:

```bash
python manage.py seed_demo
```

It is safe to run more than once and prints the guest credentials it created,
so run it once and read the login details off your terminal. All demo
accounts share the same password.

One of the accounts is the one the "Guest Login" button of the frontend
expects; the frontend hard-codes it in `shared/js/config.js`. The account
definitions live in
`kanban_app/management/commands/seed_demo.py` if you need to look them up
later.

## Optional: admin interface

The Django admin is enabled and can manage users, boards, tasks and comments.
Create an administrator account:

```bash
python manage.py createsuperuser
```

You will be asked for an email address and a full name — this project has no
username field. The admin is served at `http://127.0.0.1:8000/admin/`.

## Connecting the frontend

The frontend reads its API base URL from `shared/js/config.js`. It has to
match the address this backend runs on:

```javascript
const API_BASE_URL = 'http://127.0.0.1:8000/api/';
```

Because the frontend is served from a different origin than the API, CORS is
handled by `django-cors-headers`.

To reach the backend from another device in the same network, start it on all
interfaces and point the frontend at the machine's IP address:

```bash
python manage.py runserver 0.0.0.0:8000
```

A browser on another device resolves `127.0.0.1` to itself, so leaving the
default value in `config.js` makes every request fail silently.

## Running the tests

The project has 121 tests covering every endpoint, its permissions and its
error responses.

```bash
python manage.py test
```

With a coverage report:

```bash
coverage run --source='.' --omit='*/migrations/*,*/tests/*,env/*,manage.py,core/asgi.py,core/wsgi.py' manage.py test
coverage report -m
```

Current coverage: **100%**.

## Code style

The code follows PEP 8 with the default line length of 79 characters:

```bash
flake8 --exclude=env,migrations,.git .
```

## Project structure

```text
backend/
├── core/                  Project configuration
│   ├── settings.py        Installed apps, DRF, CORS, custom user model
│   └── urls.py            Central routing, includes every app below /api/
├── auth_app/              Authentication
│   ├── models.py          User model (email as identifier, fullname)
│   ├── managers.py        User creation helpers
│   ├── admin.py           Admin configuration
│   ├── api/               serializers.py, views.py, urls.py
│   └── tests/             Registration, login, email check, model tests
├── kanban_app/            Boards, tasks and comments
│   ├── models.py          Board, Task, Comment
│   ├── admin.py           Admin configuration
│   ├── api/               serializers.py, views.py, urls.py,
│   │                      permissions.py, utils.py
│   ├── management/        seed_demo command
│   └── tests/             Board, task, comment and model tests
├── manage.py
└── requirements.txt
```

## Notable implementation details

- **Custom user model.** `auth_app.User` replaces `username`, `first_name`
  and `last_name` with a single `fullname` field and uses the email address
  as `USERNAME_FIELD`, because that is what the frontend submits. Because of
  this, `AUTH_USER_MODEL` must stay in place — the database cannot be
  migrated to a different user model afterwards.
- **Case-insensitive email addresses.** The unique constraint on the model is
  case sensitive, so registration additionally rejects addresses that differ
  from an existing one only in capitalisation.
- **Board counters.** The board list aggregates its member, ticket, to-do and
  high-priority counts in a single query. The accessible board ids are
  resolved in a subquery first, otherwise Django would reuse the membership
  join for the member count and report the wrong number.
- **Tasks cannot change boards.** The board of an existing task is read-only,
  so a `board` key in a PATCH payload is ignored instead of rejected.
- **Deletion rules.** Only a board owner may delete a board, only the creator
  of a task or the owner of its board may delete the task, and only the
  author of a comment may delete it.

## Security notes for deployment

This repository is configured for local development. Before deploying it
anywhere, change the following in `core/settings.py`:

- `DEBUG` must be `False`.
- `SECRET_KEY` must be read from the environment, not from the source file.
- `ALLOWED_HOSTS` must list the real host names instead of `'*'`.
- `CORS_ALLOW_ALL_ORIGINS` must be replaced by an explicit
  `CORS_ALLOWED_ORIGINS` list.

The SQLite database file is excluded from version control.

## API endpoints

All endpoints are prefixed with `/api/` and, except for registration and
login, require the header `Authorization: Token <token>`.

### Authentication

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/api/registration/` | Create an account, returns a token |
| POST | `/api/login/` | Authenticate, returns a token |
| GET | `/api/email-check/?email=` | Look up a user by email address |

### Boards

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/boards/` | Boards the user owns or is a member of |
| POST | `/api/boards/` | Create a board, the user becomes its owner |
| GET | `/api/boards/{board_id}/` | Board with its members and tasks |
| PATCH | `/api/boards/{board_id}/` | Update title and members |
| DELETE | `/api/boards/{board_id}/` | Delete a board (owner only) |

### Tasks

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/api/tasks/` | Create a task on a board |
| PATCH | `/api/tasks/{task_id}/` | Update a task |
| DELETE | `/api/tasks/{task_id}/` | Delete a task (creator or board owner) |
| GET | `/api/tasks/assigned-to-me/` | Tasks the user is assigned to |
| GET | `/api/tasks/reviewing/` | Tasks the user reviews |

### Comments

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/tasks/{task_id}/comments/` | Comments of a task |
| POST | `/api/tasks/{task_id}/comments/` | Add a comment |
| DELETE | `/api/tasks/{task_id}/comments/{comment_id}/` | Delete own comment |

`status` accepts `to-do`, `in-progress`, `review` and `done`.
`priority` accepts `low`, `medium` and `high`.
