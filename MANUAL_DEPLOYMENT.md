# 🚀 MANUAL DEPLOYMENT INSTRUCTIONS

## Step 1: Push Code to GitHub Manually

### 1.1 Check Git Status
```bash
cd /app
git status
```

### 1.2 Configure Git (if needed)
```bash
git config --global user.email "your-email@example.com"
git config --global user.name "Your Name"
```

### 1.3 Check Current Remote
```bash
git remote -v
```

### 1.4 If Remote Doesn't Exist, Add It
```bash
git remote add origin https://github.com/varununjiya/AI-LISTING-STUDIO.git
```

### 1.5 If Remote Exists But Wrong, Update It
```bash
git remote set-url origin https://github.com/varununjiya/AI-LISTING-STUDIO.git
```

### 1.6 Stage All Changes
```bash
git add .
```

### 1.7 Commit Changes
```bash
git commit -m "Add OpenRouter AI Engine, MongoDB Atlas, and Vercel deployment config"
```

### 1.8 Push to GitHub (master branch)
```bash
git push -u origin master
```

**If you get authentication error:**
You'll need a GitHub Personal Access Token:

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: `repo` (all)
4. Generate and copy the token
5. Use it as password when pushing:
   ```bash
   git push -u origin master
   # Username: varununjiya
   # Password: <paste your token here>
   ```

---

## Step 2: Deploy to Vercel

### 2.1 Create Vercel Account
1. Go to: https://vercel.com/signup
2. Click "Continue with GitHub"
3. Authorize Vercel

### 2.2 Import Project
1. Go to: https://vercel.com/new
2. Click "Import Git Repository"
3. Find: `varununjiya/AI-LISTING-STUDIO`
4. Click "Import"

### 2.3 Configure Project
**Framework Preset:** Other
**Root Directory:** ./ (leave default)
**Build Command:** (leave default, vercel.json handles it)
**Output Directory:** frontend/build
**Install Command:** (leave default)

**Click "Deploy"** (don't add env vars yet)

### 2.4 Add Environment Variables

After first deployment completes:

1. Go to your project in Vercel
2. Click "Settings" tab
3. Click "Environment Variables" in sidebar
4. Add each variable below:

**Add these one by one:**

```
Name: MONGO_URL
Value: mongodb+srv://varun:Varun%40db123@cluster0.4zhnyai.mongodb.net/?appName=Cluster0
Environments: ✓ Production ✓ Preview ✓ Development
```

```
Name: DB_NAME
Value: ai_listing_studio
Environments: ✓ Production ✓ Preview ✓ Development
```

```
Name: OPENROUTER_API_KEY_1
Value: YOUR_OPENROUTER_API_KEY_HERE
Environments: ✓ Production ✓ Preview ✓ Development
```

```
Name: IMAGE_GENERATION_SERVICE
Value: pollinations
Environments: ✓ Production ✓ Preview ✓ Development
```

```
Name: POLLINATIONS_API_URL
Value: https://image.pollinations.ai/prompt/
Environments: ✓ Production ✓ Preview ✓ Development
```

```
Name: MODEL_LISTING_GENERATION
Value: deepseek/deepseek-chat
Environments: ✓ Production ✓ Preview ✓ Development
```

```
Name: MODEL_SEO_GENERATION
Value: qwen/qwen-2.5-72b-instruct
Environments: ✓ Production ✓ Preview ✓ Development
```

```
Name: MODEL_GRAMMAR_CHECK
Value: anthropic/claude-3.5-sonnet
Environments: ✓ Production ✓ Preview ✓ Development
```

```
Name: MODEL_VISION_ANALYSIS
Value: qwen/qwen2-vl-72b-instruct
Environments: ✓ Production ✓ Preview ✓ Development
```

```
Name: CORS_ORIGINS
Value: *
Environments: ✓ Production ✓ Preview ✓ Development
```

**Frontend Environment Variable:**
```
Name: REACT_APP_BACKEND_URL
Value: https://YOUR-PROJECT-NAME.vercel.app
Environments: ✓ Production ✓ Preview ✓ Development
```

**IMPORTANT:** Replace `YOUR-PROJECT-NAME` with your actual Vercel project name (check the URL at top of Vercel dashboard)

### 2.5 Redeploy
1. Go to "Deployments" tab
2. Click the 3-dot menu on latest deployment
3. Click "Redeploy"
4. Check "Use existing Build Cache"
5. Click "Redeploy"

---

## Step 3: Test Deployment

### 3.1 Check Frontend
Visit: `https://your-project-name.vercel.app`

Should see landing page.

### 3.2 Check Backend API
Visit: `https://your-project-name.vercel.app/api/`

Should see:
```json
{
  "message": "AI Ecommerce Content Studio API",
  "status": "ok"
}
```

### 3.3 Full Test
1. Create account
2. Add product
3. Generate listing
4. Generate images
5. Export

---

## Troubleshooting

### Issue: Git push authentication failed

**Solution:**
```bash
# Use GitHub CLI (if installed)
gh auth login

# OR use Personal Access Token
# Generate at: https://github.com/settings/tokens
# Then use as password when pushing
```

### Issue: Vercel deployment fails

**Check:**
1. Vercel dashboard → Functions → View logs
2. Look for Python errors
3. Check if all environment variables are set
4. Ensure requirements.txt is in backend folder

### Issue: 502 Bad Gateway on /api/

**Solution:**
1. Check environment variables are set correctly
2. Check MongoDB URL is URL-encoded
3. View Vercel function logs
4. Ensure backend/server.py exists

### Issue: Frontend can't reach backend

**Solution:**
1. Update `REACT_APP_BACKEND_URL` with correct Vercel URL
2. Check CORS_ORIGINS is set to `*`
3. Redeploy after fixing

---

## Quick Reference

### Git Commands
```bash
cd /app
git status                  # Check status
git add .                   # Stage all changes
git commit -m "message"     # Commit
git push origin master      # Push to GitHub
```

### Check Deployment
```bash
# Frontend
curl https://your-project-name.vercel.app

# Backend
curl https://your-project-name.vercel.app/api/
```

---

## What Gets Deployed

**Frontend (React):**
- Landing page
- Dashboard
- Product management
- AI Image Studio
- All UI components

**Backend (FastAPI):**
- All API endpoints
- OpenRouter integration
- Pollinations.ai integration
- MongoDB Atlas connection
- Authentication

---

## After Successful Deployment

1. ✅ Test all features
2. ✅ Set up custom domain (optional)
3. ✅ Enable Vercel Analytics
4. ✅ Monitor MongoDB usage
5. ✅ Check OpenRouter credits

---

## Important URLs

- **Your GitHub:** https://github.com/varununjiya/AI-LISTING-STUDIO
- **Vercel Dashboard:** https://vercel.com/dashboard
- **MongoDB Atlas:** https://cloud.mongodb.com/
- **OpenRouter:** https://openrouter.ai/
- **GitHub Tokens:** https://github.com/settings/tokens

---

Last Updated: $(date)
