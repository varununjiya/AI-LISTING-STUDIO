# 🚀 AI Listing Studio - Production-Ready Multi-Marketplace SaaS

**Production-grade Multi-Marketplace Content & Catalog Management SaaS for Amazon, Flipkart, & Meesho.**

AI Listing Studio allows e-commerce sellers to connect their seller accounts on **Amazon SP-API**, **Flipkart Seller API**, and **Meesho Seller API**, fetch live catalogs/orders/inventory, import products with 1-click, and generate high-converting AI listings, SEO metadata, and studio photography images.

---

## 🌟 Key Features & Architecture Overview

### 🛍️ 1. Multi-Marketplace Integration
- **Amazon Selling Partner API (SP-API)**:
  - LWA OAuth 2.0 Seller Authentication & auto token refresh
  - Fetch Listings, Orders, Inventory, Pricing, Catalog & Images
  - Native support for ASIN, SKU, Brand, Product Type, and Specifications
- **Flipkart Seller Hub API**:
  - OAuth 2.0 token management & secure token rotation
  - Import FSN, SKU, Catalog, Orders, Inventory & Pricing
- **Meesho Seller API**:
  - API Key & Supplier authentication
  - Direct Meesho catalog, orders & inventory import

### 📊 2. Marketplace Dashboard & Import Center
- **Interactive Dashboard Cards**: Live status indicators (Connected/Disconnected) for Amazon, Flipkart, & Meesho with total listing count, orders, inventory, and revenue tracking.
- **1-Click Import Products**: Select any connected marketplace -> fetch catalog -> select items -> import into AI Listing Studio with auto-populated title, description, brand, category, images, price, SKU, and specifications.

### 🤖 3. Modular AI Pipeline & Image Studio
- **Listing & SEO Generation**: OpenRouter integration supporting DeepSeek, Claude 3.5, & Qwen 2.5 models.
- **Modular Image Generation Abstraction (`ImageGenerationProvider`)**:
  - Switch providers via `IMAGE_GENERATION_PROVIDER` inside `.env` or settings
  - Supported Providers: **Google Gemini (Imagen 3)**, **HuggingFace (FLUX.1/SD)**, and **Pollinations AI**.

### 💳 4. Razorpay Subscriptions & Usage Limits
- **Free Tier**: 5 AI generations limit
- **Monthly Pro (₹100/month)**: Unlimited AI generations, Priority Processing Queue
- **Yearly Pro (₹1000/year)**: Unlimited AI generations, Priority Processing Queue, Advanced Analytics
- Automated Razorpay payment signature verification & webhook event handling (`payment.captured`, renewals, cancellation, expiry).

### 🔒 5. Security & Credentials Encryption
- Sensitive Access Tokens, Refresh Tokens, and Client Secrets are encrypted at rest using **Fernet AES-256** symmetric encryption before storage in MongoDB.
- Credentials are never exposed to the frontend API payloads.

---

## 🔑 Environment Variables Reference

### Backend (`backend/.env`)

```env
# Database & General
MONGO_URL="mongodb+srv://user:password@cluster.mongodb.net/?appName=Cluster0"
DB_NAME="ai_listing_studio"
CORS_ORIGINS="*"
ENCRYPTION_KEY="your-32-byte-fernet-encryption-secret-key"

# AI OpenRouter Configuration
OPENROUTER_API_KEY_1="sk-or-v1-xxxxxxxx"
OPENROUTER_API_KEY_2=""
OPENROUTER_API_KEY_3=""

# Modular Image Generation Provider
# Options: gemini, huggingface, pollinations
IMAGE_GENERATION_PROVIDER="gemini"
GEMINI_API_KEY="AIzaSyXXXXXXXX"
GEMINI_IMAGE_MODEL="imagen-3.0-generate-002"
HUGGINGFACE_API_KEY="hf_XXXXXXXX"
POLLINATIONS_API_URL="https://image.pollinations.ai/prompt/"

# Amazon SP-API Credentials
AMAZON_APP_ID="amzn1.sp.solution.xxxxxxxx"
AMAZON_CLIENT_ID="amzn1.application-oa2-client.xxxxxxxx"
AMAZON_CLIENT_SECRET="amzn1.oa2-cs.v1.xxxxxxxx"
AMAZON_SP_API_ENDPOINT="https://sellingpartnerapi-fe.amazon.com"

# Flipkart Seller API Credentials
FLIPKART_APP_ID="fk_app_xxxxxxxx"
FLIPKART_APP_SECRET="fk_sec_xxxxxxxx"

# Meesho Seller API Credentials
MEESHO_API_KEY="meesho_api_key_xxxxxxxx"
MEESHO_SUPPLIER_ID="MSH-SUP-10293"

# Razorpay Subscriptions
RAZORPAY_KEY_ID="rzp_test_XXXXXXXX"
RAZORPAY_KEY_SECRET="XXXXXXXXXXXX"
RAZORPAY_WEBHOOK_SECRET="whsec_XXXXXXXX"
```

### Frontend (`frontend/.env`)

```env
REACT_APP_BACKEND_URL="http://localhost:8001"
```

---

## 📖 Setup & Setup Guides

### 🟧 1. Amazon SP-API Setup
1. Register a Seller Central Account on [Amazon Seller Central India](https://sellercentral.amazon.in/).
2. Create an App in Developer Central:
   - OAuth Redirect URI: `https://your-frontend-domain.vercel.app/settings`
   - Select Roles: **Product Listing**, **Pricing**, **Orders**, **Inventory**.
3. Copy `LWA Client ID`, `LWA Client Secret`, and `Refresh Token` into backend environment variables or connect via the Settings modal.

### 🟦 2. Flipkart Seller API Setup
1. Register on [Flipkart Seller Hub](https://seller.flipkart.com/).
2. Request API Developer Access to get `Application ID` and `Application Secret`.
3. Set OAuth Redirect URI to `https://your-frontend-domain.vercel.app/settings`.

### 🟪 3. Meesho Seller API Setup
1. Login to [Meesho Supplier Panel](https://supplier.meesho.com/).
2. Generate your `Supplier API Key` under Settings -> API Integration.
3. Enter `Supplier ID` and `API Key` in Settings.

---

## ⚡ Deployment Instructions

### Backend (Render / Vercel Serverless)
1. Push repository to GitHub.
2. Create a Web Service on [Render](https://render.com/).
3. Build Command: `pip install -r backend/requirements.txt`
4. Start Command: `cd backend && uvicorn server:app --host 0.0.0.0 --port $PORT`
5. Add environment variables listed above.

### Frontend (Vercel)
1. Import GitHub repository into [Vercel](https://vercel.com).
2. Set Root Directory: `frontend`
3. Framework Preset: `Create React App`
4. Environment Variable: `REACT_APP_BACKEND_URL=https://your-backend.onrender.com`

---

## 🧪 Testing Instructions

Run backend unit & integration tests:
```bash
cd backend
py -m pytest
```

Test server loading & API status:
```bash
py -c "import server; print('Server ready!')"
```

Visit local frontend at `http://localhost:3000`.
