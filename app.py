from flask import Flask, render_template, request, jsonify

from pipeline.orchestrator import run

app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    message = request.form.get("message", "")
    category = request.form.get("category", "sms")
    screenshot = request.files.get("screenshot")

    result = run(message, screenshot, category=category)

    if "error" in result:
        return jsonify(result), 400

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)
