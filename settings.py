import os

# IBM Bluemix Weather Company API Credentials
WEATHER_ENDPOINT = 'https://{username}:{password}@twcservice.au-syd.mybluemix.net/api/weather/v1/geocode/{latitude}/{longitude}/forecast/hourly/48hour.json'
WEATHER_USERNAME = os.getenv('WEATHER_COMPANY_USERNAME', default='')
WEATHER_PASSWORD = os.getenv('WEATHER_COMPANY_PASSWORD', default='')

POP_THRESHOLD_HARDLY = 10
POP_THRESHOLD_MAYBE = 30
POP_THRESHOLD_LIKELY = 50
POP_THRESHOLD_ALMOST = 80
FORECAST_LENGTH = 12
