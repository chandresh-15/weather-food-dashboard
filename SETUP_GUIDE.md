# 🌦️ Weather & Food Cravings — Live Dashboard Setup Guide

## Overview

```
Google Form → Google Sheet → Streamlit App (auto-refreshes every 30s)
```

---

## STEP 1 — Link Your Google Form to a Sheet

1. Open your **Google Form**
2. Click the **Responses** tab
3. Click the **green Sheets icon** → "Create a new spreadsheet"
4. Name it (e.g. `Weather Food Cravings Responses`)
5. Click **Create** — responses now auto-flow into this sheet

---

## STEP 2 — Enable Google Sheets API

1. Go to → **https://console.cloud.google.com/**
2. Create a new project (or select existing)
3. In the left menu → **APIs & Services → Library**
4. Search **"Google Sheets API"** → Enable it
5. Search **"Google Drive API"** → Enable it

---

## STEP 3 — Create a Service Account

1. Go to → **APIs & Services → Credentials**
2. Click **"+ Create Credentials"** → **Service Account**
3. Fill in:
   - Name: `survey-dashboard`
   - Role: `Editor` (or `Viewer` for read-only)
4. Click **Done**
5. Click on the service account you just created
6. Go to **Keys** tab → **Add Key → Create new key → JSON**
7. A `credentials.json` file downloads — **keep this safe!**

---

## STEP 4 — Share Your Sheet with the Service Account

1. Open `credentials.json` and copy the `client_email` value
   - Looks like: `survey-dashboard@your-project.iam.gserviceaccount.com`
2. Open your **Google Sheet**
3. Click **Share** (top right)
4. Paste the service account email
5. Set permission to **Viewer** → click **Share**

---

## STEP 5 — Set Up the App Locally

```bash
# 1. Create and enter the project folder
mkdir weather_food_dashboard && cd weather_food_dashboard

# 2. Copy your app files here
#    app.py, requirements.txt, .gitignore

# 3. Place credentials.json in the folder
#    (downloaded in Step 3)

# 4. Create virtual environment
python -m venv venv
source venv/bin/activate       # Mac/Linux
venv\Scripts\activate          # Windows

# 5. Install dependencies
pip install -r requirements.txt

# 6. Run the app
streamlit run app.py
```

The app opens at **http://localhost:8501**

Paste your Google Sheet URL in the sidebar and you're live! 🎉

---

## STEP 6 — Deploy to Streamlit Cloud (Free Hosting)

### 6a. Push to GitHub

```bash
git init
git add app.py requirements.txt .gitignore
# DO NOT add credentials.json or secrets.toml
git commit -m "Initial dashboard"
git remote add origin https://github.com/chandresh-15/weather-food-dashboard.git
git push -u origin main
```

### 6b. Deploy on Streamlit Cloud

1. Go to → **https://share.streamlit.io/**
2. Sign in with GitHub
3. Click **"New app"**
4. Select your repo, branch `main`, file `app.py`
5. Click **"Advanced settings"** → **Secrets**
6. Paste the contents of your `credentials.json` in this format:

```toml
[gcp_service_account]
type                        = "service_account"
project_id                  = "your-project-id"
private_key_id              = "abc123..."
private_key                 = "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----\n"
client_email                = "survey-dashboard@your-project.iam.gserviceaccount.com"
client_id                   = "123456789"
auth_uri                    = "https://accounts.google.com/o/oauth2/auth"
token_uri                   = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url        = "https://www.googleapis.com/robot/v1/metadata/x509/..."
```

7. Click **Deploy** — you get a public URL like:
   `https://your-app-name.streamlit.app`

---

## How Auto-Refresh Works

```python
# In app.py — this is the key mechanism:

@st.cache_data(ttl=30)   # Cache expires every 30 seconds
def load_data(sheet_url):
    ...fetch from Google Sheet...

# At the bottom of app.py:
time.sleep(refresh_interval)
st.cache_data.clear()
st.rerun()           # Forces Streamlit to re-run the whole script
```

Every time Streamlit re-runs, it fetches fresh data from the Sheet.
New form submissions appear within 30 seconds automatically.

---

## File Structure

```
weather_food_dashboard/
├── app.py                  ← Main Streamlit app
├── requirements.txt        ← Python dependencies
├── .gitignore              ← Excludes credentials from Git
├── credentials.json        ← ⚠️ LOCAL ONLY — never commit!
└── .streamlit/
    └── secrets.toml        ← ⚠️ LOCAL ONLY — never commit!
```

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| `gspread.exceptions.APIError: PERMISSION_DENIED` | Share the Sheet with your service account email |
| `No credentials found` | Put `credentials.json` in the app folder |
| `KeyError: column name` | Check your Form column names match the rename list in `app.py` |
| App doesn't refresh | Click "Force Refresh Now" in the sidebar |
| Streamlit Cloud: secrets error | Double-check the TOML format — especially `private_key` newlines |

---

## Column Name Mapping

The app renames your Form columns to short names.
If your Form questions differ, update this in `app.py`:

```python
df.columns = [
    "timestamp",             # Timestamp (auto)
    "age_group",             # What is your age group?
    "role",                  # What best describes you?
    "order_freq",            # How often do you order per week?
    "craving_freq",          # How often do cravings change with weather?
    "rainy_cuisine",         # Rainy day cuisine (multi-select)
    "rainy_fav",             # Favorite food for rainy weather
    "cold_cuisine",          # Cold day cuisine (multi-select)
    "cold_fav",              # Favorite food for cold weather
    "hot_cuisine",           # Hot day cuisine (multi-select)
    "hot_fav",               # Favorite food for hot weather
    "weather_change_behavior", # Sudden weather change behavior
    "bad_weather_order",     # Order frequency in bad weather
    "weather_influence",     # Open-ended: weather influence
]
```
