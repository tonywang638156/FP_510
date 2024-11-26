import unittest
import os
import pandas as pd
from datetime import datetime, timedelta
from stock_price_pred import collect_stock_data, fetch_news, analyze_sentiment, merge_and_calculate, calculate_rsi

class TestStockPricePrediction(unittest.TestCase):

    def test_collect_stock_data(self):
        stock_data = collect_stock_data()
        self.assertIsInstance(stock_data, pd.DataFrame)
        self.assertTrue('date' in stock_data.columns)
        self.assertTrue('Close' in stock_data.columns)

    def test_fetch_news(self):
        news_data = fetch_news()
        self.assertIsInstance(news_data, pd.DataFrame)
        self.assertTrue('title' in news_data.columns)
        self.assertTrue('description' in news_data.columns)

    def test_analyze_sentiment(self):
        sample_news = pd.DataFrame({
            'title': ["Apple stock rises after new iPhone release"],
            'description': ["The new iPhone has driven Apple stock upwards."],
        })
        analyzed_news = analyze_sentiment(sample_news)
        self.assertIsInstance(analyzed_news, pd.DataFrame)
        self.assertTrue('title_sentiment_hf' in analyzed_news.columns)
        self.assertTrue('description_sentiment_hf' in analyzed_news.columns)

    def test_calculate_rsi(self):
        sample_data = pd.DataFrame({'Close': [150, 155, 160, 158, 162, 165, 170]})
        sample_data['RSI'] = calculate_rsi(sample_data)
        self.assertTrue('RSI' in sample_data.columns)
        self.assertFalse(sample_data['RSI'].isnull().all())

    def test_merge_and_calculate(self):
        stock_data = pd.DataFrame({
            'date': [(datetime.now() - timedelta(days=i)).date() for i in range(5)],
            'Close': [150, 155, 160, 158, 162],
        })
        news_data = pd.DataFrame({
            'date': [(datetime.now() - timedelta(days=i)).date() for i in range(5)],
            'publishedAt': [(datetime.now() - timedelta(days=i)).isoformat() for i in range(5)],
            'title': ["Sample news"] * 5,
            'description': ["Sample description"] * 5,
            'title_sentiment_hf': ["POSITIVE"] * 5,
            'description_sentiment_hf': ["POSITIVE"] * 5,
        })
        merged_data = merge_and_calculate(stock_data, news_data)
        self.assertIsInstance(merged_data, pd.DataFrame)
        self.assertTrue('SMA' in merged_data.columns)
        self.assertTrue('EMA' in merged_data.columns)
        self.assertTrue('RSI' in merged_data.columns)

    def test_output_file(self):
        if os.path.exists("final_data.csv"):
            os.remove("final_data.csv")
        stock_data = collect_stock_data()
        news_data = fetch_news()
        news_data = analyze_sentiment(news_data)
        final_data = merge_and_calculate(stock_data, news_data)
        final_data.to_csv("final_data.csv", index=False)
        self.assertTrue(os.path.exists("final_data.csv"))

if __name__ == "__main__":
    unittest.main()
