
# Skill Trail — Python-Focused Learning Platform

## Project Overview

Skill Trail is a learning-path dashboard built with a Python backend and a lightweight HTML, CSS, and JavaScript frontend. It helps users explore learning topics, organize their goals, track course progress, and view demo completion certificates.

This project demonstrates practical Python programming, web development, API design, authentication, and database concepts.

## Technology Stack

- **Backend:** Python 3.10+, Flask REST API
- **Frontend:** HTML, CSS, JavaScript
- **Database:** SQLite
- **Authentication:** Server-side sessions and PBKDF2-HMAC password hashing

## Features

- Create an account, sign in, and sign out
- Securely hash passwords instead of storing them in plain text
- Browse topics and learning paths
- Save learning interests, goals, skill level, and weekly study hours
- Track course completion
- Store progress records
- Generate demo certificate codes
- Access application data through REST API endpoints

## Project Structure

```text
Skill_Trail/
├── app.py
├── requirements.txt
├── skill_trail.db
├── templates/
│   └── index.html
├── static/
│   ├── css/
│   ├── js/
│   └── other assets
└── README.md
```

The structure above is illustrative. Actual folders and files may differ.

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/Stic-bit/Skill_Trail.git
cd Skill_Trail
```

If the application files are inside a subfolder, navigate to that folder before continuing.

### 2. Create a virtual environment

```bash
python -m venv .venv
```

On Windows:

```bash
.venv\Scripts\activate
```

On macOS or Linux:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
python app.py
```

Open the local URL displayed in your terminal, usually:

`http://127.0.0.1:5000`

## API Overview

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Application health check |
| GET | `/api/topics` | List available topics |
| GET | `/api/courses` | List learning paths |
| POST | `/api/register` | Create an account |
| POST | `/api/login` | Sign in |
| POST | `/api/logout` | Sign out |
| GET | `/api/me` | Retrieve current user data |
| PUT | `/api/preferences` | Update learning preferences |
| PUT | `/api/progress/<course_id>` | Update course completion |
| GET | `/api/certificates` | List demo certificate records |

## Frontend and Backend Responsibilities

**Frontend**
- Page layout and styling
- Forms and user interactions
- Course cards and filtering
- Displaying progress and messages

**Python backend**
- Input validation
- Password hashing and authentication
- Session management
- API responses
- Preference and progress updates
- Certificate record generation
- Database access

## Deployment and Database Notes

The application currently uses SQLite. A local SQLite database file is not automatically a persistent, shared database when the application is deployed to a serverless platform such as Vercel.

For persistent production data, use an appropriately configured persistent database. Configure `SKILL_TRAIL_SECRET` through the deployment platform's environment variables and keep it stable across deployments. Never commit production secrets to GitHub.

## Security and Limitations

Skill Trail is an educational prototype, not a production-ready service.

Before production use, consider adding:
- CSRF protection
- Login rate limiting
- Email verification and password reset
- Production security configuration
- Database migrations and automated tests
- Persistent production database storage

The certificate feature creates demo completion records, not accredited qualifications. The application does not implement real payments or a verified administrator role.

## Future Improvements

- Expand the topic and course catalogue
- Improve the user interface and accessibility
- Add automated tests
- Improve database management
- Add verified learning achievements
- Expand deployment and security support

## Author

**Stic-bit**

GitHub: https://github.com/Stic-bit

## License

This project is intended for educational and learning purposes. A specific license should be added if you plan to distribute the project under particular terms.

## Update: new interface + server-side accounts

- The frontend (`skill_trail_python/templates/index.html`) now uses the full dashboard design: docked collapsible sidebar, top-bar profile avatar, onboarding, libraries, self-check, certificates, mentors, custom colour themes.
- Account data (profile, interests, settings, saved items) is saved on the server through `GET/PUT /api/state`.
- Admins are decided on the server by the `ADMIN_EMAILS` environment variable (comma-separated). Admin pages call `GET /api/admin/users`, which returns 403 for everyone else.
- New env var: `ADMIN_EMAILS`. Keep `SKILL_TRAIL_SECRET` set and stable.
- Existing routes are unchanged. New routes: `/api/state`, `/api/account` (DELETE), `/api/admin/users`.
