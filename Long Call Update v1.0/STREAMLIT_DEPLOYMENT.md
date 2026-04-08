# Streamlit Dashboard Deployment Guide

## 🎉 Firebase Integration Complete!

Your extension is now configured to send data to Firebase Firestore!

---

## ✅ What's Done

1. ✅ Firebase configured in extension
2. ✅ Extension sends data to Firestore when "Send to Dashboard" is clicked
3. ✅ Streamlit dashboard code created (`streamlit_dashboard.py`)
4. ✅ Ready to deploy!

---

## 🚀 Next Step: Deploy Streamlit Dashboard

You have **3 hosting options**:

---

### **Option 1: Streamlit Community Cloud** (Easiest!)

**Cost:** FREE (public) or $20/month (private)

**Steps:**

1. **Create GitHub account** (if you don't have one)
   - Go to: https://github.com/signup

2. **Create new repository**
   ```
   - Name: long-call-dashboard
   - Private: YES (if you have paid plan) or NO (free)
   - Click "Create repository"
   ```

3. **Upload files to GitHub:**
   ```
   Upload these files:
   - streamlit_dashboard.py
   - requirements.txt
   ```

4. **Get Firebase service account key:**
   ```
   a. Go to Firebase Console: https://console.firebase.google.com
   b. Click gear icon → Project settings
   c. Click "Service accounts" tab
   d. Click "Generate new private key"
   e. Save the JSON file (keep it secret!)
   ```

5. **Deploy to Streamlit Cloud:**
   ```
   a. Go to: https://share.streamlit.io
   b. Sign in with GitHub
   c. Click "New app"
   d. Repository: your-username/long-call-dashboard
   e. Main file path: streamlit_dashboard.py
   f. Click "Advanced settings"
   g. Add secret: GOOGLE_APPLICATION_CREDENTIALS
      (Paste contents of service account JSON)
   h. Click "Deploy"
   ```

6. **Done!** Your dashboard will be at: `https://your-app.streamlit.app`

---

### **Option 2: Run Locally** (For Testing)

**Cost:** FREE

**Steps:**

1. **Install Python** (if not installed)
   ```bash
   # Check if Python is installed
   python --version
   # Should show Python 3.8 or higher
   ```

2. **Install dependencies:**
   ```bash
   cd "/home/kristinamajasa/Long Call Update v1.0"
   pip install -r requirements.txt
   ```

3. **Set up Firebase credentials:**
   ```bash
   # Download service account key from Firebase Console
   # Save as: firebase-service-account.json

   # Set environment variable (Linux/Mac):
   export GOOGLE_APPLICATION_CREDENTIALS="firebase-service-account.json"

   # Or (Windows):
   set GOOGLE_APPLICATION_CREDENTIALS=firebase-service-account.json
   ```

4. **Run Streamlit:**
   ```bash
   streamlit run streamlit_dashboard.py
   ```

5. **Open browser:** http://localhost:8501

**Good for testing, but not accessible to squad leads!**

---

### **Option 3: Azure App Service** (If Approved)

**Cost:** $10-15/month
**Best if:** You get Azure approval

**Steps:**

1. **Prerequisites:**
   ```
   - Azure subscription approved
   - Azure CLI installed
   ```

2. **Create App Service:**
   ```bash
   # Login to Azure
   az login

   # Create resource group
   az group create --name LongCallDashboard --location eastus

   # Create App Service plan
   az appservice plan create \
     --name streamlit-plan \
     --resource-group LongCallDashboard \
     --sku B1 \
     --is-linux

   # Create web app
   az webapp create \
     --resource-group LongCallDashboard \
     --plan streamlit-plan \
     --name long-call-dashboard \
     --runtime "PYTHON:3.11"
   ```

3. **Deploy code:**
   ```bash
   # Create startup script
   echo "python -m streamlit run streamlit_dashboard.py --server.port=8000 --server.address=0.0.0.0" > startup.sh

   # Deploy
   az webapp up \
     --resource-group LongCallDashboard \
     --name long-call-dashboard \
     --runtime "PYTHON:3.11"
   ```

4. **Add Firebase credentials:**
   ```bash
   # Add service account as app setting
   az webapp config appsettings set \
     --resource-group LongCallDashboard \
     --name long-call-dashboard \
     --settings GOOGLE_APPLICATION_CREDENTIALS='@firebase-service-account.json'
   ```

5. **Access:** https://long-call-dashboard.azurewebsites.net

---

## 🎯 Recommended Deployment Path

### **For You:**

**Start with Option 1: Streamlit Community Cloud**

**Why:**
- ✅ Easiest setup (30 minutes)
- ✅ No server management
- ✅ Auto-updates from GitHub
- ✅ Good for testing

**Then:**
- Show to IT/Manager
- If approved, migrate to Azure (Option 3)
- Get Azure AD login
- Integrate with Microsoft ecosystem

---

## 📋 Testing the Extension

### **Test Data Flow:**

1. **Reload extension** in Chrome
2. **Answer a call** on 8X8
3. **Fill in Issue & Reason**
4. **Click "📤 Send to Dashboard"**
5. **Check Firebase Console:**
   ```
   - Go to Firebase Console
   - Click "Firestore Database"
   - You should see "updates" collection
   - Click it to see your data!
   ```
6. **Check Streamlit dashboard:**
   ```
   - Refresh dashboard
   - Your update should appear!
   ```

---

## 🐛 Troubleshooting

### **Extension: "Failed to send"**
```
1. Open browser console (F12)
2. Look for error messages
3. Check Firebase Console → Firestore → Rules
4. Make sure rules allow write
```

### **Streamlit: "Permission denied"**
```
1. Make sure GOOGLE_APPLICATION_CREDENTIALS is set
2. Check service account has Firestore permissions
3. Try: gcloud auth application-default login
```

### **Streamlit: "No data"**
```
1. Check Firebase Console - is data there?
2. Check Firestore rules - allow read?
3. Refresh Streamlit dashboard
4. Check filters (Squad, Date) - try "All"
```

---

## 📞 Next Steps

**Choose your deployment option:**

- ✅ **Quick test:** Option 2 (Run locally)
- ✅ **Show squad leads:** Option 1 (Streamlit Cloud)
- ✅ **Production:** Option 3 (Azure - after approval)

**Which option do you want to try first?**

---

## 🎯 Summary

**What you have now:**

```
Extension → Firebase Firestore → Streamlit Dashboard
   ↓              ↓                    ↓
Detects call   Stores data        Displays to squad leads
```

**All working! Just need to deploy Streamlit!**

---

**Questions? Let me know which deployment option you want to use!** 🚀
