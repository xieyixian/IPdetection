from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import joblib
import geoip2.database
import ipaddress

app = Flask(__name__)
CORS(app)

GEOIP_DATABASE_PATH = 'GeoLite2-City.mmdb'
MODEL_PATH = 'model.pkl'
BLACKLIST_PATH = 'blacklist_ips.csv'

# Load pre-trained models and blacklists
model = joblib.load(MODEL_PATH)


def load_blacklist(filepath):
    with open(filepath, 'r') as file:
        return set(line.strip() for line in file)


def is_local_or_reserved_ip(ip_address):
    try:
        ip = ipaddress.ip_address(ip_address)
        return ip.is_loopback or ip.is_private or ip.is_reserved
    except ValueError:
        return False


def enrich_ip_data(ip_address):
    if is_local_or_reserved_ip(ip_address):
        return {
            'country': 'Local or Reserved',
            'city': 'Local or Reserved',
            'latitude': 0.0,
            'longitude': 0.0
        }

    enriched_data = {
        'country': 'unknown',
        'city': 'unknown',
        'latitude': 0.0,
        'longitude': 0.0
    }

    try:
        with geoip2.database.Reader(GEOIP_DATABASE_PATH) as reader:
            response = reader.city(ip_address)
            enriched_data['country'] = response.country.name
            enriched_data['city'] = response.city.name
            enriched_data['latitude'] = response.location.latitude
            enriched_data['longitude'] = response.location.longitude
    except (ValueError, geoip2.errors.AddressNotFoundError):
        pass

    return enriched_data


def preprocess(data, blacklist, model):
    processed_data = data[~data['IP'].isin(blacklist)]
    processed_data['Time'] = pd.to_datetime(processed_data['Time']).astype('int64') // 10 ** 9
    enriched_info = [enrich_ip_data(ip) for ip in processed_data['IP']]
    enriched_df = pd.DataFrame(enriched_info)
    processed_data = pd.concat([processed_data.reset_index(drop=True), enriched_df], axis=1)
    processed_data['Accept-Language'] = processed_data['Accept-Language'].astype('category').cat.codes
    processed_data['Location'] = processed_data['Location'].astype('category').cat.codes
    processed_data['country'] = processed_data['country'].astype('category').cat.codes
    processed_data['city'] = processed_data['city'].astype('category').cat.codes
    numeric_cols = processed_data.select_dtypes(include=['float64', 'int64']).columns
    for col in numeric_cols:
        processed_data[col] = processed_data[col].fillna(processed_data[col].mean())
    processed_data = processed_data[model.feature_names_in_]
    return processed_data


@app.route('/ipcheck', methods=['POST'])
def predict():
    data = request.get_json()
    #get IP address
    if request.headers.getlist("X-Forwarded-For"):
        ip_address = request.headers.getlist("X-Forwarded-For")[0]
    else:
        ip_address = request.remote_addr

    blacklist = load_blacklist(BLACKLIST_PATH)
    if is_local_or_reserved_ip(ip_address) or ip_address in blacklist:
        return jsonify({'prediction': 0, 'message': 'IP address is local, reserved, or in blacklist, considered safe.'})

    test_data = pd.DataFrame({
        'IP': [ip_address],
        'Time': [data.get('time', '')],
        'Accept-Language': [data.get('accept_language', '')],
        'Location': [data.get('location', '')],
    })

    processed_test_data = preprocess(test_data, blacklist, model)
    prediction = model.predict(processed_test_data)[0]

    status_map = {0: 'safe', 1: 'verify', 2: 'block'}
    status = status_map.get(prediction, 'error')
    return jsonify({'status': status, 'prediction': int(prediction)})


if __name__ == '__main__':
    app.run(debug=True)
