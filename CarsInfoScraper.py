# import required libraries
import pandas as pd
import requests as rq
from bs4 import BeautifulSoup as bs
import time
from datetime import datetime, timedelta
import os
import random

# Headers to mimic a real browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def format_time(seconds):
    return str(timedelta(seconds=round(seconds)))
start_time = time.time()
print(f"Starting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
# create a loop for different price ranges and pages
for price_from in range(3000, 80000, 500):  # From 3000 to 80000, step 500
    price_to = price_from + 500
    print(f"\nStarting price range £{price_from} - £{price_to}")
    
    # Reset car_list for each price range
    car_list = []
    price_range_start_time = time.time()
    
    for page in range(1, 51):  # Pages 1 to 50 for each price range
        page_start_time = time.time()
        website = f"https://www.theaa.com/used-cars/displaycars?fullpostcode=&sortby=priceasc&page={page}&pricefrom={price_from}&priceto={price_to}"
        try:
            print(f"Scraping price range £{price_from}-£{price_to}, page {page}...")
            page_content = rq.get(website, headers=headers)
            
            # Add random sleep between requests (2-5 seconds)
            sleep_time = random.uniform(2, 5)
            time.sleep(sleep_time)
            
            soup = bs(page_content.content, 'html.parser')
            
            # get all features at once to minimize DOM traversals
            names = soup.select('.make-model-text')
            prices = soup.find_all("strong", {"class": "total-price"})
            other_features = soup.find_all('ul', {'class': "vl-specs"})
            
            if not names or not prices:  # Check if we got any results
                print(f"No results found on page {page}, might be blocked or at the end")
                break
                
            # Process all items together
            for name, price, features in zip(names, prices, other_features):
                feature_items = features.find_all('li')
                car_list.append({
                    'name': name.text.strip(),
                    'price': price.text.strip().replace('\n', '').replace(' ' * 36, ''),
                    'year': feature_items[0].text,
                    'mileage': feature_items[2].text,
                    'engine': feature_items[4].text,
                    'transmission': feature_items[6].text if len(feature_items) > 6 else 'n/a'
                })            
        except Exception as e:
            print(f"Error on page {page}: {str(e)}")
            continue

    # Save data after each price range is completed
    if car_list:  # Only create if we have data
        cars = pd.DataFrame(car_list)
        file_exists = os.path.isfile('./dataSet/car_data.csv')
        # save new dataframe in a csv file, appending to existing data   
        cars.to_csv('./dataSet/car_data.csv', 
                    mode='a', 
                    header=not file_exists, 
                    index=False)
        
        # Calculate and print price range execution time
        price_range_time = time.time() - price_range_start_time
        print(f"\nPrice range £{price_from}-£{price_to} completed in: {format_time(price_range_time)}")
        print(f"Successfully saved {len(cars)} car listings for price range £{price_from}-£{price_to}")
    else:
        print(f"No data was collected for price range £{price_from}-£{price_to}")
total_time = time.time() - start_time
print(f"Total execution time: {format_time(total_time)}")