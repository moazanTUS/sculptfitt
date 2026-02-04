# GitHub Secrets Setup Guide

## Required Secrets for GitHub Actions

To run automated tests, you need to add these secrets to your GitHub repository:

### How to Add Secrets

1. Go to your GitHub repository
2. Click **Settings** tab
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Add each secret below

---

## Secrets to Add

### 1. GEMINI_API_KEY
- **Name:** `GEMINI_API_KEY`
- **Value:** Your Google Gemini API key
- **Where to get it:** https://aistudio.google.com/app/apikey

### 2. CLERK_SECRET_KEY  
- **Name:** `CLERK_SECRET_KEY`
- **Value:** Your Clerk secret key
- **Where to get it:** 
  - Go to https://dashboard.clerk.com
  - Select your application
  - Go to **API Keys**
  - Copy the **Secret Key** (starts with `sk_test_` or `sk_live_`)

### 3. DB_HOST
- **Name:** `DB_HOST`
- **Value:** Your database host (e.g., `containers-us-west-123.railway.app`)
- **Where to get it:** From your Railway/database provider

### 4. DB_USER
- **Name:** `DB_USER`
- **Value:** Your database username (e.g., `root`)

### 5. DB_PASS
- **Name:** `DB_PASS`
- **Value:** Your database password

### 6. DB_NAME
- **Name:** `DB_NAME`
- **Value:** Your database name (e.g., `sculpfit`)

### 7. DB_PORT
- **Name:** `DB_PORT`
- **Value:** Your database port (e.g., `3306`)

---

## Summary: All Secrets Needed

Add these **7 secrets** to GitHub:
1. `GEMINI_API_KEY` - AI API key
2. `CLERK_SECRET_KEY` - Authentication key
3. `DB_HOST` - Database host
4. `DB_USER` - Database username
5. `DB_PASS` - Database password
6. `DB_NAME` - Database name
7. `DB_PORT` - Database port

---

## Verify Setup

After adding secrets:

1. Go to **Actions** tab
2. Click **"Re-run all jobs"** on latest workflow run
3. If secrets are correct, tests will pass ✅
4. If missing, you'll see errors about missing API keys

---

## Security Notes

- ✅ Secrets are encrypted and never exposed in logs
- ✅ Only repository collaborators can manage secrets
- ✅ Secrets are only available to GitHub Actions
- ✅ Never commit `.env` file to repository
- ✅ Use `.env.example` as template only

---

## For Production Deployment

When deploying to Railway/Heroku/other platforms, add the same variables there:

**Railway:**
```
Variables tab → Add these:
- GEMINI_API_KEY
- CLERK_SECRET_KEY
- DB_HOST
- DB_USER
- DB_PASS
- DB_NAME
- DB_PORT
- ALLOWED_ORIGINS
```

**Heroku:**
```bash
heroku config:set GEMINI_API_KEY=your_key_here
heroku config:set CLERK_SECRET_KEY=your_key_here
# ... etc
```

---

## Testing Secrets Locally

Create a `.env` file (already in `.gitignore`):

```bash
cp .env.example .env
# Edit .env with your actual values
```

**NEVER commit the `.env` file!**

---

## Troubleshooting

### Tests fail with "API key not found"
→ Add the missing secret in GitHub repository settings

### Tests fail with "Database connection error"  
→ GitHub Actions should handle this automatically
→ Check the workflow file has MySQL service configured

### Secrets not updating
→ Edit the secret in repository settings
→ Re-run the workflow

---

## Summary Checklist

- [ ] Add `GEMINI_API_KEY` to GitHub Secrets
- [ ] Add `CLERK_SECRET_KEY` to GitHub Secrets
- [ ] Verify `.env` is in `.gitignore`
- [ ] Never commit actual API keys to repository
- [ ] Push code and check Actions tab for test results
