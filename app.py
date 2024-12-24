from flask import Flask, render_template, request, jsonify
import pickle
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
from sklearn.neighbors import NearestNeighbors

app = Flask(__name__)

# Load model and data
def load_model():
    with open("./models/regressorfinal.pkl", "rb") as file:
        return pickle.load(file)

def load_data():
    return pd.read_csv('./dataSet/cleaned_car_data2.csv')

data = load_model()
df = load_data()
model = data["model"]
norm = data["norm"]

# Get top 30 manufacturers by frequency
top_manufacturers = df['manufacturer'].value_counts().nlargest(35).index.tolist()

# Create and fit label encoders
le_manufacturer = LabelEncoder()
le_name = LabelEncoder()
le_engine = LabelEncoder()
le_transmission = LabelEncoder()

le_manufacturer.fit(df['manufacturer'])
le_name.fit(df['name'])
le_engine.fit(df['engine'])
le_transmission.fit(df['transmission'])

# Encode categorical variables in df for recommendation system
df['manufacturer_enc'] = le_manufacturer.transform(df['manufacturer'])
df['engine_enc'] = le_engine.transform(df['engine'])
df['transmission_enc'] = le_transmission.transform(df['transmission'])

# Scale numerical features for recommendation system
df['price'] = df['price'] * 12.8  # Convert to MAD
scaler = MinMaxScaler()
df[['kilometerage', 'price', 'age']] = scaler.fit_transform(df[['kilometerage', 'price', 'age']])

# Features to use for similarity
features = [
    'manufacturer_enc',
    'engine_enc',
    'age',
    'transmission_enc',
    'kilometerage',
    'price'
]

@app.route('/')
def home():
    return render_template(
        'index.html',
        manufacturers=sorted(top_manufacturers),
        engines=sorted(df["engine"].unique()),
        transmissions=sorted(df["transmission"].unique())
    )

"""
Recommend similar cars based on input data.
"""
def get_recommendations(input_data, df, features, scaler, le_encoders, top_n=6):
    try:
        # Create a DataFrame for the input data
        input_df = pd.DataFrame([input_data])

        # Encode categorical variables
        input_df['manufacturer_enc'] = le_encoders['manufacturer'].transform([input_data['manufacturer']])
        input_df['engine_enc'] = le_encoders['engine'].transform([input_data['engine']])
        input_df['transmission_enc'] = le_encoders['transmission'].transform([input_data['transmission']])

        # Scale numerical features including age
        input_df[['kilometerage', 'price', 'age']] = scaler.transform(
            input_df[['kilometerage', 'price', 'age']]
        )

        # Prepare input features for NearestNeighbors
        input_features = input_df[features].values

        # Initialize and fit NearestNeighbors
        nn = NearestNeighbors(n_neighbors=top_n*3, metric='cosine')
        nn.fit(df[features])

        # Find nearest neighbors
        distances, indices = nn.kneighbors(input_features)

        # Get recommended cars
        recommended_cars = df.iloc[indices[0]].copy()

        # Inverse transform scaled numerical features
        recommended_cars[['kilometerage', 'price', 'age']] = scaler.inverse_transform(
            recommended_cars[['kilometerage', 'price', 'age']]
        )
        recommended_cars['price'] = recommended_cars['price']

        # Inverse transform categorical variables
        recommended_cars['manufacturer'] = le_encoders['manufacturer'].inverse_transform(
            recommended_cars['manufacturer_enc'].astype(int)
        )
        recommended_cars['engine'] = le_encoders['engine'].inverse_transform(
            recommended_cars['engine_enc'].astype(int)
        )
        recommended_cars['transmission'] = le_encoders['transmission'].inverse_transform(
            recommended_cars['transmission_enc'].astype(int)
        )

        # Ensure unique car names in recommendations
        recommended_cars = recommended_cars.drop_duplicates(subset=['name'])

        # Prioritize price and engine in recommendations
        recommended_cars = recommended_cars.sort_values(by=['price', 'engine'])

        final_recommendations = recommended_cars.head(top_n)
        return final_recommendations
    except Exception as e:
        print(f"Recommendation error: {str(e)}")
        raise

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        
        # Validate manufacturer is in top 30
        if data['manufacturer'] not in top_manufacturers:
            return jsonify({
                'error': 'Selected manufacturer is not in the top 30 list',
                'success': False
            }), 400
            
        # Create feature array with correct order
        X = np.array([[
            data['name'],
            data['manufacturer'],
            float(data['age']),
            float(data['mileage']),  # This remains the same
            data['engine'],
            data['transmission']
        ]])

        X_transformed = X.copy()
        X_transformed[:, 0] = le_name.transform([X[0, 0]])[0]  # Transform name
        X_transformed[:, 1] = le_manufacturer.transform([X[0, 1]])[0]  # Transform manufacturer
        # age and mileage are already numeric
        X_transformed[:, 4] = le_engine.transform([X[0, 4]])[0]  # Transform engine
        X_transformed[:, 5] = le_transmission.transform([X[0, 5]])[0]  # Transform transmission
        X_transformed = X_transformed.astype(float)

        # Define feature names for the DataFrame
        model_feature_names = ['name', 'manufacturer', 'age', 'kilometerage', 'engine', 'transmission']

        # Convert to DataFrame to retain feature names
        X_transformed_df = pd.DataFrame(X_transformed, columns=model_feature_names)
                
        # Normalize using the scaler (norm)
        X_normalized = norm.transform(X_transformed_df)
        price = model.predict(X_normalized)
        actual_price = price[0]
        
        # Prepare input data for recommendation
        input_features = {
            'manufacturer': data['manufacturer'],
            'engine': data['engine'],
            'transmission': data['transmission'],
            'kilometerage': float(data['mileage']),  # Use 'kilometerage' as the key
            'price': actual_price,
            'age': float(data['age'])  # Include age in the input features
        }
        # Get recommendations
        recommendations = get_recommendations(
            input_data=input_features,
            df=df,
            features=features,
            scaler=scaler,
            le_encoders={
                'manufacturer': le_manufacturer,
                'engine': le_engine,
                'transmission': le_transmission
            },
            top_n=6
        )

        # Convert recommendations to JSON serializable format
        recommendations_list = recommendations[[
            'manufacturer', 'name', 'engine', 'transmission', 'kilometerage', 'price', 'age'
        ]].to_dict('records')

        # Return JSON response with price and recommendations
        return jsonify({
            'price': f"{actual_price:,.0f} MAD",
            'success': True,
            'recommendations': recommendations_list
        })
    except Exception as e:
        print(f"Prediction error: {str(e)}")  # Logging for debugging
        return jsonify({
            'error': str(e),
            'success': False
        }), 400
        
@app.route('/get_car_names/<manufacturer>', methods=['GET'])
def get_car_names(manufacturer):
    try:
        print(f"Fetching car names for manufacturer: {manufacturer}")
        names = sorted(df[df['manufacturer'] == manufacturer]['name'].unique())
        print(f"Found {len(names)} car names")
        return jsonify({'cars': names})
    except Exception as e:
        print(f"Error getting car names: {str(e)}")
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)