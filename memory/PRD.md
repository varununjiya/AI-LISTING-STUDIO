# AI Listing Studio — PRD

## Original Problem Statement
Build "AI Listing Studio": a web app helping e-commerce sellers generate Amazon & Flipkart
product listings using AI. Requested stack was Next.js + Supabase; adapted to the
Emergent-supported stack: **React + FastAPI + MongoDB**. Auth = Emergent Google OAuth.
AI generation is MOCK JSON behind a swappable provider service layer.

## Architecture
- **Backend** (`/app/backend/server.py`): FastAPI, MongoDB (motor). Collections: users,
  user_sessions, products, generated_listings, uploads, exports, settings.
  Auth via Emergent Google OAuth (session cookie + Bearer fallback). Excel via openpyxl.
- **AI layer** (`/app/backend/ai_service.py`): `BaseAIProvider` abstraction + `MockAIProvider`.
  Swap/add providers (OpenAI/Gemini/Ollama) via `PROVIDERS` registry — no caller changes.
- **Frontend** (React + Tailwind + framer-motion + lenis): award-style landing page,
  Google login, dashboard app (sidebar + topbar, dark/light toggle).

## User Persona
E-commerce sellers listing products across Amazon & Flipkart who want AI-generated,
marketplace-ready copy and bulk exports.

## Implemented (2026-07-13)
- Award-winning landing page: kinetic masked hero reveal, parallax 3D shapes, editorial
  marquee, numbered manifesto chapters, bento showcase, stats, pricing CTA, huge footer.
- Emergent Google OAuth (login page + callback + protected routes + logout).
- Dashboard: 4 stat cards (Total/Draft/Completed/Exported) + recent products table
  (search + status filter + Add Product).
- Add Product: full field form + multiple base64 image upload; Save Draft + Generate Listing.
- Product Details: tabs (Product Information, Amazon, Flipkart, SEO, History); each
  generated section is editable with Copy / Regenerate / Save.
- AI generation (MOCK): amazon title/5 bullets/description/backend keywords, flipkart
  title/highlights/description, seo keywords, meta description, product specifications.
- Bulk Upload: xlsx/csv/pdf parse -> preview table -> Generate Listings for All.
- Exports: Amazon / Flipkart / Generic valid .xlsx downloads; marks products exported.
- Settings: AI provider, API key, marketplace, brand tone, language, char limits, export format.
- Dark/light theme toggle, toasts (sonner), skeleton loaders, responsive.

## Testing
- Backend pytest 19/19 pass (`/app/backend/tests/backend_test.py`).
- Frontend Playwright flows verified. CORS wildcard+credentials bug fixed (allow_origin_regex).

## Backlog / Next
- P1: Connect a real AI provider (OpenAI/Gemini) via existing service layer.
- P1: Persist export files for re-download from Exports history.
- P2: Amazon/Flipkart API publishing, image generation, competitor analysis, SEO scoring,
  approval workflow, multi-user roles, audit logs.
