# Step-by-Step: Deploy SeenSlide Cloud to Railway

**Time Required:** 5-10 minutes
**Cost:** $0-5/month (free tier available)

---

## Step 1: Prepare Railway Account

1. **Go to https://railway.app**
2. **Click "Login"**
3. **Sign in with GitHub**
4. Authorize Railway to access your GitHub account

✅ **You now have a Railway account!**

---

## Step 2: Create New Project

1. In Railway dashboard, click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. If prompted, authorize Railway to access your repositories
4. Find and select: **`phaysaal/seenslide`**
5. Railway will automatically:
   - Detect Python application
   - Read `Procfile` and `railway.json`
   - Install dependencies from `requirements-cloud.txt`
   - Start the server

---

## Step 3: Wait for Deployment

**Watch the logs in Railway dashboard:**

You'll see:
```
Building...
Installing dependencies...
Starting server...
✓ Deployment successful
```

**This takes 2-3 minutes.**

---

## Step 4: Generate Public URL

1. Click on your deployment in Railway dashboard
2. Go to **"Settings"** tab (left sidebar)
3. Scroll to **"Networking"** section
4. Click **"Generate Domain"**

Railway will create a public URL like:
```
https://seenslide-production-a1b2.up.railway.app
```

**Copy this URL!** You'll need it for testing.

---

## Step 5: Test Your Deployment

### Option A: Quick Browser Test

Open in browser:
```
https://your-app.up.railway.app/health
```

You should see:
```json
{
  "status": "healthy",
  "stats": {
    "active_sessions": 0,
    "total_slides": 0,
    "total_viewers": 0
  }
}
```

### Option B: Command Line Test

```bash
# Set your Railway URL
export CLOUD_URL="https://your-app.up.railway.app"

# Test health
curl $CLOUD_URL/health

# Create a test session
curl -X POST $CLOUD_URL/api/cloud/session/create \
  -H "Content-Type: application/json" \
  -d '{"presenter_name": "Test User", "max_slides": 50}'
```

**Expected Response:**
```json
{
  "session_id": "ABC-1234",
  "presenter_name": "Test User",
  "created_at": 1733740887.265,
  "status": "active",
  "total_slides": 0,
  "max_slides": 50,
  "viewer_count": 0
}
```

### Option C: Full Test Suite

```bash
cd /home/faisal/code/hobby/SeenSlide
source venv/bin/activate
python test_cloud_phase1.py --url https://your-app.up.railway.app
```

**Expected:**
```
✓ ALL TESTS PASSED!
```

---

## Step 6: Configure Cost Cap (Important!)

**Prevent surprise charges:**

1. In Railway dashboard, go to **"Settings"**
2. Find **"Usage Limits"**
3. Set **"Spending Limit"**: **$5.00**
4. Check **"Hard limit"** option
5. Click **"Save"**

Railway will stop your service if it hits $5/month.

**Free Tier:**
- $5 credit/month (covers typical usage)
- Auto-sleep after 30 min inactivity
- Wakes automatically on request

---

## Step 7: Add Persistent Storage (Optional)

By default, the database is stored in `/tmp/` which resets on redeploy.

**To persist data:**

1. In Railway, click **"Settings"** → **"Volumes"**
2. Click **"Add Volume"**
3. Configure:
   - **Mount Path:** `/data`
   - **Size:** 1 GB
4. Click **"Add"**

5. Add environment variable:
   - Go to **"Variables"** tab
   - Click **"+ New Variable"**
   - **Name:** `SEENSLIDE_DB_PATH`
   - **Value:** `/data/seenslide_cloud.db`
   - Click **"Add"**

6. Railway will automatically redeploy

---

## Step 8: Save Your Configuration

**Create a file to save your deployment info:**

```bash
# In your project
cat > deploy/my_deployment.txt <<EOF
Railway URL: https://your-app.up.railway.app
Deployed: $(date)
Session Management: ✅ Active
Cost Cap: $5/month
Database: /data/seenslide_cloud.db (persistent)
EOF
```

---

## Verification Checklist

- [ ] Railway deployment successful
- [ ] Public URL generated
- [ ] Health endpoint responds
- [ ] Can create test session
- [ ] Session ID format correct (ABC-1234)
- [ ] Cost cap set to $5/month
- [ ] (Optional) Persistent volume added

---

## Next Steps

### 1. Use in Local App

When configuring your local SeenSlide app:
- **Cloud URL:** Your Railway URL
- **Mode:** Cloud + Local fallback

### 2. Monitor Usage

**Railway Dashboard:**
- View logs: **Deployments** tab
- Check usage: **Metrics** tab
- Current cost: **Usage** section

### 3. Proceed to Phase 2

Ready to implement:
- Slide upload from local app
- Slide download for viewers
- Real-time WebSocket updates

---

## Troubleshooting

### Build Failed

**Check Railway logs:**
1. Go to **Deployments** tab
2. Click failed deployment
3. Review error messages

**Common issues:**
- Missing dependencies → Check `requirements-cloud.txt`
- Python version → Check `runtime.txt`
- Syntax errors → Review recent commits

### Server Not Starting

**Check logs for errors:**
```
Railway Dashboard → Deployments → Logs
```

**Common issues:**
- Port binding → Railway sets `PORT` env var automatically
- Database permissions → Use `/tmp/` or add volume
- Import errors → Verify all modules committed

### URL Not Working

**Verify:**
1. Domain generated in Railway Settings
2. Health endpoint: `https://your-url/health`
3. Check Railway logs for errors

### Rate Limiting

If you see "Rate limit exceeded":
- Wait 1 minute
- Or adjust limits in `modules/cloud/security.py`
- Redeploy after changes

---

## Railway Dashboard Overview

### Tabs

**Deployments**
- Build logs
- Runtime logs
- Deployment history
- Manual redeploy

**Metrics**
- CPU usage
- Memory usage
- Network traffic
- Request count

**Settings**
- Environment variables
- Volumes (persistent storage)
- Networking (domains)
- Build configuration

**Variables**
- Add custom env vars
- Configure secrets
- Database URLs

---

## Auto-Deployment

Railway automatically redeploys when you push to GitHub:

```bash
# Make changes
git add .
git commit -m "Update cloud server"
git push origin main

# Railway detects push and redeploys automatically
```

---

## Manual Redeployment

If you need to manually redeploy:

1. Go to **Deployments** tab
2. Click **"..."** menu on latest deployment
3. Click **"Redeploy"**

---

## Cost Monitoring

**View current costs:**
1. Railway Dashboard → **Usage**
2. See charges per service
3. Projected monthly cost

**Typical costs:**
- Light usage (10-20 sessions/day): $1-2/month
- Medium usage (50-100 sessions/day): $3-4/month
- Heavy usage: Up to free tier cap ($5/month)

---

## Getting Help

**Railway Support:**
- Docs: https://docs.railway.app
- Discord: https://discord.gg/railway
- Status: https://status.railway.app

**SeenSlide Issues:**
- GitHub: https://github.com/phaysaal/seenslide/issues

---

## Security Notes

**Before Production Use:**
- [ ] Configure CORS for your domain
- [ ] Add admin authentication (Phase 8)
- [ ] Use custom domain with HTTPS
- [ ] Review rate limits
- [ ] Set up monitoring/alerts
- [ ] Regular security updates

---

**Congratulations!** Your SeenSlide Cloud Server is now live! 🎉

**Your URL:** `https://your-app.up.railway.app`

Save this URL for use in Phases 2-10.
