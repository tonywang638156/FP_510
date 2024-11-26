import os
import pandas as pd
import requests
from datetime import datetime, timedelta
import yfinance as yf
from transformers import pipeline
import matplotlib.pyplot as plt
import seaborn as sns

# Function to collect stock data
def collect_stock_data():
    stock_symbol = "AAPL"
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    stock_data = yf.download(stock_symbol, start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))
    stock_data.reset_index(inplace=True)
    stock_data.rename(columns={"Date": "date"}, inplace=True)
    return stock_data

# Function to fetch news articles
def fetch_news():
    news_api_key = ""
    news_base_url = "https://newsapi.org/v2/everything"

    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    top_articles = []

    for i in range(30):
        date = start_date + timedelta(days=i)
        next_date = date + timedelta(days=1)
        news_params = {
            'q': 'apple stock',
            'language': 'en',
            'sortBy': 'popularity',
            'from': date.strftime('%Y-%m-%d'),
            'to': next_date.strftime('%Y-%m-%d'),
            'apiKey': news_api_key,
            'pageSize': 3
        }
        response = requests.get(news_base_url, params=news_params)
        if response.status_code == 200:
            news_data = response.json()
            articles = news_data.get('articles', [])
            if articles:
                most_relevant_article = articles[0]
                top_articles.append({
                    "date": date.strftime('%Y-%m-%d'),
                    "title": most_relevant_article.get("title"),
                    "description": most_relevant_article.get("description"),
                    "url": most_relevant_article.get("url"),
                    "source": most_relevant_article.get("source", {}).get("name"),
                    "publishedAt": most_relevant_article.get("publishedAt"),
                })
    return pd.DataFrame(top_articles)

# Function to add sentiment analysis
def analyze_sentiment(news_df):
    sentiment_pipeline = pipeline("sentiment-analysis")
    
    def get_sentiment_huggingface(text):
        if pd.isna(text):
            return None
        result = sentiment_pipeline(text)
        return result[0]['label']
    
    news_df['title_sentiment_hf'] = news_df['title'].apply(get_sentiment_huggingface)
    news_df['description_sentiment_hf'] = news_df['description'].apply(get_sentiment_huggingface)
    return news_df

# Function to calculate RSI
def calculate_rsi(data, window=5):
    delta = data['Close'].diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# Function to merge and compute financial indicators
def merge_and_calculate(stock_data, news_data):
    stock_data['date'] = pd.to_datetime(stock_data['date']).dt.date
    news_data['publishedAt'] = pd.to_datetime(news_data['publishedAt'])
    news_data['date'] = news_data['publishedAt'].dt.date
    
    merged_data = pd.merge(stock_data, news_data, on='date', how='left')
    merged_data['Close'] = pd.to_numeric(merged_data['Close'], errors='coerce')
    merged_data['SMA'] = merged_data['Close'].rolling(window=5).mean()
    merged_data['EMA'] = merged_data['Close'].ewm(span=5, adjust=False).mean()
    merged_data['RSI'] = calculate_rsi(merged_data)
    return merged_data

# Function to visualize data
def visualize_data(data):
    data['date'] = pd.to_datetime(data['date'])
    data.dropna(subset=['title_sentiment_hf', 'description_sentiment_hf'], inplace=True)
    sentiment_mapping = {'POSITIVE': 1, 'NEGATIVE': -1, 'NEUTRAL': 0}
    data['title_sentiment_hf'] = data['title_sentiment_hf'].map(sentiment_mapping)
    data['description_sentiment_hf'] = data['description_sentiment_hf'].map(sentiment_mapping)

    correlation_matrix = data.corr()
    plt.figure(figsize=(10, 6))
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt=".2f")
    plt.title('Correlation Matrix')
    plt.savefig('correlation_matrix.png')
    plt.close()

    plt.figure(figsize=(10, 5))
    sns.histplot(data['title_sentiment_hf'], bins=3, kde=False, label='Title Sentiment', color='red')
    sns.histplot(data['description_sentiment_hf'], bins=3, kde=False, label='Description Sentiment', color='green')
    plt.title('Distribution of Sentiment Scores')
    plt.xlabel('Sentiment Score')
    plt.ylabel('Frequency')
    plt.legend()
    plt.savefig('sentiment_score_distribution.png')
    plt.close()

    plt.figure(figsize=(10, 6))
    sns.boxplot(x='title_sentiment_hf', y='Adj Close', data=data)
    plt.title('Stock Prices by Title Sentiment')
    plt.xlabel('Title Sentiment')
    plt.ylabel('Adjusted Close Price')
    plt.savefig('stock_prices_by_title_sentiment.png')
    plt.close()

    plt.figure(figsize=(10, 6))
    sns.boxplot(x='description_sentiment_hf', y='Adj Close', data=data)
    plt.title('Stock Prices by Description Sentiment')
    plt.xlabel('Description Sentiment')
    plt.ylabel('Adjusted Close Price')
    plt.savefig('stock_prices_by_description_sentiment.png')
    plt.close()

if __name__ == "__main__":
    if not os.path.exists("final_data.csv"):
        stock_data = collect_stock_data()
        news_data = fetch_news()
        news_data = analyze_sentiment(news_data)
        final_data = merge_and_calculate(stock_data, news_data)
        final_data.to_csv("final_data.csv", index=False)
        visualize_data(final_data)
        print("Final data saved to 'final_data.csv' and visualizations generated.")
    else:
        print("'final_data.csv' already exists.")
