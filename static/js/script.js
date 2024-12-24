console.log('Script loaded!');

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('predictionForm');
    const manufacturerSelect = document.getElementById('manufacturer');
    const carNameSelect = document.getElementById('carName');
    const result = document.getElementById('result');
    const predictionsList = document.getElementById('predictionsList');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const predictionCount = document.getElementById('predictionCount');
    const avgPrice = document.getElementById('avgPrice');
    const clearHistoryBtn = document.getElementById('clearHistoryBtn');
    const recommendationsCard = document.getElementById('recommendationsCard'); // New
    const recommendationsDiv = document.getElementById('recommendations');     // New
    let predictions = [];

    // Load predictions from localStorage on page load
    function loadPredictions() {
        const savedPredictions = localStorage.getItem('carPricePredictions');
        if (savedPredictions) {
            predictions = JSON.parse(savedPredictions);
            updatePredictionHistory();
            updateStats();
            updateClearButtonVisibility();
        }
    }

    loadPredictions();

    // Manufacturer select change event
    if (manufacturerSelect) {
        manufacturerSelect.onchange = async function() {
            if (carNameSelect) {
                carNameSelect.disabled = true;
                carNameSelect.innerHTML = '<option value="">Loading car names...</option>';
                
                if (this.value) {
                    try {
                        const url = `/get_car_names/${this.value}`;
                        const response = await fetch(url);
                        const data = await response.json();
                        
                        carNameSelect.innerHTML = '<option value="">Choose car name...</option>';
                        if (data.cars && Array.isArray(data.cars)) {
                            data.cars.forEach(car => {
                                const option = document.createElement('option');
                                option.value = car;
                                option.textContent = car;
                                carNameSelect.appendChild(option);
                            });
                        } else {
                            console.error('Invalid data format:', data);
                        }
                    } catch (error) {
                        console.error('Error fetching car names:', error);
                        carNameSelect.innerHTML = '<option value="">Error loading car names</option>';
                    } finally {
                        carNameSelect.disabled = false;
                    }
                } else {
                    carNameSelect.innerHTML = '<option value="">Select car name</option>';
                    carNameSelect.disabled = true;
                }
            } else {
                console.error('Car name select not found');
            }
        };
    } else {
        console.error('Manufacturer select not found');
    }

    // Save predictions to localStorage
    function savePredictions() {
        localStorage.setItem('carPricePredictions', JSON.stringify(predictions));
        updateClearButtonVisibility();
    }

    // Update clear button visibility
    function updateClearButtonVisibility() {
        if (predictions.length > 0) {
            clearHistoryBtn.classList.remove('d-none');
        } else {
            clearHistoryBtn.classList.add('d-none');
        }
    }

    // Clear history button click handler
    clearHistoryBtn.addEventListener('click', clearPredictionHistory);

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        if (!form.checkValidity()) {
            e.stopPropagation();
            form.classList.add('was-validated');
            return;
        }
        
        // Clear previous result and recommendations
        const resultElement = document.getElementById('result');
        if (resultElement) {
            resultElement.innerHTML = '';
            resultElement.style.display = 'none';
        }
        if (recommendationsDiv) {
            recommendationsDiv.innerHTML = '';
        }
        if (recommendationsCard) {
            recommendationsCard.style.display = 'none';
        }
        
        loadingOverlay.style.display = 'flex';
        
        const formData = {
            manufacturer: manufacturerSelect.value,
            name: carNameSelect.value,
            age: parseInt(document.getElementById('age').value),
            mileage: parseFloat(document.getElementById('mileage').value),
            engine: document.getElementById('engine').value,
            transmission: document.getElementById('transmission').value
        };
    
        try {
            const response = await fetch('/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
    
            const data = await response.json();
            console.log('Prediction response:', data);
    
            // Add timeout before showing results
            await new Promise(resolve => setTimeout(resolve, 1500));

            if (response.ok && data.success) {
                const prediction = {
                    ...formData,
                    price: data.price,
                    timestamp: new Date().toLocaleString()
                };
                
                predictions.unshift(prediction);
                savePredictions();
                updatePredictionHistory();
                updateClearButtonVisibility();
                updateStats();
                
                if (resultElement && predictions.length > 0) {
                    const latestPrediction = predictions[0];
                    displayPrediction(latestPrediction, resultElement);
                    resultElement.scrollIntoView({ behavior: 'smooth' });
                } else {
                    console.error('Result element not found or no predictions!');
                }

                if (data.recommendations && data.recommendations.length > 0) {
                    // Show skeleton cards
                    recommendationsDiv.innerHTML = Array(3).fill(`
                        <div class="col-md-6 col-lg-4">
                            <div class="skeleton-card"></div>
                        </div>
                    `).join('');
                    recommendationsCard.style.display = 'block';
                    recommendationsCard.scrollIntoView({ behavior: 'smooth' });

                    // After 1 second, show the actual recommendations
                    setTimeout(() => {
                        recommendationsDiv.innerHTML = data.recommendations.map(car => `
                            <div class="col-md-6 col-lg-4">
                                <div class="card h-100">
                                    <div class="card-body">
                                        <h5 class="card-title">${car.name || ''}</h5>
                                        <p class="card-text">
                                            Engine: ${car.engine}<br>
                                            Transmission: ${car.transmission}<br>
                                            Price: ${parseFloat(car.price).toLocaleString()} MAD<br>
                                            Mileage: ${parseFloat(car.kilometerage).toLocaleString()} km<br>
                                            Age: ${car.age} years
                                        </p>
                                    </div>
                                </div>
                            </div>
                        `).join('');
                    }, 2000);
                } else if (recommendationsCard) {
                    recommendationsCard.style.display = 'none';
                }
            } else {
                if (resultElement) {
                    resultElement.innerHTML = `
                        <div class="alert alert-danger mb-0">
                            <i class="fas fa-exclamation-circle me-2"></i>
                            ${data.error || 'Failed to predict price'}
                        </div>
                    `;
                    resultElement.style.display = 'block';
                }
                throw new Error(data.error || 'Failed to predict price');
            }
        } catch (error) {
            console.error('Prediction error:', error);
            if (resultElement) {
                resultElement.innerHTML = `
                    <div class="alert alert-danger mb-0">
                        <i class="fas fa-exclamation-circle me-2"></i>
                        Error: ${error.message}
                    </div>
                `;
                resultElement.style.display = 'block';
            }
        } finally {
            loadingOverlay.style.display = 'none';
        }
    });

    // Function to display a single prediction
    function displayPrediction(prediction, element) {
        const predictionElement = document.createElement('div');
        if (element.id === 'result') {
            // Main result display only car name and price
            predictionElement.className = 'list-group-item';
            predictionElement.innerHTML = `
                <div>
                    <strong>${prediction.name}</strong>
                </div>
                <div class="text-end">
                    <strong>Estimated Price: ${parseInt(prediction.price.replace(/[^0-9]/g, '')).toLocaleString()}</strong><br>
                    <small class="text-muted">Price Range: ${(Math.ceil((parseInt(prediction.price.replace(/[^0-9]/g, '')) * 0.9) / 100) * 100).toLocaleString()} - ${(Math.ceil((parseInt(prediction.price.replace(/[^0-9]/g, '')) * 1.15) / 100) * 100).toLocaleString()} MAD</small>
                </div>
            `;
        } else {
            // History display - full details
            predictionElement.className = 'list-group-item d-flex justify-content-between align-items-start';
            predictionElement.innerHTML = `
                <div>
                    <strong> ${prediction.name}</strong><br>
                    Age: ${prediction.age} years<br>
                    Kilometerage: ${parseInt(prediction.mileage).toLocaleString()} km<br>
                    Engine: ${prediction.engine}<br>
                    Transmission: ${prediction.transmission}
                </div>
                <div class="text-end">
                    <strong>${prediction.price}</strong><br>
                    <small class="text-muted">${prediction.timestamp}</small>
                </div>
            `;
        }
        element.appendChild(predictionElement);
        element.style.display = 'block';
    }

    function updatePredictionHistory() {
        predictionsList.innerHTML = '';
        const latestPredictions = predictions.slice(0, 4);
        latestPredictions.forEach(prediction => {
            displayPrediction(prediction, predictionsList);
        });
    }

    function clearPredictionHistory() {
        if (confirm('Are you sure you want to clear all prediction history?')) {
            predictions = [];
            localStorage.removeItem('carPricePredictions');
            updatePredictionHistory();
            updateStats();
            updateClearButtonVisibility();
        }
    }

    function updateStats() {
        predictionCount.textContent = predictions.length;
        if (predictions.length > 0) {
            const prices = predictions.map(p => {
                if (p && p.price) {
                    const priceStr = p.price.toString();
                    return parseInt(priceStr.replace(/[^0-9]/g, '')) || 0;
                }
                return 0;
            });
            const avg = prices.reduce((a, b) => a + b, 0) / prices.length;
            avgPrice.textContent = `${Math.round(avg).toLocaleString()} MAD`;
        } else {
            avgPrice.textContent = '0 MAD';
        }
    }

    // Input validation
    const inputs = form.querySelectorAll('input, select');
    inputs.forEach(input => {
        input.addEventListener('change', () => {
            if (!input.checkValidity()) {
                form.classList.add('was-validated');
            }
        });
    });
});