import os
from collections import deque
from datetime import datetime

import streamlit as st 
import pandas as pd 
import plotly.express as px 

current_date = datetime.now()

def sort_by_date(df):
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['txn_amount_btc'] = pd.to_numeric(df['txn_amount_btc'])
    df['exchange_rate_usd'] = pd.to_numeric(df['exchange_rate_usd'].replace('[\$,]', '', regex=True))
    sorted = df.sort_values(by='timestamp')
    return sorted

@st.cache_data
def make_df(file):
    file_ext = os.path.splitext(file.name)[1]
    if file_ext == '.csv':
        df = pd.read_csv(file)
    elif file_ext == '.xlsx':
        df = pd.read_excel(file)
    sorted = sort_by_date(df)
    return sorted

@st.cache_data
def calculate_basis(df, method):
    trades = df.values.tolist()
    trade_queue = deque()

    formatted_trades = []

    for trade in trades:
        timestamp, txn_amount_btc, exchange_rate_usd = trade

        if txn_amount_btc < 0:
            remainder = abs(txn_amount_btc)

            while remainder > 0:
                if method == 'FIFO':
                    oldest_trade = trade_queue.popleft()
                elif method == 'LIFO':
                    oldest_trade = trade_queue.pop()
                oldest_amount = oldest_trade[1]
                oldest_price = oldest_trade[2]
                remainder -= oldest_amount 

                if remainder < 0:
                    trade_queue.appendleft((timestamp, abs(remainder), oldest_price))
                else: 
                    pass
        else: 
            trade_queue.append((timestamp, txn_amount_btc, exchange_rate_usd))

        total_btc = 0
        total_cost = 0
        latest_price = trade[2]

        for queue_trade in trade_queue:
            trade_amount = queue_trade[1]
            trade_price = queue_trade[2]
            total_btc += trade_amount
            total_cost += trade_amount * trade_price
        
        cost_basis_usd = total_cost / total_btc
        total_gain_usd = (latest_price - cost_basis_usd) * total_btc

        formatted_trades.append([timestamp, txn_amount_btc, exchange_rate_usd, total_btc, cost_basis_usd, total_gain_usd])

    formatted = pd.DataFrame(
        formatted_trades, 
        columns=['Timestamp', 'BTC Purchased/Sold', 'BTC Price ($)', 'Net BTC', 'Cost Basis ($)', 'Total P&L ($)'])

    return formatted


def main():
    cwd = os.getcwd()
    sample_path = cwd + '/data/sample_data.csv'
    example_file = open(sample_path, 'r')

    st.markdown('# btcBasis')
    st.markdown('##### Calculate and visualize your bitcoin cost basis in seconds.')

    txn_data = st.file_uploader(
        label='___', 
        type=['csv','xlsx'], 
        accept_multiple_files=False,
        key='txn_data',
        help='''Upload a file in .csv or .xlsx format that contains the following columns: timestamp, txn_amount_btc, exchange_rate_usd'''
    )

    st.download_button(
            label='Click to download the accepted file format',
            data=example_file,
            file_name=f'btcBasis_file_format.csv',
            mime='text/csv'
    )

    st.markdown('### Calculate your basis')

    with st.expander('What are LIFO and FIFO?'):
        st.markdown("LIFO: stands for 'last in first out' i.e. your most recent trade is sold first when calculating cost basis.")
        st.markdown("FIFO: stands for 'first in first out' i.e. your very first trade is sold first when calculating cost basis.")
        st.markdown('Read more about LIFO vs FIFO [here](https://www.investopedia.com/articles/02/060502.asp)')

    method = st.radio(
        label='Select a method for basis calculation:',
        options=['LIFO', 'FIFO'],
        index=0
    )

    if txn_data is not None:
        df = make_df(txn_data)
        st.markdown(txn_data.name)
    else:
        sample_file = open(sample_path, 'r')
        df = make_df(sample_file)


    with st.spinner('Please wait while your bais is being calculated...'):

        formatted_df = calculate_basis(df, method)

        with st.expander("View Processed Transaction History"):
            st.dataframe(formatted_df)

        downloadable = formatted_df.to_csv().encode('utf-8')

        st.download_button(
            label='Click to Download Processed Data',
            data=downloadable,
            file_name=f'btcBasis_transaction_history_{current_date}.csv',
            mime='text/csv'
        )

        metrics = st.multiselect(
            label='Select values to graph against time',
            options=['BTC Purchased/Sold', 'BTC Price ($)', 'Net BTC', 'Cost Basis ($)', 'Total P&L ($)'],
            default=['BTC Price ($)', 'Cost Basis ($)']
        )
        fig = px.line(
            formatted_df,
            x='Timestamp',
            y=metrics
        )
        st.markdown('### Visualize your basis')
        st.plotly_chart(fig)

    st.markdown('''___''')

    col1, col2 = st.columns([2,3])

    with col1:
        st.markdown('Source code: [btcBasis](https://github.com/sambradbury/btcBasis)')
        st.markdown('See my work on [Github](https://github.com/sambradbury)')
        st.markdown('Follow me on Twitter [@sam_bradbury_](https://twitter.com/sam_bradbury_)')
        st.markdown("""
            Disclosure: this app does not log or retain any data. Follow the instructions [here]() if you'd like to run it locally""")

    with col2:
        st.markdown('If you like this app please consider sending me some sats.')
        with st.expander(label='Donate'):
            st.markdown('BTC Address:')
            st.code('bc1q433z7nhkp58a63l28za0um04lrmu6e8l7lj8e0')
            st.markdown('')

if __name__ == '__main__':
    main()
