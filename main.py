from flask import Flask, jsonify, render_template, request
import fetch_yesterday_count

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send_checktrayCount_email', methods=['GET'])
def send_checktrayCount_email():
    data = fetch_yesterday_count.update_check_tray_images_count()
    return jsonify({"message": data})

if __name__ == '__main__':
    app.run(debug=True)
