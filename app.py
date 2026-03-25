from flask import Flask, render_template, request

app = Flask(__name__)

def analyze_text(text):
    text = text.lower()

    score = 0
    reasons = []

    # Rule 1: Asking money
    if "pay" in text or "fee" in text or "registration" in text:
        score += 40
        reasons.append("Asks for money")

    # Rule 2: Urgency
    if "urgent" in text or "limited time" in text:
        score += 20
        reasons.append("Creates urgency")

    # Rule 3: Unofficial contact
    if "whatsapp" in text or "telegram" in text:
        score += 20
        reasons.append("Uses unofficial communication")

    # Rule 4: Too good to be true
    if "easy money" in text or "no experience" in text:
        score += 20
        reasons.append("Too good to be true")

    # Rule 5: Unrealistic hiring
    if "no interview" in text or "selected" in text:
        score += 20
        reasons.append("Unrealistic hiring process")

    # Rule 6: Work from home scam
    if "work from home" in text:
        score += 10
        reasons.append("Generic job phrase")

    # Rule 7: Suspicious links
    if "click here" in text or "apply now" in text:
        score += 10
        reasons.append("Suspicious link language")

    # Rule 8: Unrealistic promises
    if "guaranteed" in text:
        score += 10
        reasons.append("Unrealistic promises")

    # Final result
    if score >= 60:
        return f"⚠️ Scam Likely ({score}%)<br><b>Reasons:</b> {', '.join(reasons)}"
    elif score >= 30:
        return f"⚠️ Suspicious ({score}%)<br><b>Reasons:</b> {', '.join(reasons)}"
    else:
        return f"✅ Looks Safe ({score}%)"

@app.route("/", methods=["GET", "POST"])
def index():
    result = ""
    if request.method == "POST":
        user_input = request.form["message"]
        result = analyze_text(user_input)
    return render_template("index.html", result=result)

if __name__ == "__main__":
    app.run(debug=True)