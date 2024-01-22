# import libraries
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import seaborn as sns
import requests
from requests.auth import HTTPBasicAuth
import streamlit as st
from dotenv import load_dotenv
pd.options.display.float_format = '{:,.2f}'.format


st.title('Portfolio Balance')

# Implementing Basic Authentication. THIS ONE IS RECOMENDED.
#a key benefit of using Basic Auth is that your request can reliably  
#take advantage of COVALENT caching mechanism for better query performance."""

# Always protect your API keys, ideally using environment variables

# load api key
load_dotenv()
api_key = os.getenv('COVALENT_API_KEY')

# Define a function to fetch the balance of a given wallet from the Covalent API

def get_wallet_balance(walletAddress):
    """
    Fetches the balance of a given wallet from the Covalent API and returns it as a DataFrame.

    Parameters:
    walletAddress (str): The address of the wallet to fetch the balance for.

    Returns:
    df (pd.DataFrame): A DataFrame containing the balance information for the wallet.
    """

    # Construct the URL for the API request
    url = f"https://api.covalenthq.com/v1/eth-mainnet/address/{walletAddress}/balances_v2/?quote-currency=USD"

    # Send a GET request to the API
    response = requests.get(url, auth=HTTPBasicAuth(api_key, ''))

    # Parse the JSON response
    data = response.json()

    # Convert the relevant part of the JSON response into a DataFrame
    df = pd.DataFrame(data['data']['items'])

    # Return the DataFrame
    return df


# Get the wallet address from the user
wallet_input = st.text_input("Please enter a wallet address")

# Fetch the balance of the wallet
if wallet_input:
    df = get_wallet_balance(wallet_input.strip())  # strip() is used to remove leading/trailing spaces
    # Convert balance to numeric
    df['balance'] = pd.to_numeric(df['balance'], errors='coerce', downcast='float').round(2)
    # Create a new column for pretty_balance = balance/(10^contract_decimals)
    df['pretty_balance'] = df['balance'] / (10 ** df['contract_decimals'])
    # Keep only relevant columns
    df = df[['contract_name', 'contract_ticker_symbol', 'pretty_balance', 'pretty_quote']]
    # Rename columns
    df.columns = ['Name', 'Asset', 'Balance', 'Value']
    # Remove the dollar sign and commas
    df['Value'] = df['Value'].replace({'\$': '', ',': ''}, regex=True)
    # Convert the column to float using the recommended syntax
    df['Value'] = pd.to_numeric(df['Value'], errors='coerce')
    # Filter out assets with zero or negative balance
    df = df[df['Value'] > 0.00]
    
    # Calculate Total Portfolio Value
    total_portfolio_value = df['Value'].sum()
    # vizualize total portfolio value
    #print(f'Total Portfolio Value: ${total_portfolio_value:,.2f}')

    # Create a new DataFrame where values less than 100 are grouped into 'Other'
    df_grouped = df.copy()
    df_grouped.loc[df['Value'] < 100, 'Asset'] = 'Other'
    df_grouped = df_grouped.groupby('Asset').sum(numeric_only=True).sort_values(by='Value', ascending=False)

    # Create a donut chart with top assets

    # Define a custom function to display values in dollars
    def absolute_value(val):
        a  = np.round(val/100.*df_grouped['Value'].sum(), 0)
        return '${:,.0f}'.format(a)

    # Set the font size
    plt.rcParams['font.size'] = 10

    # Assuming df is your DataFrame
    explode = (0.05,) * len(df_grouped)

    # Create a figure and set different background
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_facecolor('none')  # Make the background transparent
    # Create a pie chart
    df_grouped['Value'].plot(kind='pie', y='Value',
                            wedgeprops={'width':0.3}, 
                            autopct=absolute_value,
                            ax=ax,
                            labels=df_grouped.index, 
                            pctdistance=1.12, 
                            labeldistance=1.3, 
                            colors=sns.color_palette("Paired"),
                            #explode=explode,
                            )

    # Display the total portfolio value in the middle of the donut
    ax.text(0, 0, f'${total_portfolio_value:,.2f}', ha='center', va='center', fontsize=12, color='black')
    plt.title('')
    plt.ylabel('')
    plt.show()
    st.pyplot(fig)

    # Create a DataFrame for the table
    dataset = df.set_index('Asset',).round(2)
    dataset.index.name = 'Coin'
    dataset['Value'] = dataset['Value'].apply(lambda x: '${:,.2f}'.format(x))
    dataset['Balance'] = dataset['Balance'].round(2)
    # Display the DataFrame
    st.table(dataset)

   