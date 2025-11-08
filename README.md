# Finance-Quest
Users track their spending and savings like a quest. Each financial action gives them XP, badges, and levels. The idea is to make budgeting and saving feel like playing an RPG — not a chore.

## Stack
- Frontend: React 18 + Vite, Tailwind CSS, Axios, React Router
- Backend: Django 5 + DRF, custom auth middleware, PyMongo (MongoDB)
- DB: MongoDB (Atlas or local)

## Features
- Auth: Sign Up, Login, Session (JWT stored in localStorage, Axios interceptor)
- Profiles: View XP, Level, Badges
- Transactions: List, Create, Delete (+ awards XP on create)
- Goals: List, Create
- XP: Manual award endpoint and UI
- Analytics: Spend by Category, Income vs Expense, Goal Progress & Forecast
- Recurring: Rules to auto-create transactions on a cadence (daily/weekly/monthly), Run Now / Run Due
- Savings Plans: Auto-increment goal progress on a cadence, Run Now / Run Due

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
- core/analytics_views.py (spend-by-category, income-vs-expense, goal-progress)
- core/recurring_views.py (recurring rules, savings plans, run-now, run-due)
- api/urls.py

Key frontend files:
- src/services/mongodbClient.js (Axios, auth, domain API helpers)
- src/context/AuthProvider.jsx (auth state + actions)
- src/components/Navbar.jsx
- src/pages/{Login,Dashboard,Transactions,Goals,Profile,AwardXP,Analytics,Recurring,Savings}.jsx
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
   - pip install -r requirements.txt (if present) or pip install django djangorestframework pymongo python-dotenv dj-database-url PyJWT django-cors-headers
2) Configure .env with MongoDB and secrets
3) Run server
   - python manage.py runserver 0.0.0.0:8000

Frontend (Vite):
1) cd finance-quest-web
2) npm install
3) npm install recharts
4) npm run dev (Vite dev server at http://localhost:5173)

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
- GET  /api/analytics/spend-by-category/?month=YYYY-MM
- GET  /api/analytics/income-vs-expense/?from=YYYY-MM-DD&to=YYYY-MM-DD
- GET  /api/analytics/goal-progress/
- GET  /api/recurring/
- POST /api/recurring/create/
- POST /api/recurring/{id}/run-now/
- POST /api/recurring/run-due/
- GET  /api/savings/
- POST /api/savings/create/
- POST /api/savings/{id}/run-now/
- POST /api/savings/run-due/

Headers
- Authorization: Bearer <access_token>
- (Dev) Middleware may also accept an X-User-Id header and will attach request.mongodb_user when valid

Notes
- Backend uses PyMongo directly; ids are stored as strings (UUIDs) in Mongo.
- Serializer validation ensures numeric and date fields are valid; the backend normalizes Decimals/UUIDs/Dates for Mongo.
- Recurring/Savings endpoints sanitize Mongo _id from JSON responses; analytics hardens datetimes and numbers.

## Troubleshooting
- 401 on signup/login: ensure auth middleware bypasses /api/auth/* (already configured), and JWT_SECRET matches.
- 403 on POST/DELETE: DRF permissions; we set AllowAny on viewsets. Ensure server reloaded.
- 500 when creating data: check Django console; we surface errors as 400 with { error: "create_failed: ..." }.
- Mongo errors about Decimal/UUID/date encoding: already handled by normalization in core/views.py.
- Frontend 404 at /: ensure finance-quest-web/index.html exists and Vite is running.
- Analytics goal-progress 500: server restart may be needed; endpoint returns 400 with readable error on bad data.

## Development Notes
- Auth: JWTs are issued in core/auth_views.py. Axios attaches them automatically.
- Gamification: Transactions create awards XP via core/gamelogic.py; levels are floor(xp/100); badges auto-check.
- Soft delete: destroy() toggles is_deleted.
- Transactions include a `type` field: "income" | "expense" for analytics.
- Recurring: "Run Due" processes rules with next_run <= now and advances by cadence.
- Savings: "Run Due" increments goals and advances next_run by interval.

## Seed demo data
Create a rich demo user with profile, 20 transactions, 6 goals, and xp logs:

```
python manage.py seed_superuser --email "admin+fq@example.com" --password "Passw0rd!234"
```

Use these credentials to log in at /login.

## Frontend Pages
- Dashboard: snapshot of XP/Level/Badges
- Transactions: list/create/delete (type, amount, category, occurred_at)
- Goals: list/create
- Profile: id, email, xp, level, badges
- Award XP: manual XP grant
- Analytics: spend by category, income vs expense, goal progress
- Recurring: list/create rules, Run Now / Run Due
- Savings: list/create plans, Run Now / Run Due

## Quick E2E Verification
1) Create a recurring rule and Run Now → confirm a transaction appears in Transactions.
2) Create a savings plan for a goal and Run Now → confirm goal current_amount increased.
3) Open Analytics → verify charts render (install recharts).

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
