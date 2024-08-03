from flask import Flask, jsonify, render_template, request
import fetch_yesterday_count

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send_checktrayCount_email', methods=['POST'])
def send_checktrayCount_email():
    if not request.is_json:
        return jsonify({"error": "Request body must be JSON"}), 400
    
    reqdata = request.get_json()
    response_data = fetch_yesterday_count.update_check_tray_images_count(reqdata)
    return jsonify({"message": response_data})

if __name__ == '__main__':
    app.run(debug=True)
