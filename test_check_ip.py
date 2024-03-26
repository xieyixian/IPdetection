import pandas as pd
import joblib
import geoip2.database
GEOIP_DATABASE_PATH = 'GeoLite2-City.mmdb'
MODEL_PATH = 'model.pkl'
BLACKLIST_PATH = 'blacklist_ips.csv'

def enrich_ip_data(ip_address):
    with geoip2.database.Reader(GEOIP_DATABASE_PATH) as reader:
        enriched_data = {
            'country': None,
            'city': None,
            'latitude': None,
            'longitude': None
        }
        try:
            response = reader.city(ip_address)
            enriched_data['country'] = response.country.name
            enriched_data['city'] = response.city.name
            enriched_data['latitude'] = response.location.latitude
            enriched_data['longitude'] = response.location.longitude
        except geoip2.errors.AddressNotFoundError:
            pass
        return enriched_data

def load_blacklist(filepath):
    with open(filepath, 'r') as file:
        blacklist = set(line.strip() for line in file)
    return blacklist


def preprocess(data, blacklist, model):
    processed_data = data[~data['IP'].isin(blacklist)]
    processed_data['Time'] = pd.to_datetime(processed_data['Time']).astype('int64') // 10**9
    enriched_info = [enrich_ip_data(ip) for ip in processed_data['IP']]
    enriched_df = pd.DataFrame(enriched_info)

    # 明确转换为float类型，然后填充NaN值
    enriched_df['latitude'] = enriched_df['latitude'].astype(float).fillna(0)
    enriched_df['longitude'] = enriched_df['longitude'].astype(float).fillna(0)

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


model = joblib.load(MODEL_PATH)

test_data = pd.DataFrame({
    'IP': ['127.0.0.1'],
    'Time': ['2022-03-20 14:22:00'],
    'Accept-Language': ['en-GB,en-US;q=0.9,en;q=0.8,zh-CN;q=0.7,zh;q=0.6'],
    'Location': ['None, None, None'],
})

blacklist = load_blacklist(BLACKLIST_PATH)
processed_test_data = preprocess(test_data, blacklist, model)

prediction = model.predict(processed_test_data)

print(f"Prediction: {prediction}")
