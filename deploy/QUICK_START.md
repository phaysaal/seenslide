# Quick Start: Deploy to Railway in 5 Minutes

## Prerequisites
- GitHub account
- Railway account (sign up at https://railway.app)

## 1. Push to GitHub

```bash
cd /home/faisal/code/hobby/SeenSlide

# Add deployment files
git add Procfile railway.json runtime.txt requirements-cloud.txt .railwayignore
git add modules/cloud/
git add test_cloud_phase1.py
git add deploy/

# Commit
git commit -m "Add cloud server and Railway deployment"

# Push to GitHub
git push origin main
```

## 2. Deploy to Railway

1. **Go to https://railway.app**
2. **Login with GitHub**
3. **Click "New Project"**
4. **Select "Deploy from GitHub repo"**
5. **Choose `SeenSlide` repository**
6. **Wait 2-3 minutes** for deployment

## 3. Generate Domain

1. In Railway dashboard, click your deployment
2. Go to **Settings → Networking**
3. Click **"Generate Domain"**
4. Copy your URL (e.g., `https://seenslide-production-xxxx.up.railway.app`)

## 4. Test Your Deployment

```bash
# Replace with your Railway URL
export CLOUD_URL="https://your-app.up.railway.app"

# Test health
curl $CLOUD_URL/health

# Create a session
curl -X POST $CLOUD_URL/api/cloud/session/create \
  -H "Content-Type: application/json" \
  -d '{"presenter_name": "Test User", "max_slides": 50}'

# You'll get a session ID like: ABC-1234
```

## 5. Run Full Test Suite

```bash
python test_cloud_phase1.py --url $CLOUD_URL
```

## Done!

Your cloud server is now live and ready to use!

**Next Steps:**
- Save your Railway URL
- Proceed to Phase 2 (Slide upload/download)
- Configure local app to use cloud server

## Troubleshooting

### Build Failed?
- Check logs in Railway dashboard
- Verify all files are committed and pushed

### Server Not Responding?
- Check Railway logs for errors
- Verify domain was generated
- Test health endpoint: `curl https://your-url/health`

### Cost Concerns?
- Free tier: $5/month credit
- Set spending cap in Railway settings
- Typical usage: $1-3/month

## Support

Need help? Check:
- Railway Docs: https://docs.railway.app
- Full guide: `deploy/RAILWAY_DEPLOYMENT.md`
