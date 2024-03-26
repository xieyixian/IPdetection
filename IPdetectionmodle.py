from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import pandas as pd
import joblib
import geoip2.database

# Path to the GeoLite2 database file you downloaded
GEOIP_DATABASE_PATH = '/home/GeoLite2-City.mmdb'


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


def preprocess(data, blacklist):
    processed_data = data[~data['IP'].isin(blacklist)]

    # Convert time column to UNIX timestamp
    processed_data['Time'] = pd.to_datetime(processed_data['Time']).astype('int64') // 10 ** 9

    enriched_info = [enrich_ip_data(ip) for ip in processed_data['IP']]
    enriched_df = pd.DataFrame(enriched_info)

    processed_data = pd.concat([processed_data.reset_index(drop=True), enriched_df], axis=1)

    # Convert categorical data to numeric codes
    processed_data['Accept-Language'] = processed_data['Accept-Language'].astype('category').cat.codes
    processed_data['Location'] = processed_data['Location'].astype('category').cat.codes
    processed_data['country'] = processed_data['country'].astype('category').cat.codes
    processed_data['city'] = processed_data['city'].astype('category').cat.codes

    # Handling NaN values in numeric columns
    numeric_cols = processed_data.select_dtypes(include=['float64', 'int64']).columns
    for col in numeric_cols:
        processed_data[col].fillna(processed_data[col].mean(), inplace=True)

    # Remove original IP column
    return processed_data.drop(['IP'], axis=1)


if __name__ == "__main__":
    blacklist = load_blacklist('/home/blacklist_ips.csv')
    training_data = pd.read_csv('/home/training_ip_data_8000.csv')

    processed_data = preprocess(training_data, blacklist)

    X = processed_data.drop('Threat Level', axis=1)
    y = processed_data['Threat Level']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Model accuracy: {accuracy}")

    joblib.dump(model, '/home/model.pkl')
