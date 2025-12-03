# 🚀 VigilAI with Google Gemini - Quick Setup

## ✅ Changes Made

Replaced OpenAI and Anthropic with **Google Gemini** (100% FREE tier available!)

---

## 📝 How to Get Google Gemini API Key (FREE)

1. **Go to Google AI Studio**:
   - Visit: https://makersuite.google.com/app/apikey
   - OR: https://aistudio.google.com/app/apikey

2. **Sign in** with your Google account

3. **Click "Create API Key"**

4. **Copy the key** (starts with `AIza...`)

5. **Free Tier Limits**:
   - ✅ 60 requests per minute
   - ✅ 1,500 requests per day
   - ✅ No credit card required
   - ✅ Perfect for development and testing

---

## 🔧 Setup Steps

### 1. Create `.env` file:

```powershell
Copy-Item .env.example .env
```

### 2. Edit `.env` and add your key:

```env
# Required - Get from https://makersuite.google.com/app/apikey
GOOGLE_API_KEY=AIzaSy...your_actual_key_here

# Generate random secret
JWT_SECRET=your_random_32_character_string_here

# Database (keep as-is for Docker)
DATABASE_URL=postgresql://vigilai:vigilai_password@postgres:5432/vigilai
REDIS_URL=redis://redis:6379/0

# Optional (can leave empty)
PERPLEXITY_API_KEY=
NOTION_API_KEY=
SLACK_BOT_TOKEN=
```

### 3. Generate JWT Secret:

```powershell
-join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | % {[char]$_})
```

Copy the output and paste it as `JWT_SECRET` in `.env`

### 4. Install dependencies:

```powershell
# Update backend dependencies
cd backend
pip install google-generativeai==0.3.2

# OR rebuild Docker containers
cd ..
docker-compose down
docker-compose build
```

### 5. Start the application:

```powershell
docker-compose up -d
```

### 6. Verify it's working:

```powershell
docker-compose logs backend | Select-String "Gemini"
```

---

## 🎯 What Works with Gemini

✅ **Competitor analysis** - Detects meaningful changes  
✅ **Battlecard generation** - Auto-creates competitive intelligence  
✅ **Impact scoring** - Rates changes 0-10  
✅ **Hiring trend analysis** - Identifies strategic shifts  
✅ **Content summarization** - Analyzes blog posts/news  
✅ **Noise filtering** - Ignores cosmetic changes  

---

## 🆚 Gemini vs OpenAI/Claude

| Feature | Google Gemini | OpenAI GPT-4 | Anthropic Claude |
|---------|---------------|--------------|------------------|
| **Free Tier** | ✅ 1,500 req/day | ❌ $5 credits only | ❌ Limited trial |
| **Cost** | FREE | $0.01/1K tokens | $0.015/1K tokens |
| **Speed** | Fast | Medium | Fast |
| **Quality** | Excellent | Excellent | Excellent |
| **Best For** | Development, Testing | Production | Long contexts |

---

## 🐛 Troubleshooting

### "API key not found" error:

```powershell
# Check if .env exists
Test-Path .env

# Verify GOOGLE_API_KEY is set
Get-Content .env | Select-String "GOOGLE_API_KEY"
```

### "Rate limit exceeded":

- Free tier: 60 requests/min, 1,500/day
- Reduce scraping frequency
- Or upgrade to paid plan ($0.00035/1K tokens)

### Test the API key:

```python
import google.generativeai as genai

genai.configure(api_key="YOUR_KEY_HERE")
model = genai.GenerativeModel('gemini-pro')
response = model.generate_content("Hello, Gemini!")
print(response.text)
```

---

## 📊 Access Your App

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/docs
- **N8N Workflows**: http://localhost:5678

---

## 💡 Pro Tips

1. **Monitor usage**: https://makersuite.google.com/app/apikey (shows your quota)
2. **Upgrade if needed**: Pay-as-you-go is very cheap ($0.00035/1K tokens)
3. **Test with small competitors first**: Saves API quota
4. **Cache results**: VigilAI uses Redis to avoid duplicate API calls

---

## 🎉 You're Ready!

```powershell
# Quick start
docker-compose up -d

# View logs
docker-compose logs -f backend

# Open frontend
start http://localhost:3000
```

**Happy competitive intelligence gathering! 🕵️**
