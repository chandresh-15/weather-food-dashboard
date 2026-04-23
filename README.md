# 🌦️ Weather & Food Cravings — Live Dashboard

A real-time Streamlit dashboard that visualizes survey responses about how weather influences food cravings. Responses flow automatically from a Google Form → Google Sheet → Live Dashboard, refreshing every 30 seconds.

---

## 📐 Architecture

```
Google Form → Google Sheet → Streamlit App (auto-refreshes every 30s)
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- A Google account
- A Google Cloud project with Sheets & Drive APIs enabled

### Local Setup

```bash
# 1. Clone the repo
git clone https://github.com/chandresh-15/weather-food-dashboard.git
cd weather-food-dashboard

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate       # Mac/Linux
venv\Scripts\activate          # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your credentials.json (see Configuration below)

# 5. Run the app
streamlit run app.py
```

The app opens at **http://localhost:8501** — paste your Google Sheet URL in the sidebar and you're live! 🎉

---

## ⚙️ Configuration

### Step 1 — Link Google Form to a Sheet

1. Open your **Google Form** → click the **Responses** tab
2. Click the **green Sheets icon** → "Create a new spreadsheet"
3. Name it (e.g. `Weather Food Cravings Responses`) → click **Create**

Responses will now auto-flow into the sheet.

### Step 2 — Enable Google APIs

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create or select a project
3. Navigate to **APIs & Services → Library**
4. Search and enable both:
   - **Google Sheets API**
   - **Google Drive API**

### Step 3 — Create a Service Account

1. Go to **APIs & Services → Credentials**
2. Click **"+ Create Credentials" → Service Account**
3. Set Name: `survey-dashboard`, Role: `Editor` (or `Viewer` for read-only)
4. Under the **Keys** tab → **Add Key → Create new key → JSON**
5. Save the downloaded `credentials.json` — **keep this file safe and never commit it!**

### Step 4 — Share Your Sheet

1. Open `credentials.json` and copy the `client_email` value
   (looks like `survey-dashboard@your-project.iam.gserviceaccount.com`)
2. Open your Google Sheet → click **Share**
3. Paste the service account email, set permission to **Viewer**, and confirm

---

## 📁 File Structure

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

## ☁️ Deploying to Streamlit Cloud (Free)

### 1. Push to GitHub

```bash
git init
git add app.py requirements.txt .gitignore
# ⚠️ Do NOT add credentials.json or secrets.toml
git commit -m "Initial dashboard"
git remote add origin https://github.com/chandresh-15/weather-food-dashboard.git
git push -u origin main
```

### 2. Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io/) and sign in with GitHub
2. Click **"New app"** → select your repo, branch `main`, file `app.py`
3. Click **"Advanced settings" → Secrets** and paste your `credentials.json` contents in TOML format:

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

4. Click **Deploy** — your app goes live at `https://your-app-name.streamlit.app`

---

## 🔄 How Auto-Refresh Works

```python
# Cache expires every 30 seconds, then fresh data is fetched
@st.cache_data(ttl=30)
def load_data(sheet_url):
    ...fetch from Google Sheet...

# Forces Streamlit to re-run the whole script
time.sleep(refresh_interval)
st.cache_data.clear()
st.rerun()
```

New form submissions appear in the dashboard within 30 seconds automatically.

---

## 🗂️ Column Name Mapping

The app renames Google Form columns to short internal names. If your Form questions differ, update this block in `app.py`:

```python
df.columns = [
    "timestamp",               # Timestamp (auto)
    "age_group",               # What is your age group?
    "role",                    # What best describes you?
    "order_freq",              # How often do you order per week?
    "craving_freq",            # How often do cravings change with weather?
    "rainy_cuisine",           # Rainy day cuisine (multi-select)
    "rainy_fav",               # Favorite food for rainy weather
    "cold_cuisine",            # Cold day cuisine (multi-select)
    "cold_fav",                # Favorite food for cold weather
    "hot_cuisine",             # Hot day cuisine (multi-select)
    "hot_fav",                 # Favorite food for hot weather
    "weather_change_behavior", # Sudden weather change behavior
    "bad_weather_order",       # Order frequency in bad weather
    "weather_influence",       # Open-ended: weather influence
]
```

---

## 🛠️ Troubleshooting

| Error | Fix |
|-------|-----|
| `gspread.exceptions.APIError: PERMISSION_DENIED` | Share the Sheet with your service account email |
| `No credentials found` | Place `credentials.json` in the project root folder |
| `KeyError: column name` | Ensure Form column names match the rename list in `app.py` |
| App doesn't refresh | Click **"Force Refresh Now"** in the sidebar |
| Streamlit Cloud: secrets error | Double-check TOML format — especially `private_key` newlines |

---

## 📄 License

This project is for academic and portfolio purposes.
