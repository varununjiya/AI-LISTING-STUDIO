# 🚀 AI Listing Studio

**AI-Powered E-commerce Content Generation Platform**

Generate high-quality product listings, SEO content, and images for Amazon, Flipkart, Meesho, Shopify, and WooCommerce.

---

## ✨ Features

### 🤖 AI-Powered Content Generation
- **Multi-Marketplace Listings**: Generate optimized listings for Amazon, Flipkart, and Meesho
- **Advanced SEO**: Primary, secondary, long-tail, trending, and competitor keywords
- **Quality Scoring**: 0-100 scoring with actionable recommendations
- **Natural Language**: No repetition, proper grammar, keyword optimization

### 🎨 AI Image Studio (FREE!)
- **22 Image Presets**: Studio shots, lifestyle images, commerce images, social media graphics
- **Powered by Pollinations.ai**: FREE unlimited image generation
- **High Quality**: 1024x1024 resolution with FLUX models
- **Multiple Styles**: White background, product angles, lifestyle scenes, promotional banners

### 📊 Complete Product Management
- **Bulk Upload**: Excel, CSV support
- **Version History**: Track and restore previous versions
- **Quality Analytics**: Detailed breakdown and suggestions
- **Export Options**: Amazon, Flipkart, Meesho, Shopify, WooCommerce formats

---

## 🏗️ Tech Stack

### Frontend
- **React 18** with React Router
- **Tailwind CSS** + shadcn/ui components
- **Framer Motion** for animations
- **Recharts** for analytics
- **Axios** for API calls

### Backend
- **FastAPI** (Python)
- **Motor** (Async MongoDB driver)
- **OpenRouter** for AI text generation
- **Pollinations.ai** for FREE image generation

### Database
- **MongoDB Atlas** (Cloud)

### AI Models
- **DeepSeek** - Listing generation (~$0.14 per 1000 listings)
- **Qwen** - SEO generation (~$0.02 per 1000)
- **Qwen Vision** - Image analysis
- **FLUX** - Image generation (FREE via Pollinations.ai)

---

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and Yarn
- Python 3.11+
- MongoDB Atlas account
- OpenRouter API key

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/varununjiya/AI-LISTING-STUDIO.git
cd AI-LISTING-STUDIO
```

2. **Backend Setup**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your MongoDB Atlas URL and OpenRouter API key
```

3. **Frontend Setup**
```bash
cd frontend
yarn install
cp .env.example .env
# Edit .env with your backend URL
```

4. **Run Locally**
```bash
# Terminal 1 - Backend
cd backend
uvicorn server:app --reload --port 8001

# Terminal 2 - Frontend
cd frontend
yarn start
```

Visit: http://localhost:3000

---

## ☁️ Deploy to Vercel

**Full deployment guide:** See [VERCEL_DEPLOYMENT.md](./VERCEL_DEPLOYMENT.md)

### Quick Deploy

1. **Push to GitHub** (this repo)
2. **Import to Vercel**: https://vercel.com/new
3. **Add Environment Variables** (see deployment guide)
4. **Deploy!**

**Vercel automatically:**
- ✅ Builds React frontend
- ✅ Deploys FastAPI backend as serverless
- ✅ Configures routes
- ✅ Provides HTTPS domain

---

## 🔑 Environment Variables

### Backend (.env)
```bash
MONGO_URL=mongodb+srv://...
DB_NAME=ai_listing_studio
OPENROUTER_API_KEY_1=sk-or-v1-...
IMAGE_GENERATION_SERVICE=pollinations
POLLINATIONS_API_URL=https://image.pollinations.ai/prompt/
```

### Frontend (.env)
```bash
REACT_APP_BACKEND_URL=https://your-api-url.vercel.app
```

---

## 💰 Cost

**MongoDB Atlas:** Free tier (512 MB) or ~$9/month  
**OpenRouter:** ~$1-20/month (pay as you go)  
**Pollinations.ai:** FREE Forever  
**Vercel:** Free tier (100 GB bandwidth)

**Total: $1-30/month**

---

## 📚 Documentation

- [Vercel Deployment Guide](./VERCEL_DEPLOYMENT.md)
- [MongoDB Atlas Setup](./memory/MONGODB_POLLINATIONS_SETUP.md)
- [OpenRouter Integration](./memory/UPGRADE_COMPLETE.md)

---

## 🛠️ Project Structure

```
AI-LISTING-STUDIO/
├── backend/
│   ├── ai_engine/           # OpenRouter AI Engine
│   │   ├── ai_manager.py
│   │   ├── openrouter_service.py
│   │   ├── pollinations_service.py
│   │   ├── model_router.py
│   │   └── prompt_manager.py
│   ├── prompts/             # AI prompt templates
│   ├── server.py            # FastAPI app
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/           # React pages
│   │   ├── components/      # Reusable components
│   │   ├── contexts/        # React contexts
│   │   └── lib/             # Utilities
│   └── package.json
├── vercel.json              # Vercel configuration
└── VERCEL_DEPLOYMENT.md     # Deployment guide
```

---

## 🎯 Key Features Explained

### Listing Generation
- Marketplace-specific optimization
- Character limit enforcement
- Natural keyword integration
- Anti-repetition algorithms

### AI Image Studio
- 22 preset styles
- Background replacement
- Product photography
- Social media graphics
- Promotional banners

### SEO Center
- Primary & secondary keywords
- Long-tail keyword suggestions
- Trending keywords
- Competitor analysis
- Meta descriptions

### Quality Scoring
- Completeness check
- Marketplace compliance
- SEO optimization score
- Readability analysis
- Image completeness

---

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines.

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🔗 Links

- **Live Demo**: [Coming Soon]
- **Documentation**: See /memory folder
- **OpenRouter**: https://openrouter.ai/
- **Pollinations.ai**: https://pollinations.ai/
- **MongoDB Atlas**: https://cloud.mongodb.com/

---

## 📧 Support

For issues or questions:
- GitHub Issues: https://github.com/varununjiya/AI-LISTING-STUDIO/issues
- Email: [Your Email]

---

## ⭐ Star This Repo!

If you find this project useful, please give it a star ⭐

---

**Built with ❤️ using OpenRouter, Pollinations.ai, and MongoDB Atlas**

**Version:** 2.0 (MongoDB Atlas + Pollinations.ai Edition)
