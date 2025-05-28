"""
Access the model and run inference directly on the model with a given input.
"""

import argparse
from forecast_functions import forecast_data_for_future_date, retrieve_data_from_historical_date, next_day_weather_forecast

parser = argparse.ArgumentParser(description="Inference script for weather forecasting using Google Gemini API.")
parser.add_argument( 
    "--model", 
    type=str, 
    help="Select the forecast model to use:\n" \
        "  'nd' - Next day forecast (requires city name)\n" \
        "  'ff' - Future date forecast (requires city name and date)\n" \
        "  'rh' - Retrieve historical data (requires city name and date)\n" \
        "Default is 'nd' (next day forecast).", 
    default="nd")

parser.add_argument(
    "--city",
    help="City name for which to forecast the weather. Required for all models. NB: Supported cities are: kazan, abidjan, toronto, berlin",
    type=str,
    required=True,
)
parser.add_argument(
    "--date",
    help="Future date for which to forecast the weather (format: YYYY-MM-DD). Required for 'ff' and rh model.",
    type=str,
    default=None,
)

args = parser.parse_args()
if args.model == "nd":
    if not args.city:
        raise ValueError("City name is required for next day forecast.")
    print(next_day_weather_forecast(args.city))
elif args.model == "ff":
    if not args.city or not args.date:
        raise ValueError("City name and date are required for future date forecast.")
    print(forecast_data_for_future_date(args.city, args.date))
elif args.model == "rh":
    if not args.city or not args.date:
        raise ValueError("City name and date are required for retrieving historical data.")
    print(retrieve_data_from_historical_date(args.city, args.date))
else:
    raise ValueError(
        "Invalid model selected. Choose from 'nd' (next day), 'ff' (future date), or 'rh' (historical data)."
    )
