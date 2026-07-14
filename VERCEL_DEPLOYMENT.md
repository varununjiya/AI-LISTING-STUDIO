# 🚀 VERCEL DEPLOYMENT GUIDE - AI LISTING STUDIO

## ✅ Prerequisites Completed

- ✅ MongoDB Atlas configured
- ✅ OpenRouter API key added
- ✅ Pollinations.ai integrated (FREE)
- ✅ All code ready for deployment
- ✅ GitHub repository: https://github.com/varununjiya/AI-LISTING-STUDIO

---

## 📋 DEPLOYMENT STEPS

### **Step 1: Push Code to GitHub** 🔄

**Using Emergent's "Save to GitHub" Feature:**

1. Look for the **"Save to GitHub"** button in your Emergent chat interface
2. Click it to push all code to your repository
3. Confirm the push to the `master` branch
4. Verify code is pushed: Visit https://github.com/varununjiya/AI-LISTING-STUDIO

**What gets pushed:**
- ✅ All frontend code
- ✅ All backend code with OpenRouter integration
- ✅ Pollinations.ai service
- ✅ MongoDB Atlas configuration
- ✅ Deployment configuration files
- ✅ This deployment guide

---

### **Step 2: Create Vercel Account** 🔐

1. Go to https://vercel.com/signup
2. Sign up with your GitHub account
3. Authorize Vercel to access your repositories

---

### **Step 3: Import Project to Vercel** 📦

1. **Go to Vercel Dashboard:** https://vercel.com/new
2. **Click "Import Project"**
3. **Select GitHub repository:** `varununjiya/AI-LISTING-STUDIO`
4. **Configure Project:**
   - Framework Preset: `Other` (we have custom config)
   - Root Directory: `./` (leave as root)
   - Build Command: Will auto-detect from vercel.json
   - Output Directory: `frontend/build`

5. **Click "Deploy"** (Don't add environment variables yet)

---

### **Step 4: Configure Environment Variables** 🔑

After first deployment, add these environment variables in Vercel:

**Go to:** Vercel Dashboard → Your Project → Settings → Environment Variables

**Add these variables:**

```bash
# MongoDB Atlas
MONGO_URL=mongodb+srv://varun:Varun%40db123@cluster0.4zhnyai.mongodb.net/?appName=Cluster0
DB_NAME=ai_listing_studio

# OpenRouter API Key
OPENROUTER_API_KEY_1=YOUR_OPENROUTER_API_KEY_HERE

# Image Generation Service
IMAGE_GENERATION_SERVICE=pollinations
POLLINATIONS_API_URL=https://image.pollinations.ai/prompt/

# AI Model Configuration (Optional - defaults work fine)
MODEL_LISTING_GENERATION=deepseek/deepseek-chat
MODEL_SEO_GENERATION=qwen/qwen-2.5-72b-instruct
MODEL_GRAMMAR_CHECK=anthropic/claude-3.5-sonnet
MODEL_VISION_ANALYSIS=qwen/qwen2-vl-72b-instruct
MODEL_IMAGE_GENERATION=gemini-3.1-flash-image-preview

# CORS Configuration
CORS_ORIGINS=*
```

**Important:** Set each variable for **Production**, **Preview**, and **Development** environments.

---

### **Step 5: Add Frontend Environment Variable** 🌐

The frontend needs to know the backend URL.

**In Vercel Dashboard → Environment Variables, add:**

```bash
REACT_APP_BACKEND_URL=https://your-project-name.vercel.app
```

**Note:** Replace `your-project-name` with your actual Vercel project name (you'll see it after first deployment).

**Example:**
```bash
REACT_APP_BACKEND_URL=https://ai-listing-studio.vercel.app
```

---

### **Step 6: Redeploy** 🔄

After adding environment variables:

1. Go to **Deployments** tab
2. Find the latest deployment
3. Click the **3 dots** menu
4. Click **"Redeploy"**
5. Check **"Use existing Build Cache"**
6. Click **"Redeploy"**

---

### **Step 7: Update Frontend .env (Optional)** 📝

If you want to update the frontend .env for local development:

**File:** `/app/frontend/.env`

```bash
REACT_APP_BACKEND_URL=https://your-project-name.vercel.app
WDS_SOCKET_PORT=443
ENABLE_HEALTH_CHECK=false
```

Then push to GitHub again using "Save to GitHub" and Vercel will auto-deploy.

---

## 🎯 VERCEL-SPECIFIC CONFIGURATIONS

### **vercel.json** (Already Created ✅)

Located at `/app/vercel.json`:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "frontend/package.json",
      "use": "@vercel/static-build",
      "config": { "distDir": "build" }
    },
    {
      "src": "backend/server.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "backend/server.py"
    },
    {
      "src": "/(.*)",
      "dest": "frontend/$1"
    }
  ],
  "env": {
    "NODE_VERSION": "18"
  },
  "regions": ["iad1"]
}
```

**What this does:**
- Builds React frontend
- Deploys FastAPI backend as serverless function
- Routes `/api/*` to backend
- Routes everything else to frontend

---

### **Backend API Wrapper** (Already Created ✅)

Located at `/app/backend/api/index.py`:

```python
from server import app
handler = app
```

This wraps your FastAPI app for Vercel serverless.

---

## 🔍 VERIFY DEPLOYMENT

### **Check Frontend:**
Visit: `https://your-project-name.vercel.app`

You should see the AI Listing Studio landing page.

### **Check Backend API:**
Visit: `https://your-project-name.vercel.app/api/`

You should see:
```json
{
  "message": "AI Ecommerce Content Studio API",
  "status": "ok"
}
```

### **Test Full Flow:**
1. Create account / Login
2. Add a product
3. Generate listing
4. Generate images with AI Image Studio
5. Export listings

---

## 🐛 TROUBLESHOOTING

### **Issue 1: Backend not responding (502 Error)**

**Solution:**
1. Check Vercel Functions logs (Dashboard → Functions)
2. Verify all environment variables are set
3. Ensure `MONGO_URL` is correctly URL-encoded
4. Check Python dependencies in `requirements.txt`

### **Issue 2: Frontend not loading backend**

**Solution:**
1. Verify `REACT_APP_BACKEND_URL` points to correct Vercel URL
2. Check browser console for CORS errors
3. Ensure `CORS_ORIGINS=*` is set in backend env vars
4. Redeploy after fixing

### **Issue 3: MongoDB connection failed**

**Solution:**
1. Check MongoDB Atlas IP whitelist (allow 0.0.0.0/0 for Vercel)
2. Verify `MONGO_URL` password is URL-encoded (`@` → `%40`)
3. Test connection in MongoDB Atlas console

### **Issue 4: OpenRouter API errors**

**Solution:**
1. Verify API key is correct
2. Check OpenRouter dashboard for credits
3. Ensure key starts with `sk-or-v1-`
4. Check backend logs in Vercel

### **Issue 5: Images not generating**

**Solution:**
1. Pollinations.ai is FREE and needs no API key
2. Check if `IMAGE_GENERATION_SERVICE=pollinations` is set
3. Check backend logs for errors
4. Test Pollinations directly: https://image.pollinations.ai/prompt/test

---

## 📊 MONITORING & ANALYTICS

### **Vercel Analytics:**
1. Go to Vercel Dashboard → Analytics
2. Enable Web Analytics (free)
3. Monitor traffic and performance

### **Function Logs:**
1. Dashboard → Functions
2. View real-time logs
3. Debug errors

### **MongoDB Atlas Monitoring:**
1. Login to MongoDB Atlas
2. Go to Clusters → Metrics
3. Monitor database operations

### **OpenRouter Usage:**
1. Visit https://openrouter.ai/
2. Check usage and costs
3. Monitor API key activity

---

## 🔐 SECURITY RECOMMENDATIONS

### **1. MongoDB Atlas:**
- ✅ Already using authentication
- ⚠️ **Recommended:** Add IP whitelist for Vercel
  - Get Vercel IPs: https://vercel.com/docs/concepts/functions/serverless-functions/regions
  - Add to MongoDB Atlas → Network Access

### **2. API Keys:**
- ✅ Stored in Vercel environment variables (secure)
- ✅ Not exposed to frontend
- ✅ Not in git repository

### **3. CORS:**
- Current: `CORS_ORIGINS=*` (allows all)
- **Production:** Change to your domain only:
  ```bash
  CORS_ORIGINS=https://your-project-name.vercel.app
  ```

### **4. Rate Limiting:**
- Consider adding rate limiting for API endpoints
- Vercel Pro plan includes DDoS protection

---

## 💰 COST ESTIMATE

### **Vercel Free Tier Limits:**
- ✅ 100 GB bandwidth/month
- ✅ 100 GB-hours serverless function execution
- ✅ 6,000 build minutes/month
- ✅ Unlimited websites and APIs

**Your usage:**
- Typical: Well within free tier
- If exceeded: ~$20/month for Pro plan

### **MongoDB Atlas:**
- Free tier: 512 MB (good for 1000s of products)
- Paid: ~$9/month if needed

### **OpenRouter:**
- $1-20/month depending on usage
- Very affordable

### **Pollinations.ai:**
- FREE forever

**Total: $1-30/month** (mostly free!)

---

## 🎉 AUTOMATIC DEPLOYMENTS

After initial setup, every push to `master` branch will:
1. ✅ Automatically trigger new deployment
2. ✅ Build frontend
3. ✅ Deploy backend
4. ✅ Update live site
5. ✅ Generate deployment preview

**No manual work needed!**

---

## 📚 USEFUL LINKS

- **Your GitHub Repo:** https://github.com/varununjiya/AI-LISTING-STUDIO
- **Vercel Dashboard:** https://vercel.com/dashboard
- **Vercel Docs:** https://vercel.com/docs
- **MongoDB Atlas:** https://cloud.mongodb.com/
- **OpenRouter Dashboard:** https://openrouter.ai/
- **Pollinations.ai:** https://pollinations.ai/

---

## 📞 SUPPORT

If you encounter any issues:

1. Check Vercel Function logs
2. Check browser console (F12)
3. Review this troubleshooting section
4. Check MongoDB Atlas connection
5. Verify environment variables

---

## ✅ DEPLOYMENT CHECKLIST

Before going live:

- [ ] Code pushed to GitHub (master branch)
- [ ] Vercel account created
- [ ] Project imported to Vercel
- [ ] All environment variables added
- [ ] Frontend and backend deployed
- [ ] MongoDB Atlas connected
- [ ] OpenRouter API key working
- [ ] Test login/signup
- [ ] Test product creation
- [ ] Test listing generation
- [ ] Test image generation
- [ ] Test exports
- [ ] Custom domain configured (optional)

---

**Ready to Deploy? Follow Step 1 above!** 🚀

**Estimated deployment time: 10-15 minutes**

---

Last Updated: $(date)
Version: 1.0 (Vercel Deployment Guide)
