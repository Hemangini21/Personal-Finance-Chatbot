import os
import yfinance as yf
import streamlit as st
import pandas as pd
import plotly.graph_objs as go

# Streamlit Page Configuration
st.set_page_config(page_title="Stock Analysis Pro", layout="wide")
st.title("📈 Stock Analysis Pro")

# Cache stock data to improve performance
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_stock_data(symbol: str, period: str = '1y'):
    try:
        # First Attempt: Using Ticker object
        stock = yf.Ticker(symbol)
        hist = stock.history(period=period)

        # Second Attempt: Using yf.download() if the first method fails
        if hist.empty:
            hist = yf.download(symbol, period=period)

        # If still empty, return an error
        if hist.empty:
            return {'error': f"⚠️ No stock data found for '{symbol}'. Ensure the symbol is correct and try again."}

        # Fetch additional stock details safely
        info = stock.info if hasattr(stock, 'info') else {}
        financials = stock.financials if hasattr(stock, 'financials') else pd.DataFrame()
        recommendations = stock.recommendations if hasattr(stock, 'recommendations') else pd.DataFrame()

        return {
            'history': hist,
            'info': info,
            'financials': financials,
            'recommendations': recommendations,
            'error': None
        }
    except Exception as e:
        return {'error': f"⚠️ API Error: {str(e)}"}

def create_stock_chart(data, symbol):
    """Generate a candlestick chart for the stock price."""
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name='Price'
    ))
    fig.update_layout(
        title=f'{symbol} Stock Price',
        xaxis_title='Date',
        yaxis_title='Price',
        xaxis_rangeslider_visible=False,
        height=600
    )
    return fig

def display_company_info(info):
    """Display company details in a DataFrame format."""
    if not info:
        return "No company information available"

    metrics = {
        'Sector': info.get('sector', 'N/A'),
        'Industry': info.get('industry', 'N/A'),
        'Market Cap': f"${info.get('marketCap', 'N/A'):,}" if info.get('marketCap') else 'N/A',
        'PE Ratio': info.get('trailingPE', 'N/A'),
        'EPS': info.get('trailingEps', 'N/A'),
        'Dividend Yield': f"{info.get('dividendYield', 0)*100:.2f}%" if info.get('dividendYield') else '0%'
    }

    return pd.DataFrame.from_dict(metrics, orient='index', columns=['Value'])

def generate_investment_analysis(symbol, data):
    """Generate a basic investment analysis report."""
    hist = data['history']
    info = data['info']

    if hist.empty:
        return "⚠️ Insufficient data for analysis"

    # Basic technical analysis
    latest_close = hist['Close'][-1]
    sma_50 = hist['Close'].rolling(window=50).mean()[-1]
    sma_200 = hist['Close'].rolling(window=200).mean()[-1]

    analysis = f"""
    Investment Analysis for {symbol}

    Current Price: ${latest_close:.2f}  
    50-Day SMA: ${sma_50:.2f}  
    200-Day SMA: ${sma_200:.2f}  

    Technical Outlook:  
    {'🔼 Bullish' if sma_50 > sma_200 else '🔽 Bearish'} crossover signal  
    """

    if info:
        analysis += f"""
        Fundamental Analysis:
        - Sector: {info.get('sector', 'N/A')}  
        - Market Cap: ${info.get('marketCap', 'N/A'):,}  
        - P/E Ratio: {info.get('trailingPE', 'N/A')}  
        - ROE: {info.get('returnOnEquity', 'N/A')}  
        """

    analysis += "\n\n🔔 Recommendation: Always consult with a financial advisor before making investment decisions."

    return analysis

# Sidebar Controls
with st.sidebar:
    st.header("⚙️ Settings")
    symbol = st.text_input("Stock Symbol", "AAPL").upper()
    period = st.selectbox("Analysis Period", ['1d', '5d', '1mo', '3mo', '6mo', '1y', '5y'], index=5)
    analysis_type = st.selectbox("Analysis Type", ['Technical', 'Fundamental', 'Full Report'])

# Fetch & Analyze Data
if st.sidebar.button("🔍 Analyze"):
    data = get_stock_data(symbol, period)

    if data['error']:
        st.error(data['error'])
    else:
        # Create tabs for different sections
        tab1, tab2, tab3 = st.tabs(["📊 Price Chart", "🏢 Company Info", "📈 Investment Analysis"])

        with tab1:
            st.plotly_chart(create_stock_chart(data['history'], symbol), use_container_width=True)

        with tab2:
            st.subheader("📄 Company Overview")
            st.dataframe(display_company_info(data['info']), use_container_width=True)

            if not data['financials'].empty:
                with st.expander("📜 Financial Statements"):
                    st.write("Income Statement")
                    st.dataframe(data['financials'], use_container_width=True)

        with tab3:
            analysis = generate_investment_analysis(symbol, data)
            st.markdown(analysis)

            if not data['recommendations'].empty:
                with st.expander("📊 Analyst Recommendations"):
                    st.dataframe(data['recommendations'].tail(10), use_container_width=True)
else:
    st.info("👈 Enter a stock symbol and click 'Analyze' to get started")

# Add some style
st.markdown("""
<style>
    .stDataFrame { 
        font-size: 0.9em;
    }
    .st-b7 { 
        color: white;
    }
</style>
""", unsafe_allow_html=True)
