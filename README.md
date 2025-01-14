# Car Price Prediction and Recommendation System

This project is a web application that provides car price predictions and recommends similar cars based on user input. It uses machine learning models to make accurate price predictions and find similar vehicles based on various features.

## Features

- Car price prediction based on multiple parameters
- Similar car recommendations
- Interactive web interface
- Support for multiple car manufacturers and models
- Data normalization and preprocessing

## Tech Stack

- **Backend**: Flask (Python)
- **Machine Learning**: scikit-learn, XGBoost
- **Data Processing**: NumPy, Pandas
- **Frontend**: HTML, CSS, JavaScript
- **Deployment**: Docker support

## Project Structure

```
├── app.py              # Main Flask application
├── Dockerfile          # Docker configuration
├── requirements.txt    # Python dependencies
├── models/            # Trained ML models
├── dataSet/           # Dataset files
├── static/            # Static assets (CSS, JS)
└── templates/         # HTML templates
```

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

### Local Development
```bash
python app.py
```
The application will be available at `http://localhost:5000`

### Using Docker
```bash
docker build -t car-prediction-app .
docker run -p 5000:5000 car-prediction-app
```

## Dependencies

- Flask==2.1.3
- NumPy==1.23.5
- Pandas==1.5.3
- scikit-learn==1.1.3
- XGBoost==1.6.2

## Features in Detail

1. **Price Prediction**
   - Input various car specifications
   - Get estimated price based on machine learning model
   - Support for multiple manufacturers and models

2. **Car Recommendations**
   - Get similar car recommendations based on your preferences
   - View alternatives in the same price range
   - Compare different models and manufacturers

## Contributing

Feel free to submit issues and enhancement requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
