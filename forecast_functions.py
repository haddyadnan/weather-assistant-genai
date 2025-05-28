"""
All functions related to forecasting.
"""

from typing import Union, Dict
import pickle
import pandas as pd


# Include more clarity to avoid overlap with future_date_forecast function
# Next day is made to be absolute - i.e the day after the data ends
# Not relative to the current date i.e {today.date + 1 day}
# Might need a rethink but currently this is the intent
def next_day_weather_forecast(city: str) -> Union[Dict[float, float], str]:
    """
    Provides a weather forecast for a specific city for the next day.
    Uncertainty Estimation:
    The forecast includes a 95% prediction interval for each value.
    This interval (shown as *_pi_lower and *_pi_upper) represents the range within which a future observation
    is expected to fall, considering uncertainty in trend, seasonality, and noise.


    Args:
        city (str): The name of the city for which to retrieve the forecast. 
            Only the following cities are supported: "Abidjan", "Berlin", "Toronto", "Kazan".
    Note:
        The function only supports forecasts for the following cities: 
        Abidjan, Berlin, Toronto, and Kazan. Providing any other city will result in an error or empty response.

    Returns:
        A weather forecast including temperature, precipitation in mm for the given location and next day.
    """

    city = city.lower()
    if city not in ['abidjan', 'berlin', 'toronto', 'kazan']:
        return f"City: {city} currently not supported"

    with open(f'models/{city}_precip_model.pkl', 'rb') as PM:
        precip_model = pickle.load(PM)

    with open(f'models/{city}_temp_model.pkl', 'rb') as TM:
        temp_model = pickle.load(TM)

    future = temp_model.make_future_dataframe(periods=1)
    
    temp, precip = temp_model.predict(future), precip_model.predict(future)
    
    temp_forecast, precip_forecast = temp['yhat'].tail(1).iloc[0].round(1), \
        precip['yhat'].tail(1).iloc[0].round(1)
    
    temp_forecast_lower_bound, precip_forecast_lower_bound = temp['yhat_lower'].tail(1).iloc[0].round(1), \
        precip['yhat_lower'].tail(1).iloc[0].round(1)

    temp_forecast_upper_bound, precip_forecast_upper_bound = temp['yhat_upper'].tail(1).iloc[0].round(1), \
        precip['yhat_upper'].tail(1).iloc[0].round(1)

    return {"predicted_average_temperature": round(float(temp_forecast), 1),
            "predicted_average_temperature_lower_bound": round(float(temp_forecast_lower_bound), 1),
            "predicted_average_temperature_upper_bound": round(float(temp_forecast_upper_bound), 1),
            "predicted_precipitation": round(float(precip_forecast),1),
            "predicted_precipitation_lower_bound": round(float(precip_forecast_lower_bound), 1),
            "predicted_precipitation_upper_bound": round(float(precip_forecast_upper_bound), 1),
           }
def retrieve_data_from_historical_date(city: str, date: str) -> Union[Dict[float, float], str]:

    """
    Retrieves historical weather data for a specific city on a given date.

    Args:
        city (str): The name of the city to retrieve historical weather data for. 
            Only the following cities are supported: "Abidjan", "Berlin", "Toronto", and "Kazan".
        
        date (str): The date of interest in "YYYY-MM-DD" format.

    Note:
        - Historical data availability varies by city.
        - Supported data ranges:
            • Abidjan: 1973-06-01 to 2023-09-05  
            • Kazan: 1881-01-01 to 2023-09-05  
            • Toronto: 2002-06-04 to 2023-08-28  
            • Berlin: 1931-01-01 to 2023-09-03

        - If the requested date is outside the historical range for the given city, 
          a forecast will be generated instead.
        
        - Providing a city outside the supported list will result in an error or empty response.
    """

    city = city.lower()
    if city not in ['abidjan', 'berlin', 'toronto', 'kazan']:
        return f"City: {city}, is currently not supported"

    try:
        date = pd.to_datetime(date)
    except:
        return "Invalid Date Format"

    df = pd.read_csv("data/combined_data.csv")

    df['date'] = pd.to_datetime(df.date)
    
    val = df[(df.city_name==city) & (df.date == date)]
    if len(val) < 1:
        return f"Historical data for {city} on {date} is not available"
        
    return {'average_temperature': float(val['avg_temp_c'].iloc[0]), 'precipitation_mm': float(val['precipitation_mm'].iloc[0])}

def forecast_data_for_future_date(city: str, date: str) -> Union[Dict[float, float], str]:

    from datetime import datetime
    today = datetime.today()
    
    f"""
    Generates a weather forecast for a future date beyond the available historical data for supported cities.
    Uncertainty Estimation:
    The forecast includes a 95% prediction interval for each value.
    This interval (shown as *_pi_lower and *_pi_upper) represents the range within which a future observation
    is expected to fall, considering uncertainty in trend, seasonality, and noise.

    Args:
        city (str): The name of the city to generate the forecast for. 
            Supported cities are: "Abidjan", "Berlin", "Toronto", and "Kazan".
        
        date (str): The target date for the forecast in "YYYY-MM-DD" format. 
            For reference, today's date is {today}.

    Notes:
        - Historical weather data is available only within the following ranges:
            • Abidjan: 1973-06-01 to 2023-09-05  
            • Kazan: 1881-01-01 to 2023-09-05  
            • Toronto: 2002-06-04 to 2023-08-28  
            • Berlin: 1931-01-01 to 2023-09-03

        - The forecast will only be generated if the requested date is **beyond** the historical range for the given city.

        - If the provided city is not supported, the function will return an error or empty response.

        - If a relative date (e.g., "tomorrow", "yesterday") is given, it will be resolved using today's date: {today}.

        - If a date is provided without a year (e.g., "March 29"), the current year from today's date ({today.year}) will be assumed.
    """


    city = city.lower()
    if city not in ['abidjan', 'berlin', 'toronto', 'kazan']:
        return f"City: {city}, is currently not supported"

    try:
        date = pd.to_datetime(date)
    except:
        return "Invalid Date Format"

    df = pd.read_csv("data/combined_data.csv")

    df['date'] = pd.to_datetime(df.date)

    with open(f'models/{city}_precip_model.pkl', 'rb') as PM:
        precip_model = pickle.load(PM)

    with open(f'models/{city}_temp_model.pkl', 'rb') as TM:
        temp_model = pickle.load(TM)

    df[df.city_name == city]['date'].max()

    period = (date - (df[df.city_name==city]['date']).max()).days

    future = temp_model.make_future_dataframe(periods=period)
    
    temp, precip = temp_model.predict(future), precip_model.predict(future)
    
    temp_forecast, precip_forecast = temp['yhat'].tail(1).iloc[0].round(1), \
        precip['yhat'].tail(1).iloc[0].round(1)
    
    temp_forecast_lower_bound, precip_forecast_lower_bound = temp['yhat_lower'].tail(1).iloc[0].round(1), \
        precip['yhat_lower'].tail(1).iloc[0].round(1)

    temp_forecast_upper_bound, precip_forecast_upper_bound = temp['yhat_upper'].tail(1).iloc[0].round(1), \
        precip['yhat_upper'].tail(1).iloc[0].round(1)

    return {"predicted_average_temperature": round(float(temp_forecast), 1),
            "predicted_average_temperature_lower_bound": round(float(temp_forecast_lower_bound), 1),
            "predicted_average_temperature_upper_bound": round(float(temp_forecast_upper_bound), 1),
            "predicted_precipitation": round(float(precip_forecast),1),
            "predicted_precipitation_lower_bound": round(float(precip_forecast_lower_bound), 1),
            "predicted_precipitation_upper_bound": round(float(precip_forecast_upper_bound), 1),
           }
# forecast_data_for_future_date('abidjan', '2025-05-20')
# retrieve_data_from_historical_date('abidjan', '1973-06-01')
# next_day_weather_forecast('abidjan')