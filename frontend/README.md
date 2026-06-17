# StudySync AI — Frontend

React · TypeScript · Vite · Tailwind CSS · Framer Motion.

> **Frontend chunk 1: foundation.** Auth (register/login/logout), protected
> routing, typed API client, app shell, and a working Dashboard (productivity
> score, weekly stats, the animated garden, and the AI coach insight).
> Next: profile questionnaire → tasks/focus → matching → study rooms.

## Run it

The backend must be running first (see `../backend`). Then:

```bash
npm install
cp .env.example .env        # VITE_API_URL defaults to http://localhost:8000
npm run dev
```

Open **http://localhost:5173**. Register an account, and you'll land on your
dashboard. (Tip: run the backend with `uvicorn app.main:socket_app --reload`
once you reach the study-rooms chunk; `app.main:app` is fine until then.)

```bash
npm run build     # type-check + production build
npm run preview   # serve the built app
```

## Structure

```
src/
├── lib/
│   ├── api.ts        # fetch wrapper (JWT) + typed endpoint helpers
│   └── types.ts      # types mirroring the backend schemas
├── context/
│   └── AuthContext.tsx   # token persistence, login/register/logout
├── components/
│   ├── ProtectedRoute.tsx
│   ├── Layout.tsx        # top nav shell
│   └── GardenStage.tsx   # the signature animated garden (Seed → Fruit Tree)
├── pages/
│   ├── Login.tsx
│   ├── Register.tsx
│   └── Dashboard.tsx
├── App.tsx           # routes
└── main.tsx          # entry (Router + AuthProvider)
```

## Design

The identity is quiet cultivation — the garden that grows with your
consistency is the one bold element; everything else stays disciplined.
Tokens live in `tailwind.config.js`: growth-green primary, warm amber for
streaks/XP, Fraunces (display) + Inter (body) + Space Mono (the numbers).

## Notes
- JWT is stored in `localStorage` and attached by the API client automatically.
- The signup form captures the browser timezone, which the backend uses to
  bucket streaks and active days correctly.
