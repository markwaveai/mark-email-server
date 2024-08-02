# server.py

from flask import Flask, jsonify

import fetch_yesterday_count as fetch_yesterday_count
app = Flask(__name__)

@app.route('/send_checktrayCount_email', methods=['GET'])
def call_function():
    data =  fetch_yesterday_count.update_check_tray_images_count()
    return jsonify({"message": data})
if __name__ == '__main__':
    app.run(debug=True)
