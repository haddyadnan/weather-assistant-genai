from typing import Dict, Union
import google.genai as genai
from google.genai import types
import gradio as gr
import pickle
import pandas as pd

import argparse

parser = argparse.ArgumentParser(description="Weather Assistant")
parser.add_argument("--api_key", help="Your Google Gemini API key", type=str)
parser.add_argument("--interface", help="Flag to run the model using gradio chat interface default is trye", type=str, default="True")
parser.add_argument("--prompt", help="Provide a prompt to send to the model. Required when --interface is set to false.", type=str, default=None)

try:
    args = parser.parse_args()
    api_key = args.api_key
except Exception as e:
    print("API key not provided. Please run the script with the --api_key argument")

use_gr_interface = eval(args.interface)
if not use_gr_interface:
    if args.prompt is None:
        raise ValueError("Prompt must be provided when --interface is set to false.")
    message = args.prompt

try:
    client = genai.Client(api_key=api_key) 
except Exception as e:
    print("Failed to connect to Gemini API. Please check your API key.")
    raise e

def next_day_weather_forecast(city: str) -> Union[Dict[float, float], str]:
    """
    Provides a weather forecast for a specific city on a specific date.

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
    
    temp_forecast, precip_forecast = temp_model.predict(future)['yhat'].tail(1).iloc[0].round(1), \
        precip_model.predict(future)['yhat'].tail(1).iloc[0].round(1)
    

    return {"predicted_average_temperature": round(float(temp_forecast), 1), "predicted_precipitation": round(float(precip_forecast),1)}

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
    
    temp_forecast, precip_forecast = temp_model.predict(future)['yhat'].tail(1).iloc[0].round(1), \
        precip_model.predict(future)['yhat'].tail(1).iloc[0].round(1)

    return {"predicted_average_temperature": round(float(temp_forecast), 1), "predicted_precipitation": round(float(precip_forecast),1)}

# forecast_data_for_future_date('abidjan', '2025-05-20')
# retrieve_data_from_historical_date('abidjan', '1973-06-01')
# next_day_weather_forecast('abidjan')

config = types.GenerateContentConfig(
    tools=[next_day_weather_forecast, retrieve_data_from_historical_date, forecast_data_for_future_date]
) 

def chat(message: str, history: list = []) -> str:
    """
    Handles the chat interaction with the model.

    Args:
        message (str): The user's message.
        history (list): The conversation history.

    Returns:
        tuple: The AI's response and the updated conversation history.
    """

    print("User message:", message)
    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-05-20",
        contents=message,
        config=config,
    )

    print(response.text) 

    return response.text

if use_gr_interface:

    app = gr.ChatInterface(fn=chat, type="messages", title="Weather Forecast Chatbot",
                        description="Ask about weather forecasts for Abidjan, Berlin, Toronto, or Kazan. "
                                    "You can inquire about next day forecasts, historical data, or future dates beyond the available historical data.",
                        examples=[
                            ["What will the temperature in Abidjan look like on the 20th of May 2025?"],
                            ["What was the weather in Abidjan on the 1st of June 1973?"],
                            ["How much precipitation is expected in Toronto tomorrow?"]
                        ])
    app.launch()
else:
    response = chat(message)
    print("Model response:", response)