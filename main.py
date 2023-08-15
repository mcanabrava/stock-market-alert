import pandas as pd
import configparser
import requests
import json
from twilio.rest import Client

# Read the CSV file into a Pandas DataFrame
df = pd.read_csv('indexes.csv')

# Read the API key from env.cfg
config = configparser.ConfigParser()
config.read('env.cfg')

STOCK_API_KEY = config.get('MARKETSTACK', 'API_KEY')
TWILIO_API_KEY = config.get('TWILIO', 'API_KEY')
ACCOUNT_SID = config.get('TWILIO', 'ACCOUNT_SID')
AUTH_TOKEN = config.get('TWILIO', 'AUTH_TOKEN')
TWILIO_PHONE_NUMBER = config.get('TWILIO', 'TWILIO_PHONE_NUMBER')
TARGET_PHONE_NUMBER = config.get('TWILIO', 'TARGET_PHONE_NUMBER')

# Create an empty dictionary to store the successful responses
data_dict = {}

# Loop through each value in the "ticker" column
for ticker in df['Ticker']:
    # Make the API request for each ticker
    url = f'http://api.marketstack.com/v1/intraday?access_key={STOCK_API_KEY}&symbols={ticker}'
    
    # You can add optional parameters like interval, sort, date_from, date_to, limit, and offset to the URL as needed
    # For example: url += '&interval=1h&sort=DESC&date_from=2023-01-01&date_to=2023-07-01&limit=100&offset=0'

    response = requests.get(url)

    if response.status_code == 200:
        # Parse the JSON response
        response_data = response.json()

        # Check if the "data" list is not empty
        if 'data' in response_data and len(response_data['data']) > 0:
            # Get the first "data" object from the JSON response
            data = response_data['data'][0]

            # Calculate the percentage difference between "open" and "last" values
            open_value = data['open']
            last_value = data['last']
            percent_diff = ((last_value - open_value) / open_value) * 100

            # Store the ticker and values in the dictionary
            data_dict[ticker] = {
                'open': open_value,
                'last': last_value,
                'percent_diff': percent_diff
            }
        else:
            print(f"No data available for {ticker}")
    else:
        print(f"Failed to fetch data for {ticker}. Status Code: {response.status_code}")

"""
# Manually add the specified items for 'DAX' and '000001' for testing purposes (after all I'm doing this on Sunday and the market is close)
data_dict['000001'] = {
    'open': 10.4,
    'last': 10.82,
    'percent_diff': 4.04
}"""


# Create an empty list to store the rows that meet the condition
selected_rows = []

# Set the threshold percentage difference (X)
threshold_percent_lower = -3
threshold_percent_higher = 3

# Check for tickers with percentage difference lower than the threshold
for ticker, data in data_dict.items():
    if data['percent_diff'] < threshold_percent_lower or data['percent_diff'] > threshold_percent_higher:
         selected_rows.append(f"Ticker: {ticker} - Percentage Difference {data['percent_diff']:.2f}%")

# Check if there are any selected rows before sending the message
if selected_rows:
    # Create a message with the selected_rows data
    message_body = "The following Indexes are fluctuating strongly:\n"
    for row in selected_rows:
        message_body += f"{row}\n"
        print(message_body)

    # Send the message via Twilio API
    client = Client(ACCOUNT_SID, AUTH_TOKEN)
    message = client.messages.create(
        body=message_body,
        from_=TWILIO_PHONE_NUMBER,
        to=TARGET_PHONE_NUMBER
    )

    # Print the Twilio message SID for reference
    print(f"Message SID: {message.sid}")

else:
    print("No rows meet the condition, so no message is sent.")


