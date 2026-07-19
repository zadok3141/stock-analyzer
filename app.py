import os, sys
from flask import Flask, render_template, request, jsonify
from analyzer import run_analysis, INTERVAL_MAX_PERIOD

if getattr(sys, 'frozen', False):
    # Running inside a py2app bundle — resources sit two levels above the binary
    _resources = os.path.join(os.path.dirname(os.path.dirname(sys.executable)), 'Resources')
    _template_folder = os.path.join(_resources, 'templates')
else:
    _template_folder = 'templates'

app = Flask(__name__, template_folder=_template_folder)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    body = request.get_json(silent=True) or {}
    ticker = body.get('ticker', '').strip()
    period = body.get('period', '3mo').strip()
    interval = body.get('interval', '1d').strip()
    window = int(body.get('window', 3))
    currency = body.get('currency', 'USD').strip().upper()

    if not ticker:
        return jsonify({'error': 'Please enter a ticker symbol.'}), 400

    if window < 1 or window > 20:
        return jsonify({'error': 'Swing window must be between 1 and 20.'}), 400

    try:
        result = run_analysis(ticker, period, interval, swing_window=window, currency=currency)
        return jsonify(result)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500


@app.route('/interval-limits')
def interval_limits():
    return jsonify(INTERVAL_MAX_PERIOD)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
