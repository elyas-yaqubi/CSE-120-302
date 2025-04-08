import streamlit as st
import pandas as pd
import openai

from dotenv import load_dotenv
import os
load_dotenv()  # This loads the .env file

openai.api_key = os.getenv("OPENAI_API_KEY")
# Set up Streamlit app
st.title("Excel Data Chatbot")
st.write("Upload an Excel (.xlsx) dataset and ask questions about it.")

# File uploader (Only allows .xlsx files)
data_file = st.file_uploader("Upload an Excel file", type=["xlsx"])

if data_file:
    try:
        # Read the Excel file
        df = pd.read_excel(data_file, engine="openpyxl")

        # Display dataset preview
        st.write("### Preview of the dataset:")
        st.dataframe(df.head())

        # User question input
        user_question = st.text_input("Ask a question about the dataset:")

        if user_question:
            # Construct the prompt for OpenAI
            prompt = f"Here is a dataset:\n{df.head().to_string()}\n\nAnswer the following question based on this data:\n{user_question}"

            # OpenAI API call
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a data analyst."},
                    {"role": "user", "content": prompt},
                ]
            )

            # Display response
            answer = response["choices"][0]["message"]["content"]
            st.write("### Answer:")
            st.write(answer)

    except Exception as e:
        st.error(f"Error reading the Excel file: {e}")
