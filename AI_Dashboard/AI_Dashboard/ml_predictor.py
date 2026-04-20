# AI_Dashboard/ml_predictor.py
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

class FinancialPredictor:
    def __init__(self):
        self.models = {
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'linear_regression': LinearRegression(),
            'decision_tree': DecisionTreeRegressor(random_state=42)
        }
        self.best_model = None
        self.results = {}
    
    def prepare_data(self, df, target_column='revenue'):
        """آماده‌سازی داده برای آموزش"""
        # ایجاد ویژگی‌های سری زمانی
        df['month_lag_1'] = df[target_column].shift(1)
        df['month_lag_2'] = df[target_column].shift(2)
        df['month_lag_3'] = df[target_column].shift(3)
        df['rolling_mean_3'] = df[target_column].rolling(3).mean()
        
        df = df.dropna()
        
        X = df.drop(columns=[target_column])
        y = df[target_column]
        return X, y
    
    def train_all_models(self, X, y):
        """آموزش همه مدل‌ها"""
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, shuffle=False
        )
        
        for name, model in self.models.items():
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            
            self.results[name] = {
                'model': model,
                'MAE': mean_absolute_error(y_test, y_pred),
                'RMSE': np.sqrt(mean_squared_error(y_test, y_pred)),
                'R2': r2_score(y_test, y_pred),
                'predictions': y_pred,
                'actual': y_test
            }
        
        # انتخاب بهترین مدل بر اساس R2
        self.best_model = max(self.results, key=lambda x: self.results[x]['R2'])
        return self.best_model
    
    def predict_next_month(self, last_3_months):
        """پیش‌بینی ماه آینده"""
        # پیاده‌سازی منطق پیش‌بینی
        pass