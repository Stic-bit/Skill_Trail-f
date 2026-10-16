# Skill Trail

Skill Trail is a personal learning guide. Learners pick their interests, browse videos, docs, e-books and audio, check their own level, follow mentors, track projects and earn certificates. The frontend is a single-page dashboard and the backend is a Flask API, deployed on Vercel.

Live site: https://skill-trail-u.vercel.app

## Features

**Learner experience**
- Sign up, sign in and sign out with server-side sessions
- Onboarding: choose interests, goals, level, weekly hours and preferred content formats
- Overview page with sponsored, "based on your interests" and live sections (sponsored and live can be hidden)
- Content libraries: videos, docs, tests, PPTs, notes, audio, books, audiobooks and e-books
- Free and paid content, with a checkout flow for paid items
- Self-check: rate your skills and get recommendations
- Projects: plan, track and finish project ideas
- Degree guide for choosing a course of study
- Certificates for completed courses, printable and downloadable
- Friends, followers, following and chat with sample people
- Mentor profiles with follow and message options

**Navigation and layout**
- Collapsible left sidebar with a "<" button (docked on desktop, drawer on mobile)
- Sidebar groups: Overview, Browse, Grow, Community, Profile, Settings, Support
- Profile avatar in the top bar opens the profile page
- Tagline "For better learning" at the bottom of the sidebar

**Themes and accessibility**
- Dusk (dark), Daylight (light) or match-my-device
- Custom background and accent colours, chosen per user
- Text size options, reduced motion and high contrast

**Roles**
- Learner, mentor, or both. Mentors need a public account and a LinkedIn link
- Admin access is decided on the server (see Admin below)

**Guest mode**
- Try the app without an account. Guest data stays in the browser only

## Technology

| Part | Technology |
|---|---|
| Backend | Python 3.10+, Flask 3 |
| Database | SQLite (see Deployment notes) |
| Frontend | HTML, CSS and vanilla JavaScript in one template |
| Auth | Server sessions, PBKDF2-HMAC password hashing |
| Hosting | Vercel |

## Project structure

```text
Skill Trail/
├── README.md
└── skill_trail_python/
    ├── app.py                         Flask API and server
    ├── requirements.txt               Python dependencies
    ├── .gitignore
    ├── templates/
    │   └── index.html                 The whole frontend
    └── original_design_reference.html Earlier design prototype (reference only)
```

## Running locally

1. Clone the repository and open the project folder.
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```
3. Activate it.
   - Windows: `.venv\Scripts\activate`
   - macOS or Linux: `source .venv/bin/activate`
4. Install dependencies:
   ```bash
   cd skill_trail_python
   pip install -r requirements.txt
   ```
5. Optional: set an admin email for testing.
   - Windows (PowerShell): `$env:ADMIN_EMAILS="you@example.com"`
   - macOS or Linux: `export ADMIN_EMAILS=you@example.com`
6. Start the server:
   ```bash
   python app.py
   ```
7. Open http://127.0.0.1:5000

## Environment variables

| Name | Required | Purpose |
|---|---|---|
| `SKILL_TRAIL_SECRET` | Yes, in production | Signs session cookies. Use a long random value and keep it the same across deployments, otherwise users are signed out. |
| `ADMIN_EMAILS` | For admin access | Comma-separated admin emails, no spaces. Example: `a@x.com,b@x.com` |
| `SKILL_TRAIL_DB` | No | Custom path for the SQLite file |
| `FLASK_DEBUG` | No | Set to `1` for local debugging only |

Never commit secrets to GitHub. Set them in the Vercel dashboard.

## API overview

**Public**

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/topics` | List topics |
| GET | `/api/courses` | List learning paths (optional `?topic=`) |
| POST | `/api/register` | Create an account |
| POST | `/api/login` | Sign in |
| POST | `/api/logout` | Sign out |
| GET | `/api/me` | Current user, admin flag and saved state |

**Signed-in users**

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/state` | Read saved app state |
| PUT | `/api/state` | Save profile, interests, settings, saved items and more |
| PUT | `/api/preferences` | Update learning preferences |
| PUT | `/api/progress/<course_id>` | Update course completion |
| GET | `/api/certificates` | List certificate records |
| DELETE | `/api/account` | Delete your account and data |

**Admin only**

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/admin/users` | List all accounts and their saved data |

Admin routes return 401 when signed out and 403 for non-admins. The check runs on the server, not in the browser.

## Admin

1. Set `ADMIN_EMAILS` in Vercel (or locally) to the approved emails.
2. Create a normal account using one of those emails.
3. On the sign-in page, click **Admin / developer sign in** and sign in with the same details.
4. The sidebar then shows an Admin group: overview, all content, users, payments and certificates.

Emails are not verified, so register your admin accounts as soon as you set the variable.

## Deployment (GitHub to Vercel)

1. Create a feature branch, commit your changes and push it:
   ```bash
   git checkout -b my-feature
   git add .
   git commit -m "Describe the change"
   git push -u origin my-feature
   ```
2. Vercel builds a preview for the branch. Test it.
3. Merge to `main`:
   ```bash
   git checkout main
   git merge my-feature
   git push origin main
   ```
4. Vercel deploys `main` automatically.
5. In Vercel, Settings, General, make sure Root Directory is `skill_trail_python`.
6. After adding or changing environment variables, redeploy so they apply.

## Deployment notes and known limits

- **Data persistence:** Vercel has no permanent disk. The SQLite file lives in `/tmp` and can be reset on redeploys and cold starts, which removes accounts. For real use, move to a hosted database such as Postgres (Neon or Supabase) and external file storage for uploads.
- **Demo features:** payments, tests, mentor verification and certificates currently run as client-side demos. Certificates are demo completion records, not accredited qualifications.
- **Sample data:** friends, followers, mentors and chat contacts are sample people.
- **Security gaps:** no CSRF protection, login rate limiting, email verification or password reset yet.
- **Tests:** a browser cannot fully block tab switching. The planned test screen will use fullscreen, focus-loss detection, warnings and auto-submit.

## Roadmap

1. Move to a persistent hosted database
2. Server-side tests: mentor creates, admin verifies, server scores, every attempt stored, review available later
3. Server-issued certificates: only above 80% and after course completion, with a unique verification ID and server-generated PDF
4. Real payments with a gateway such as Razorpay and server-side webhook verification, with server-checked paywalls
5. Mentor applications with OTP verification and admin approval, plus private storage for ID documents
6. Real friend requests, follows, comments and feedback stored on the server
7. Profile picture upload to external storage
8. In-site players: embedded video, audio, PDF and code viewers
9. Rate limiting, CSRF protection and automated tests

## Author

**Stic-bit** (https://github.com/Stic-bit) and team

## License

Intended for educational use. Add a license file if you plan to distribute the project under specific terms.
