# 🛡️ TrustAI — Scam Job Detector

> **AI-powered web app that detects scam job messages using rule-based and heuristic analysis.**  
> Provides a risk percentage score and plain-English explanation for every suspicious message analyzed.

🔗 **Live Demo:** [trustai-scam-detector-1.onrender.com](https://trustai-scam-detector-1.onrender.com/)  
📁 **Repository:** [GavaraNeha/TrustAI-Scam-Detector](https://github.com/GavaraNeha/TrustAI-Scam-Detector)

---

## 📌 Problem Statement

Job seekers — especially students and fresh graduates — are increasingly targeted by fraudulent job offers via WhatsApp, email, and social media. These scams often promise high pay, remote work, and easy hiring with the goal of extracting personal data or money.

**TrustAI** helps users instantly verify whether a job message is legitimate or a scam, before they respond or share any personal information.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔍 **Scam Detection** | Analyzes job messages using rule-based and heuristic pattern matching |
| 📊 **Risk Score** | Returns a percentage-based risk rating (e.g. 87% — High Risk) |
| 💬 **Explanation** | Provides a human-readable reason explaining why the message was flagged |
| 🌐 **Web Interface** | Clean, accessible UI — no installation needed |
| ⚡ **Instant Results** | Real-time analysis with no login or signup required |

---

## 🧠 How It Works

```
User pastes job message
        ↓
Rule-Based Engine scans for known scam patterns
(urgency phrases, vague job titles, payment requests, etc.)
        ↓
Heuristic Analyzer scores linguistic and structural signals
        ↓
Risk Score (0–100%) + Explanation generated
        ↓
Result displayed to user
```

**Detection signals include:**
- Unrealistic salary promises
- Requests for personal/financial information upfront
- Vague or non-existent company names
- Urgency language ("Apply immediately", "Limited slots")
- Grammar and formatting anomalies
- Suspicious contact methods (WhatsApp-only, personal emails)

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python, Flask (`app.py`) |
| **Frontend** | HTML, CSS, Jinja2 Templates |
| **Logic Engine** | Rule-based heuristics (custom NLP patterns) |
| **Deployment** | Render (free tier, live URL) |
| **Version Control** | Git, GitHub |

---

## 🚀 Getting Started (Local Setup)

### Prerequisites
- Python 3.8+
- pip

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/GavaraNeha/TrustAI-Scam-Detector.git
cd TrustAI-Scam-Detector

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
python app.py
```

Then open your browser at `http://localhost:5000`

---

## 📂 Project Structure

```
TrustAI-Scam-Detector/
│
├── templates/
│   └── index.html          # Frontend UI (Jinja2 template)
│
├── app.py                  # Flask app + detection logic
├── requirements.txt        # Python dependencies
├── LICENSE                 # MIT License
└── README.md               # Project documentation
```

---

## 💡 Example Usage

**Input message:**
> *"Congratulations! You have been selected for a Work From Home job. Earn ₹25,000/week. No experience needed. Send your Aadhaar and bank details to confirm your slot. Limited seats!"*

**TrustAI Output:**
- 🔴 **Risk Score: 91% — Very High Risk**
- ⚠️ **Reason:** Message contains multiple scam indicators — requests for sensitive documents, unrealistic income promise, urgency pressure, and no verifiable employer identity.

---

## 🔮 Future Enhancements

- [ ] Machine learning model (trained on labeled scam/legit job dataset)
- [ ] Browser extension for real-time WhatsApp / email scanning
- [ ] Multi-language support (Hindi, Telugu, Tamil)
- [ ] API endpoint for third-party integration
- [ ] User feedback loop to improve detection accuracy

---

## 👩‍💻 About the Developer

**Gavara Neha** — B.Tech in AI & Machine Learning, Aditya University  
Passionate about building AI tools that solve real-world problems for everyday users.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue?style=flat&logo=linkedin)](https://linkedin.com)
[![GitHub](https://img.shields.io/badge/GitHub-GavaraNeha-black?style=flat&logo=github)](https://github.com/GavaraNeha)
[![LeetCode](https://img.shields.io/badge/LeetCode-100%2B%20Problems-orange?style=flat&logo=leetcode)](https://leetcode.com)

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

> *Built to protect job seekers from online fraud — one message at a time.*
