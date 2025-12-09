# Deploying SeenSlide Cloud Server to Railway

This guide will walk you through deploying the SeenSlide Cloud Server to Railway.app.

## Prerequisites

1. A GitHub account
2. A Railway account (free tier available)
3. Git installed locally

## Cost Information

**Railway Free Tier:**
- $5 in credits per month
- Enough for small to medium usage
- Automatic sleep after inactivity (wakes on request)
- Capped at $5 - **no surprise charges**

**Estimated Usage:**
- For typical presentation use: $0-3/month
- Well within free tier limits

## Step-by-Step Deployment

### Step 1: Prepare Your Repository

The repository already has all necessary files:
- ✅ `Procfile` - Tells Railway how to start the server
- ✅ `railway.json` - Railway configuration
- ✅ `runtime.txt` - Python version specification
- ✅ `requirements-cloud.txt` - Cloud-only dependencies
- ✅ `.railwayignore` - Files to exclude from deployment

### Step 2: Push to GitHub

If not already done:

```bash
# Initialize git (if needed)
cd /home/faisal/code/hobby/SeenSlide
git add .
git commit -m "Add Railway deployment configuration"
git push origin main
```

### Step 3: Deploy to Railway

1. **Go to Railway.app**
   - Visit https://railway.app
   - Click "Login" and sign in with GitHub

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Authorize Railway to access your GitHub
   - Select the `SeenSlide` repository

3. **Configure Deployment**
   Railway will automatically detect the Python app and use your configuration.

   - **Build Command:** Automatically detected
   - **Start Command:** From `Procfile`
   - **Health Check:** `/health` endpoint

4. **Add Environment Variables (Optional)**
   In the Railway dashboard:
   - Click on your deployment
   - Go to "Variables" tab
   - Add any custom variables (none required for basic deployment)

5. **Deploy**
   - Railway will automatically build and deploy
   - Wait 2-3 minutes for deployment to complete
   - You'll see logs in real-time

### Step 4: Get Your Deployment URL

Once deployed:
1. Go to your Railway project dashboard
2. Click on your deployment
3. Go to "Settings" → "Networking"
4. Click "Generate Domain"
5. You'll get a URL like: `https://seenslide-production-xxxx.up.railway.app`

**Save this URL!** You'll use it for testing and in your local app.

### Step 5: Test Your Deployment

Test the deployment with curl:

```bash
# Replace with your Railway URL
CLOUD_URL="https://your-app.up.railway.app"

# Test health endpoint
curl $CLOUD_URL/health

# Create a test session
curl -X POST $CLOUD_URL/api/cloud/session/create \
  -H "Content-Type: application/json" \
  -d '{"presenter_name": "Test User", "max_slides": 50}'

# You should get a session ID like: {"session_id": "ABC-1234", ...}
```

### Step 6: Test with the Test Script

Update the test script to use your Railway URL:

```bash
python test_cloud_phase1.py --url https://your-app.up.railway.app
```

## Railway Dashboard Features

### Logs
- View real-time logs in the "Deployments" tab
- Search and filter logs
- Download logs for debugging

### Metrics
- CPU usage
- Memory usage
- Network traffic
- Request counts

### Settings
- **Custom Domain:** Add your own domain
- **Environment Variables:** Configure settings
- **Build Settings:** Customize build process
- **Sleep Settings:** Configure auto-sleep behavior

## Monitoring Your Deployment

1. **Health Check:**
   ```bash
   curl https://your-app.up.railway.app/health
   ```

2. **Server Stats:**
   ```bash
   curl https://your-app.up.railway.app/api/cloud/stats
   ```

3. **Active Sessions:**
   ```bash
   curl https://your-app.up.railway.app/api/cloud/sessions
   ```

## Cost Management

### Free Tier Usage
Railway provides $5/month in credits. For SeenSlide:
- **Light usage:** 10-20 sessions/day = ~$1-2/month
- **Medium usage:** 50-100 sessions/day = ~$3-4/month
- **Auto-sleep** when inactive saves costs

### Cost Cap
1. Go to your Railway project
2. Click "Settings"
3. Scroll to "Usage Limits"
4. Set a spending cap (e.g., $5/month)
5. Railway will stop services if cap is reached (no surprise charges)

## Database Persistence

By default, the SQLite database is stored in `/tmp/` which is ephemeral. For production:

### Option 1: Railway Volume (Recommended)

1. Go to your Railway deployment
2. Click "Settings" → "Volumes"
3. Add a volume:
   - **Mount Path:** `/data`
   - **Size:** 1 GB
4. Update environment variable:
   ```
   SEENSLIDE_DB_PATH=/data/seenslide_cloud.db
   ```

### Option 2: External Database

For high-traffic production use, consider:
- Railway PostgreSQL addon
- External database service

## Troubleshooting

### Build Fails
- Check logs in Railway dashboard
- Verify `requirements-cloud.txt` has correct dependencies
- Check Python version in `runtime.txt`

### Server Won't Start
- Check logs for error messages
- Verify `Procfile` start command
- Check health endpoint: `/health`

### Rate Limiting Issues
- Adjust rate limits in `modules/cloud/security.py`
- Redeploy after changes

### Database Issues
- Add a persistent volume (see above)
- Check file permissions
- Verify `SEENSLIDE_DB_PATH` environment variable

## Updating Your Deployment

To deploy changes:

```bash
# Make your changes
git add .
git commit -m "Update cloud server"
git push origin main
```

Railway automatically redeploys on push to main branch.

## Alternative: Manual Deployment Check

If you want to verify before pushing to GitHub:

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link to project
railway link

# Deploy
railway up
```

## Security Checklist

Before production use:

- [ ] Set up persistent database storage
- [ ] Configure custom domain with HTTPS
- [ ] Review and adjust rate limits
- [ ] Add admin authentication (Phase 8)
- [ ] Configure CORS for your domain
- [ ] Set up monitoring/alerts
- [ ] Review logs regularly

## Next Steps

1. Deploy to Railway
2. Test with `test_cloud_phase1.py`
3. Share your Railway URL in the local app configuration
4. Proceed to Phase 2 (Slide Relay API)

---

**Need Help?**
- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Railway Status: https://status.railway.app
