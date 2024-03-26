from flask import Flask, request
import requests
from datetime import datetime
from flask import jsonify

app = Flask(__name__)


@app.route('/api/print_info', methods=['GET'])
def print_info():
    # 获取请求头中的Accept-Language
    accept_language = request.headers.get('Accept-Language')

    # 获取IP地址
    if request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
        ip = request.remote_addr

    # 获取当前时间
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 获取大致位置（使用ip-api.com）
    try:
        response = requests.get(f'http://ip-api.com/json/{ip}?fields=status,message,country,regionName,city')
        location_info = response.json()
        location = f"{location_info.get('country')}, {location_info.get('regionName')}, {location_info.get('city')}"
    except Exception as e:
        location = "Location could not be determined."

    print(f"Accept-Language: {accept_language}")
    print(f"IP: {ip}")
    print(f"Time: {current_time}")
    print(f"Location: {location}")

    return jsonify({
        "Accept-Language": accept_language,
        "IP": ip,
        "Time": current_time,
        "Location": location
    })


if __name__ == '__main__':
    app.run(debug=True)
