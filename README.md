# Finance-Quest
Users track their spending and savings like a quest. Each financial action gives them XP, badges, and levels. The idea is to make budgeting and saving feel like playing an RPG — not a chore.

## Stack
- Frontend: React 18 + Vite, Tailwind CSS, Axios, React Router
- Backend: Django 5 + DRF, custom auth middleware, PyMongo (MongoDB)
- DB: MongoDB (Atlas or local)

## Features (MVP)
- Auth: Sign Up, Login, Session (JWT stored in localStorage, Axios interceptor)
- Profiles: View XP, Level, Badges
- Transactions: List, Create, Delete (+ awards XP on create)
- Goals: List, Create
- XP: Manual award endpoint and UI

## Project Structure
```
Finance-Quest-1/
  api/                  # Django project settings and URLs
  core/                 # Backend app: views, serializers, middleware, gamelogic
  finance-quest-web/    # React app (Vite)
  README.md
```

Key backend files:
- core/middleware/auth_middleware.py
- core/views.py (PyMongo CRUD for profiles, transactions, goals, xp_log)
- core/auth_views.py (signup, login, profile)
- core/gamelogic.py (award_xp, levels, badges)
- core/mongo.py (Mongo client/db helpers)
- api/urls.py

Key frontend files:
- src/services/mongodbClient.js (Axios, auth, domain API helpers)
- src/context/AuthProvider.jsx (auth state + actions)
- src/components/Navbar.jsx
- src/pages/{Login,Dashboard,Transactions,Goals,Profile,AwardXP}.jsx
- src/App.jsx (routes + auth guard)

## Prerequisites
- Node.js LTS (>=18)
- Python 3.10+
- MongoDB Atlas connection string (or local Mongo)

## Environment Variables

Backend (.env in project root or api/):
- SECRET_KEY=replace-with-strong-secret
- DEBUG=true
- MONGODB_URI=mongodb+srv://<user>:<pass>@cluster.mongodb.net/
- MONGODB_DB=finance_quest
- JWT_SECRET=replace-with-strong-secret
- JWT_ALGORITHM=HS256
- AUTH_VERIFY_URL= (optional external JWT verify URL)

Frontend (finance-quest-web/.env):
- VITE_API_BASE_URL=http://localhost:8000

## Setup & Run

Backend (Django):
1) Create venv and install deps
   - python -m venv .venv
   - .\.venv\Scripts\activate (Windows)
   - pip install -r requirements.txt (if present) or pip install django djangorestframework pymongo python-dotenv dj-database-url PyJWT corsheaders
2) Configure .env with MongoDB and secrets
3) Run server
   - python manage.py runserver 0.0.0.0:8000

Frontend (Vite):
1) cd finance-quest-web
2) npm install
3) npm run dev (Vite dev server at http://localhost:5173)

Login flow:
- Open http://localhost:5173/login
- Sign Up or Login
- You’ll be redirected to /dashboard and can navigate using the navbar

## API Summary
- POST /api/auth/signup/
- POST /api/auth/login/
- GET  /api/profile/
- GET  /api/transactions/
- POST /api/transactions/
- DELETE /api/transactions/{id}/
- GET  /api/goals/
- POST /api/goals/
- POST /api/xp/award/

Headers
- Authorization: Bearer <access_token>
- (Dev) Middleware may also accept an X-User-Id header and will attach request.mongodb_user when valid

Notes
- Backend uses PyMongo directly; ids are stored as strings (UUIDs) in Mongo.
- Serializer validation ensures numeric and date fields are valid; the backend normalizes Decimals/UUIDs/Dates for Mongo.

## Troubleshooting
- 401 on signup/login: ensure auth middleware bypasses /api/auth/* (already configured), and JWT_SECRET matches.
- 403 on POST/DELETE: DRF permissions; we set AllowAny on viewsets. Ensure server reloaded.
- 500 when creating data: check Django console; we surface errors as 400 with { error: "create_failed: ..." }.
- Mongo errors about Decimal/UUID/date encoding: already handled by normalization in core/views.py.
- Frontend 404 at /: ensure finance-quest-web/index.html exists and Vite is running.

## Development Notes
- Auth: JWTs are issued in core/auth_views.py. Axios attaches them automatically.
- Gamification: Transactions create awards XP via core/gamelogic.py; levels are floor(xp/100); badges auto-check.
- Soft delete: destroy() toggles is_deleted.

## Roadmap & Ideas (Additional Functionality)
- Analytics & Charts
  - Monthly spend charts by category
  - Goal progress charts and forecast to target date
  - Cashflow insights (income vs expenses trends)
- Budgeting
  - Monthly budgets per category with alerts when approaching limits
  - Envelope-style budgeting and rollover
- Recurring Items
  - Recurring transactions (subscriptions, bills) with reminders
  - Savings plans that auto-increment current_amount toward a goal
- Categories & Tags
  - Custom categories, multi-tag support, and filters
  - Import/export category mappings (CSV)
- Data Import/Export
  - CSV import for bank statements with mapping wizard
  - CSV/JSON export of transactions and goals
- Badges & Quests
  - Quest system (multi-step challenges) with rewards
  - Streaks and daily/weekly missions
- Social & Sharing
  - Share achievements/badges, optional leaderboards among friends
  - Collaborative goals (family savings goals)
- Notifications
  - Email/push notifications for goals, budgets, streaks
- Security & Auth
  - Password reset flow
  - OAuth (Google/Apple) and device sessions management
  - Role-based access if adding admin tools
- Admin & Ops
  - Admin dashboard to view users/goals/transactions, export reports
  - Feature flags and A/B experiments for gamification tuning
- Platform
  - PWA support (installable app, offline cache)
  - Mobile-first UI enhancements

## Contributing
PRs welcome. Please include clear descriptions and, where possible, reproduce steps for bugs.

## License
MIT
