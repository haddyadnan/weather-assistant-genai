import google.genai as genai
from google.genai import types
import gradio as gr

import argparse
from forecast_functions import retrieve_data_from_historical_date, forecast_data_for_future_date, next_day_weather_forecast

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