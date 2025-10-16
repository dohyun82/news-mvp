from flask import Flask, jsonify, render_template
from modules import crawler, gemini, slack

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/collect', methods=['POST'])
def collect_news():
    articles = crawler.crawl_naver_news([])
    return jsonify(articles)

@app.route('/api/summarize', methods=['POST'])
def summarize_news():
    summary = gemini.get_summary_from_gemini("[http://example.com](http://example.com)")
    return jsonify({"summary": summary})

@app.route('/api/send-slack', methods=['POST'])
def send_slack():
    success, message = slack.send_message_to_slack([])
    return jsonify({"success": success, "message": message})

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5001)


