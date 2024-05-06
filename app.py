import streamlit as st
import matplotlib.pyplot as plt
from tabulate import tabulate
import os
import re
from bs4 import BeautifulSoup
from sec_edgar_downloader import Downloader
import google.generativeai as genai



genai.configure(api_key="AIzaSyBnr4VZcv0yG2hQp5bUCu670z6qWs8CKr0")
def download_10k_filings(ticker, after_date, before_date):
    # Specify the base directory where filings will be stored
     # Change this to your desired base directory
    base_dir = os.getcwd()
    target_dir = os.path.join(base_dir, "sec-edgar-filings", "10-K", ticker)

    # Initialize the downloader
    dl = Downloader("VIT", "akanksha.dhar2020@vitstudent.ac.in")

    try:
        # Download the 10-K filings for the given ticker within the date range
        dl.get("10-K", ticker, after=after_date, before=before_date)
        print(f"Downloading 10-K filings for {ticker} between {after_date} and {before_date}...")
        #while not os.path.exists(target_dir) or len(os.listdir(target_dir)) == 0:
            #continue  # Wait until the directory is created and populated


        print(f"Successfully downloaded 10-K filings for {ticker} between {after_date} and {before_date}")
        return True  # Return True if download is successful
    except Exception as e:
        print(f"Error downloading 10-K filings for {ticker}: {e}")
        return False  # Return False if download fails
def answer_question(prompt):
    # Generate an answer using Gemini API based on the prompt
    response = genai.generate_text(prompt=prompt)
    
    # Extract the result from the response
    result = response.result
    
    return result
# Function to remove HTML tags and special characters from text content
def clean_text(text):
    try:
        # Specify the encoding explicitly when reading the file
        cleaned_text = BeautifulSoup(text, 'html.parser').get_text()
    except Exception as e:
        # Handle parsing errors by trying a different parser
        try:
            cleaned_text = BeautifulSoup(text, 'lxml').get_text()
        except Exception as e:
            cleaned_text = ''  # Return empty string if parsing fails

    cleaned_text = re.sub(r'[^\w\s.,]', '', cleaned_text)
    return cleaned_text.strip()

# Function to extract financial information from text
def extract_financial_info(text):
    financial_data = {}

    # Define regex patterns for common financial metrics
    financial_patterns = {
        'revenue': r'(?:total\s+)?revenue(?:\s+in\s+millions)?\s+([\d,.]+)',
        'net_income': r'net\s+income(?:\s+in\s+millions)?\s+([\d,.]+)',
        'total_assets': r'total\s+assets(?:\s+in\s+millions)?\s+([\d,.]+)',
        'total_liabilities': r'total\s+liabilities(?:\s+in\s+millions)?\s+([\d,.]+)'
        # Add more patterns for other metrics as needed
    }

    # Clean text content
    cleaned_text = clean_text(text)

    # Extract financial metrics using regex from cleaned text
    for metric, pattern in financial_patterns.items():
        match = re.search(pattern, cleaned_text, re.IGNORECASE)
        if match:
            try:
                # Try to convert the matched value to float
                financial_data[metric] = float(match.group(1).replace(',', ''))
            except ValueError:
                # Handle case where conversion to float fails
                financial_data[metric] = None
        else:
            financial_data[metric] = None

    return financial_data

# Function to analyze financial data and generate insights using Gemini API
def analyze_financial_data(financial_data):
    insights = genai.generate_text(prompt=f"Analyze financial data: {financial_data}. Give insights based on the financial data.")
    return insights
# Visualization function for financial metrics over years
def visualize_financial_metrics(ticker, processed_financial_data):
    # Define the list of financial metrics to include in the visualization
    financial_metrics = ['revenue', 'net_income', 'total_assets', 'total_liabilities']

    # Check if the specified ticker exists in the processed financial data
    if ticker in processed_financial_data:
        years_data = processed_financial_data[ticker]

        # Prepare data for plotting
        years = sorted(years_data.keys())
        num_metrics = len(financial_metrics)

        # Initialize subplots for multiple metrics
        fig, axes = plt.subplots(num_metrics, 3, figsize=(18, 12))
        fig.suptitle(f"Financial Metrics Over Years for {ticker}", fontsize=16)

        # Iterate over each financial metric and plot
        for i, metric in enumerate(financial_metrics):
            metric_values = []
            for year in years:
                financial_info = years_data[year]['financial_info']
                metric_value = financial_info.get(metric, None)
                metric_values.append(metric_value)

            # Line plot
            axes[i, 0].plot(years, metric_values, marker='o', linestyle='-', color='b')
            axes[i, 0].set_ylabel(metric.capitalize())
            axes[i, 0].set_xlabel("Year")
            axes[i, 0].grid(True)

            # Scatter plot (with random jitter for better visualization)
            jitter_years = [year + 0.2 * (i - 1.5) for year in years]
            axes[i, 1].scatter(jitter_years, metric_values, color='g', alpha=0.7)
            axes[i, 1].set_ylabel(metric.capitalize())
            axes[i, 1].set_xlabel("Year (with jitter)")
            axes[i, 1].grid(True)

            # Stacked bar chart (comparing assets and liabilities)
            assets = [years_data[year]['financial_info'].get('total_assets', 0) or 0 for year in years]
            liabilities = [years_data[year]['financial_info'].get('total_liabilities', 0) or 0 for year in years]
            axes[i, 2].bar(years, assets, color='b', label='Total Assets')
            axes[i, 2].bar(years, liabilities, color='r', label='Total Liabilities', bottom=assets)
            axes[i, 2].set_ylabel("Amount")
            axes[i, 2].set_xlabel("Year")
            axes[i, 2].legend()
            axes[i, 2].grid(True)

        # Adjust layout and display plot
        plt.tight_layout(rect=[0, 0, 1, 0.96])  # Adjust top margin for suptitle
        st.pyplot(fig)  # Display the plot in Streamlit

    else:
        st.write(f"No data found for ticker: {ticker}")
# Define the Streamlit app
def main():
    st.title("Financial Insights App")

    # User input for company ticker
    ticker = st.text_input("Enter company ticker:")
    # Date selection using date_input

    after_date = st.text_input("Enter After Date (YYYY-MM-DD)", "1995-01-01")
    before_date = st.text_input("Enter Before Date (YYYY-MM-DD)", "1998-01-01")

    # Display the entered dates
    st.write(f"You entered After Date: {after_date}")
    st.write(f"You entered Before Date: {before_date}")

    
    st.write(f"Download started for {ticker} from {after_date} to {before_date}")
    

    # Download 10-K filings for the specified ticker and date range
    if download_10k_filings(ticker, after_date, before_date):
        st.write("Download successful!")
        
        if ticker:
           
            base_dir = os.getcwd()
            
            target_dir = os.path.join(base_dir, "sec-edgar-filings")
    # Specify the base directory where ticker folders are located
            ticker_dir = os.path.join(target_dir,ticker)
            processed_financial_data = {}
            longdir=os.path.join(ticker_dir,'10-K')
            st.write ("Extracting financial data for analysis and generating insights...")
            

            # Loop through each company directory inside the specified ticker directory
            for company_dir in os.listdir(longdir):
                company_path = os.path.join(longdir, company_dir)
                
                if os.path.isdir(company_path):
                
                    # Extract year from the company directory name (e.g., '0000320193-22-000108' => '2022')
                    year_match = re.search(r'-(\d{2})-', company_dir)
                    
                    if year_match:
                        
                        
                        year_suffix = year_match.group(1)  # Extract two-digit year suffix
                        if int(year_suffix) <= 23:
                            year = 2000 + int(year_suffix)  # Convert to full four-digit year (e.g., 22 => 2022)
                        else:
                            year = 1900 + int(year_suffix)  # Convert to full four-digit year for older files

                        # Find the full-submission.txt file (assuming it's the only txt file in the directory)
                        for file in os.listdir(company_path):
                            
                            if file.endswith('.txt'):
                               
                                with open(os.path.join(company_path, file), 'r', encoding='utf-8') as f:
                                    text_content = f.read()
                                    
                                    # Extract financial information
                                    financial_info = extract_financial_info(text_content)
                                    
                                    # Analyze financial data (using placeholder function)
                                    financial_insights = analyze_financial_data(financial_info)
                                    # Store processed data for the specified ticker and year
                                   
                                    if ticker not in processed_financial_data:
                                        processed_financial_data[ticker] = {}
                                    processed_financial_data[ticker][year] = {
                                        'financial_info': financial_info,
                                        'financial_insights': financial_insights
                                    }
                                break  # Stop after reading the first .txt file

            # Display financial details in a table using tabulate
           

# Assuming processed_financial_data contains the processed financial data

# Check if the specified ticker exists in the processed financial data
            if ticker in processed_financial_data:
                years_data = processed_financial_data[ticker]

                # Prepare data for the table
                table_data = []
                financial_metrics = ['revenue', 'net_income', 'total_assets', 'total_liabilities']

                # Prepare the header row for the table
                header_row = ["Year"] + financial_metrics + ["Financial Insights"]
                table_data.append(header_row)

                # Iterate over each year and its corresponding data
                for year, data in sorted(years_data.items()):
                    financial_info = data['financial_info']
                    financial_insights = data.get('financial_insights', None)

                    # Create a row for each year's financial data
                    row_data = [year]

                    # Append financial metrics to the row data
                    for metric in financial_metrics:
                        row_data.append(financial_info.get(metric, None))

                    # Append financial insights to the row data
                    
                    if financial_insights:
                        result = financial_insights.result
                        row_data.append(result)
                    else:
                        row_data.append(None)  # Use None if insights are not available

                    # Append the row data to the table data
                    table_data.append(row_data)

                # Display the table using Streamlit
                st.header(f"Financial Details for Ticker: {ticker}")
                st.table(table_data)

            else:
                st.write(f"No data found for ticker: {ticker}")
        st.header(f"Financial Visualisations for Ticker: {ticker}")        


        visualize_financial_metrics(ticker, processed_financial_data) 
        
                # Get the answer using the defined function
        st.header("Interesting Observations in Financial Analysis")
        answer_obs=answer_question(prompt=f"Is there any sharp decline or increase in any year between 1995-2023 in the financial metrics of {ticker}? What insight do we get from that? ")   
        st.write(answer_obs) 
        answer = answer_question(prompt = f"What insights do you get from the financial metrics in the 10k filings of {ticker} from 1995 to 2023. ")
        st.header(f"Overall Insights and Analysis of {ticker}")
        st.write(answer)
        
        st.header("Ask a question")
        # Construct a prompt/question based on available financial data
        prompt_ask = st.text_input("Enter your question related to the financial analysis")

        # Get the answer using the defined function
        answer_ask = answer_question(prompt_ask)
        st.write(answer_ask)
  
    else:
        print(f"Failed to download 10-K filings for {ticker}")



if __name__ == "__main__":
    main()
