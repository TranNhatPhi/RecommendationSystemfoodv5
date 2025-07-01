"""
🎯 HYBRID RECOMMENDATION SYSTEM FOR FOOD RECIPES
==============================================

Advanced hybrid recommendation system combining multiple ML approaches:
- Collaborative Filtering (CF)
- Content-Based Filtering (CBF) 
- Matrix Factorization (MF)
- Deep Learning Neural Networks
- Ensemble Methods

Author: AI Assistant
Date: June 19, 2025
Version: 1.0
"""

from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.ensemble import RandomForestRegressor
from sklearn.decomposition import TruncatedSVD
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split
import pandas as pd
import numpy as np
import pickle
import json
import os
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ML Libraries

# Deep Learning
try:
    import tensorflow as tf
    from tensorflow.keras.models import Model, Sequential
    from tensorflow.keras.layers import Dense, Embedding, Flatten, Concatenate, Dropout, Input
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    print("⚠️ TensorFlow not available - Deep learning features disabled")

# Matrix Factorization
try:
    from surprise import Dataset, Reader, SVD, NMF, BaselineOnly
    from surprise.model_selection import train_test_split as surprise_train_test_split
    from surprise import accuracy
    SURPRISE_AVAILABLE = True
except ImportError:
    SURPRISE_AVAILABLE = False
    print("⚠️ Surprise library not available - Advanced CF methods disabled")


@dataclass
class RecommendationResult:
    """Structure for recommendation results"""
    recipe_id: str
    recipe_name: str
    score: float
    confidence: float
    method: str
    features: Dict[str, Any]


class HybridRecommendationSystem:
    """
    🎯 Advanced Hybrid Recommendation System

    Combines multiple recommendation approaches:
    1. Collaborative Filtering (User-Item, Item-Item)
    2. Content-Based Filtering (Recipe features)
    3. Matrix Factorization (SVD, NMF)
    4. Deep Learning (Neural Collaborative Filtering)
    5. Ensemble Methods (Weighted combination)
    """

    def __init__(self, config: Optional[Dict] = None):
        """Initialize the hybrid recommendation system"""
        self.config = config or self._get_default_config()

        # Data storage
        self.interactions_df = None
        self.recipes_df = None
        self.customers_df = None

        # Models
        self.models = {}
        self.encoders = {}
        self.scalers = {}

        # Feature matrices
        self.user_item_matrix = None
        self.content_features = None
        self.recipe_features = None

        # Model weights for ensemble
        self.ensemble_weights = {
            'collaborative': 0.3,
            'content_based': 0.25,
            'matrix_factorization': 0.25,
            'deep_learning': 0.2
        }

        print("🎯 Hybrid Recommendation System initialized")

    def _get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            'min_interactions': 5,
            'min_recipe_ratings': 3,
            'test_size': 0.2,
            'random_state': 42,
            'n_recommendations': 10,
            'similarity_threshold': 0.1,
            'ensemble_method': 'weighted_average',
            'deep_learning_epochs': 50,
            'deep_learning_batch_size': 256,
            'matrix_factorization_factors': 50,
            'content_tfidf_max_features': 1000
        }

    def load_data(self, interactions_path: str, recipes_path: str = None, customers_path: str = None):
        """
        Load interaction data and optional recipe/customer data

        Args:
            interactions_path: Path to interactions CSV file
            recipes_path: Optional path to recipes data
            customers_path: Optional path to customers data
        """
        print("📊 Loading data...")

        # Load interactions data
        self.interactions_df = pd.read_csv(interactions_path)
        print(f"✅ Loaded {len(self.interactions_df)} interactions")

        # Load recipes data if available
        if recipes_path and os.path.exists(recipes_path):
            self.recipes_df = pd.read_csv(recipes_path)
            print(f"✅ Loaded {len(self.recipes_df)} recipes")

        # Load customers data if available
        if customers_path and os.path.exists(customers_path):
            self.customers_df = pd.read_csv(customers_path)
            print(f"✅ Loaded {len(self.customers_df)} customers")

        self._preprocess_data()

    def _preprocess_data(self):
        """Preprocess the loaded data"""
        print("🔄 Preprocessing data...")

        # Handle missing values
        self.interactions_df['rating'] = self.interactions_df['rating'].fillna(
            3.0)

        # Create numeric encodings for categorical data
        self.encoders['customer'] = LabelEncoder()
        self.encoders['recipe'] = LabelEncoder()

        self.interactions_df['customer_encoded'] = self.encoders['customer'].fit_transform(
            self.interactions_df['customer_id']
        )
        self.interactions_df['recipe_encoded'] = self.encoders['recipe'].fit_transform(
            self.interactions_df['recipe_name']
        )

        # Filter data based on minimum interactions
        if self.config['min_interactions'] > 0:
            customer_counts = self.interactions_df['customer_id'].value_counts(
            )
            valid_customers = customer_counts[customer_counts >=
                                              self.config['min_interactions']].index
            self.interactions_df = self.interactions_df[
                self.interactions_df['customer_id'].isin(valid_customers)
            ]

        if self.config['min_recipe_ratings'] > 0:
            recipe_counts = self.interactions_df['recipe_name'].value_counts()
            valid_recipes = recipe_counts[recipe_counts >=
                                          self.config['min_recipe_ratings']].index
            self.interactions_df = self.interactions_df[
                self.interactions_df['recipe_name'].isin(valid_recipes)
            ]

        print(
            f"✅ Preprocessed data: {len(self.interactions_df)} interactions after filtering")

        # Create user-item matrix
        self._create_user_item_matrix()

        # Extract content features
        self._extract_content_features()

    def _create_user_item_matrix(self):
        """Create user-item interaction matrix"""
        print("📈 Creating user-item matrix...")

        self.user_item_matrix = self.interactions_df.pivot_table(
            index='customer_encoded',
            columns='recipe_encoded',
            values='rating',
            fill_value=0
        )

        print(
            f"✅ Created {self.user_item_matrix.shape[0]}x{self.user_item_matrix.shape[1]} user-item matrix")

    def _extract_content_features(self):
        """Extract content-based features from recipes"""
        print("🔍 Extracting content features...")

        # Combine text features for TF-IDF
        text_features = []

        for _, row in self.interactions_df.iterrows():
            features = []

            # Add recipe name
            if pd.notna(row.get('recipe_name')):
                features.append(str(row['recipe_name']))

            # Add nutrition category
            if pd.notna(row.get('nutrition_category')):
                features.append(str(row['nutrition_category']))

            # Add meal time
            if pd.notna(row.get('meal_time')):
                features.append(str(row['meal_time']))

            # Add difficulty
            if pd.notna(row.get('difficulty')):
                features.append(str(row['difficulty']))

            text_features.append(' '.join(features))

        # Create TF-IDF vectors
        tfidf = TfidfVectorizer(
            max_features=self.config['content_tfidf_max_features'],
            stop_words='english',
            ngram_range=(1, 2)
        )

        self.content_features = tfidf.fit_transform(text_features)
        self.models['tfidf'] = tfidf

        # Create numerical features matrix
        numerical_features = []
        for _, row in self.interactions_df.iterrows():
            features = [
                row.get('estimated_calories', 0),
                row.get('preparation_time_minutes', 0),
                row.get('ingredient_count', 0),
                row.get('estimated_price_vnd', 0),
                row.get('difficulty_code', 0),
                row.get('meal_time_code', 0)
            ]
            numerical_features.append(features)

        self.recipe_features = np.array(numerical_features)

        # Scale numerical features
        scaler = StandardScaler()
        self.recipe_features = scaler.fit_transform(self.recipe_features)
        self.scalers['recipe_features'] = scaler

        print("✅ Content features extracted")

    def train_collaborative_filtering(self):
        """Train collaborative filtering models"""
        print("🤝 Training collaborative filtering models...")

        # User-based collaborative filtering
        user_similarity = cosine_similarity(self.user_item_matrix)
        self.models['user_similarity'] = user_similarity

        # Item-based collaborative filtering
        item_similarity = cosine_similarity(self.user_item_matrix.T)
        self.models['item_similarity'] = item_similarity

        # KNN-based collaborative filtering
        knn_model = NearestNeighbors(
            metric='cosine', algorithm='brute', n_neighbors=20)
        knn_model.fit(self.user_item_matrix)
        self.models['knn_cf'] = knn_model

        print("✅ Collaborative filtering models trained")

    def train_content_based_filtering(self):
        """Train content-based filtering models"""
        print("📝 Training content-based filtering models...")

        # Content similarity matrix
        content_similarity = cosine_similarity(self.content_features)
        self.models['content_similarity'] = content_similarity

        # KNN for content-based recommendations
        knn_content = NearestNeighbors(
            metric='cosine', algorithm='brute', n_neighbors=20)
        knn_content.fit(self.content_features)
        self.models['knn_content'] = knn_content

        print("✅ Content-based filtering models trained")

    def train_matrix_factorization(self):
        """Train matrix factorization models"""
        print("🧮 Training matrix factorization models...")

        if SURPRISE_AVAILABLE:
            # Prepare data for Surprise library
            reader = Reader(rating_scale=(1, 5))
            data = Dataset.load_from_df(
                self.interactions_df[['customer_id', 'recipe_name', 'rating']],
                reader
            )

            trainset, testset = surprise_train_test_split(
                data, test_size=self.config['test_size'])

            # SVD Model
            svd_model = SVD(
                n_factors=self.config['matrix_factorization_factors'])
            svd_model.fit(trainset)
            self.models['svd'] = svd_model

            # NMF Model
            nmf_model = NMF(
                n_factors=self.config['matrix_factorization_factors'])
            nmf_model.fit(trainset)
            self.models['nmf'] = nmf_model

            # Evaluate models
            svd_predictions = svd_model.test(testset)
            nmf_predictions = nmf_model.test(testset)

            svd_rmse = accuracy.rmse(svd_predictions, verbose=False)
            nmf_rmse = accuracy.rmse(nmf_predictions, verbose=False)

            print(f"✅ SVD RMSE: {svd_rmse:.4f}")
            print(f"✅ NMF RMSE: {nmf_rmse:.4f}")

        else:
            # Fallback to basic SVD using sklearn
            svd = TruncatedSVD(
                n_components=self.config['matrix_factorization_factors'])
            user_factors = svd.fit_transform(self.user_item_matrix)
            item_factors = svd.components_.T

            self.models['svd_sklearn'] = {
                'model': svd,
                'user_factors': user_factors,
                'item_factors': item_factors
            }

            print("✅ Matrix factorization models trained (sklearn fallback)")

    def train_deep_learning(self):
        """Train deep learning models"""
        print("🧠 Training deep learning models...")

        if not TENSORFLOW_AVAILABLE:
            print("⚠️ TensorFlow not available - skipping deep learning training")
            return

        # Prepare data for neural network
        X_users = self.interactions_df['customer_encoded'].values
        X_items = self.interactions_df['recipe_encoded'].values
        y = self.interactions_df['rating'].values

        # Additional features
        X_features = self.recipe_features

        # Train-test split
        X_users_train, X_users_test, X_items_train, X_items_test, X_feat_train, X_feat_test, y_train, y_test = train_test_split(
            X_users, X_items, X_features, y,
            test_size=self.config['test_size'],
            random_state=self.config['random_state']
        )

        # Neural Collaborative Filtering Model
        n_users = len(self.encoders['customer'].classes_)
        n_items = len(self.encoders['recipe'].classes_)
        n_features = X_features.shape[1]

        # User input
        user_input = Input(shape=(), name='user_id')
        user_embedding = Embedding(
            n_users, 50, name='user_embedding')(user_input)
        user_flat = Flatten()(user_embedding)

        # Item input
        item_input = Input(shape=(), name='item_id')
        item_embedding = Embedding(
            n_items, 50, name='item_embedding')(item_input)
        item_flat = Flatten()(item_embedding)

        # Feature input
        feature_input = Input(shape=(n_features,), name='features')

        # Concatenate all inputs
        concat = Concatenate()([user_flat, item_flat, feature_input])

        # Hidden layers
        dense1 = Dense(128, activation='relu')(concat)
        dropout1 = Dropout(0.2)(dense1)
        dense2 = Dense(64, activation='relu')(dropout1)
        dropout2 = Dropout(0.2)(dense2)
        dense3 = Dense(32, activation='relu')(dropout2)

        # Output layer
        output = Dense(1, activation='linear')(dense3)

        # Create model
        model = Model(inputs=[user_input, item_input,
                      feature_input], outputs=output)
        model.compile(optimizer=Adam(learning_rate=0.001),
                      loss='mse', metrics=['mae'])

        # Train model
        early_stopping = EarlyStopping(
            monitor='val_loss', patience=5, restore_best_weights=True)

        history = model.fit(
            [X_users_train, X_items_train, X_feat_train], y_train,
            validation_data=(
                [X_users_test, X_items_test, X_feat_test], y_test),
            epochs=self.config['deep_learning_epochs'],
            batch_size=self.config['deep_learning_batch_size'],
            callbacks=[early_stopping],
            verbose=0
        )

        self.models['neural_cf'] = model

        # Evaluate model
        train_loss = model.evaluate(
            [X_users_train, X_items_train, X_feat_train], y_train, verbose=0)
        test_loss = model.evaluate(
            [X_users_test, X_items_test, X_feat_test], y_test, verbose=0)

        print(
            f"✅ Neural CF - Train Loss: {train_loss[0]:.4f}, Test Loss: {test_loss[0]:.4f}")

    def train_all_models(self):
        """Train all recommendation models"""
        print("🎯 Training all recommendation models...")
        start_time = datetime.now()

        self.train_collaborative_filtering()
        self.train_content_based_filtering()
        self.train_matrix_factorization()
        self.train_deep_learning()

        training_time = (datetime.now() - start_time).total_seconds()
        print(f"✅ All models trained in {training_time:.2f} seconds")

    def get_collaborative_recommendations(self, customer_id: str, n_recommendations: int = 10) -> List[RecommendationResult]:
        """Get recommendations using collaborative filtering"""
        try:
            if customer_id not in self.encoders['customer'].classes_:
                return []

            customer_encoded = self.encoders['customer'].transform([customer_id])[
                0]

            # Get user similarities
            user_similarities = self.models['user_similarity'][customer_encoded]

            # Find similar users
            similar_users = np.argsort(user_similarities)[
                ::-1][1:21]  # Top 20 similar users

            # Get items rated by similar users
            recommendations = {}
            user_ratings = self.user_item_matrix.iloc[customer_encoded]

            for similar_user in similar_users:
                similarity_score = user_similarities[similar_user]
                if similarity_score < self.config['similarity_threshold']:
                    continue

                similar_user_ratings = self.user_item_matrix.iloc[similar_user]

                for item_idx, rating in similar_user_ratings.items():
                    # User hasn't rated this item
                    if rating > 0 and user_ratings[item_idx] == 0:
                        if item_idx not in recommendations:
                            recommendations[item_idx] = 0
                        recommendations[item_idx] += similarity_score * rating

            # Convert to recommendation results
            results = []
            for item_idx, score in sorted(recommendations.items(), key=lambda x: x[1], reverse=True)[:n_recommendations]:
                recipe_name = self.encoders['recipe'].inverse_transform([item_idx])[
                    0]
                results.append(RecommendationResult(
                    recipe_id=str(item_idx),
                    recipe_name=recipe_name,
                    score=score,
                    confidence=min(score / 5.0, 1.0),
                    method='collaborative_filtering',
                    features={'similarity_based': True}
                ))

            return results

        except Exception as e:
            print(f"⚠️ Error in collaborative filtering: {e}")
            return []

    def get_content_based_recommendations(self, customer_id: str, n_recommendations: int = 10) -> List[RecommendationResult]:
        """Get recommendations using content-based filtering"""
        try:
            # Get user's interaction history
            user_interactions = self.interactions_df[self.interactions_df['customer_id'] == customer_id]

            if len(user_interactions) == 0:
                return []

            # Get user's preferred content features
            user_feature_indices = user_interactions.index.tolist()
            user_features = self.content_features[user_feature_indices]

            # Calculate user profile (average of liked items)
            user_profile = np.mean(user_features.toarray(), axis=0)

            # Calculate similarity with all items
            all_similarities = cosine_similarity(
                [user_profile], self.content_features.toarray())[0]

            # Get items user hasn't interacted with
            interacted_items = set(user_interactions['recipe_encoded'].values)
            recommendations = []

            for idx, similarity in enumerate(all_similarities):
                recipe_encoded = self.interactions_df.iloc[idx]['recipe_encoded']
                if recipe_encoded not in interacted_items and similarity > self.config['similarity_threshold']:
                    recipe_name = self.interactions_df.iloc[idx]['recipe_name']
                    recommendations.append(RecommendationResult(
                        recipe_id=str(recipe_encoded),
                        recipe_name=recipe_name,
                        score=similarity,
                        confidence=similarity,
                        method='content_based_filtering',
                        features={'content_similarity': similarity}
                    ))

            # Sort by score and return top N
            recommendations.sort(key=lambda x: x.score, reverse=True)
            return recommendations[:n_recommendations]

        except Exception as e:
            print(f"⚠️ Error in content-based filtering: {e}")
            return []

    def get_matrix_factorization_recommendations(self, customer_id: str, n_recommendations: int = 10) -> List[RecommendationResult]:
        """Get recommendations using matrix factorization"""
        try:
            recommendations = []

            if SURPRISE_AVAILABLE and 'svd' in self.models:
                # Get all recipes
                all_recipes = self.interactions_df['recipe_name'].unique()

                # Get predictions for all recipes
                for recipe_name in all_recipes:
                    prediction = self.models['svd'].predict(
                        customer_id, recipe_name)

                    recommendations.append(RecommendationResult(
                        recipe_id=recipe_name,
                        recipe_name=recipe_name,
                        score=prediction.est,
                        # Confidence based on distance from neutral rating
                        confidence=1.0 - abs(prediction.est - 3.0) / 2.0,
                        method='matrix_factorization_svd',
                        features={'predicted_rating': prediction.est}
                    ))

            elif 'svd_sklearn' in self.models:
                # Fallback to sklearn SVD
                if customer_id not in self.encoders['customer'].classes_:
                    return []

                customer_encoded = self.encoders['customer'].transform([customer_id])[
                    0]
                user_factors = self.models['svd_sklearn']['user_factors'][customer_encoded]
                item_factors = self.models['svd_sklearn']['item_factors']

                # Calculate predictions
                predictions = np.dot(user_factors, item_factors.T)

                # Get top recommendations
                top_items = np.argsort(predictions)[::-1][:n_recommendations]

                for item_idx in top_items:
                    recipe_name = self.encoders['recipe'].inverse_transform([item_idx])[
                        0]
                    score = predictions[item_idx]

                    recommendations.append(RecommendationResult(
                        recipe_id=str(item_idx),
                        recipe_name=recipe_name,
                        score=score,
                        confidence=min(score / 5.0, 1.0),
                        method='matrix_factorization_sklearn',
                        features={'predicted_rating': score}
                    ))

            # Sort by score and return top N
            recommendations.sort(key=lambda x: x.score, reverse=True)
            return recommendations[:n_recommendations]

        except Exception as e:
            print(f"⚠️ Error in matrix factorization: {e}")
            return []

    def get_deep_learning_recommendations(self, customer_id: str, n_recommendations: int = 10) -> List[RecommendationResult]:
        """Get recommendations using deep learning"""
        try:
            if not TENSORFLOW_AVAILABLE or 'neural_cf' not in self.models:
                return []

            if customer_id not in self.encoders['customer'].classes_:
                return []

            customer_encoded = self.encoders['customer'].transform([customer_id])[
                0]

            # Get all recipes
            all_recipe_encoded = list(
                range(len(self.encoders['recipe'].classes_)))

            # Prepare input data
            user_input = np.array([customer_encoded] * len(all_recipe_encoded))
            item_input = np.array(all_recipe_encoded)

            # Get average features for recipes (simplified approach)
            feature_input = np.tile(
                np.mean(self.recipe_features, axis=0), (len(all_recipe_encoded), 1))

            # Get predictions
            predictions = self.models['neural_cf'].predict(
                [user_input, item_input, feature_input], verbose=0)

            # Create recommendations
            recommendations = []
            for i, (recipe_encoded, pred_rating) in enumerate(zip(all_recipe_encoded, predictions.flatten())):
                recipe_name = self.encoders['recipe'].inverse_transform([recipe_encoded])[
                    0]

                recommendations.append(RecommendationResult(
                    recipe_id=str(recipe_encoded),
                    recipe_name=recipe_name,
                    score=pred_rating,
                    confidence=min(pred_rating / 5.0, 1.0),
                    method='deep_learning_neural_cf',
                    features={'neural_prediction': pred_rating}
                ))

            # Sort by score and return top N
            recommendations.sort(key=lambda x: x.score, reverse=True)
            return recommendations[:n_recommendations]

        except Exception as e:
            print(f"⚠️ Error in deep learning recommendations: {e}")
            return []

    def get_hybrid_recommendations(self, customer_id: str, n_recommendations: int = 10) -> List[RecommendationResult]:
        """
        Get hybrid recommendations by combining all methods

        Args:
            customer_id: ID of the customer
            n_recommendations: Number of recommendations to return

        Returns:
            List of RecommendationResult objects
        """
        print(f"🎯 Getting hybrid recommendations for customer: {customer_id}")

        # Get recommendations from each method
        cf_recs = self.get_collaborative_recommendations(
            customer_id, n_recommendations * 2)
        cb_recs = self.get_content_based_recommendations(
            customer_id, n_recommendations * 2)
        mf_recs = self.get_matrix_factorization_recommendations(
            customer_id, n_recommendations * 2)
        dl_recs = self.get_deep_learning_recommendations(
            customer_id, n_recommendations * 2)

        # Combine recommendations
        all_recommendations = {}

        # Add collaborative filtering recommendations
        for rec in cf_recs:
            if rec.recipe_name not in all_recommendations:
                all_recommendations[rec.recipe_name] = {
                    'recipe_id': rec.recipe_id,
                    'recipe_name': rec.recipe_name,
                    'scores': {},
                    'features': {}
                }
            all_recommendations[rec.recipe_name]['scores']['collaborative'] = rec.score * \
                self.ensemble_weights['collaborative']
            all_recommendations[rec.recipe_name]['features'].update(
                rec.features)

        # Add content-based recommendations
        for rec in cb_recs:
            if rec.recipe_name not in all_recommendations:
                all_recommendations[rec.recipe_name] = {
                    'recipe_id': rec.recipe_id,
                    'recipe_name': rec.recipe_name,
                    'scores': {},
                    'features': {}
                }
            all_recommendations[rec.recipe_name]['scores']['content_based'] = rec.score * \
                self.ensemble_weights['content_based']
            all_recommendations[rec.recipe_name]['features'].update(
                rec.features)

        # Add matrix factorization recommendations
        for rec in mf_recs:
            if rec.recipe_name not in all_recommendations:
                all_recommendations[rec.recipe_name] = {
                    'recipe_id': rec.recipe_id,
                    'recipe_name': rec.recipe_name,
                    'scores': {},
                    'features': {}
                }
            all_recommendations[rec.recipe_name]['scores']['matrix_factorization'] = rec.score * \
                self.ensemble_weights['matrix_factorization']
            all_recommendations[rec.recipe_name]['features'].update(
                rec.features)

        # Add deep learning recommendations
        for rec in dl_recs:
            if rec.recipe_name not in all_recommendations:
                all_recommendations[rec.recipe_name] = {
                    'recipe_id': rec.recipe_id,
                    'recipe_name': rec.recipe_name,
                    'scores': {},
                    'features': {}
                }
            all_recommendations[rec.recipe_name]['scores']['deep_learning'] = rec.score * \
                self.ensemble_weights['deep_learning']
            all_recommendations[rec.recipe_name]['features'].update(
                rec.features)

        # Calculate final scores
        final_recommendations = []
        for recipe_name, data in all_recommendations.items():
            # Calculate weighted average score
            total_score = sum(data['scores'].values())
            num_methods = len(data['scores'])

            # Confidence based on number of methods agreeing
            confidence = num_methods / 4.0  # 4 total methods

            final_recommendations.append(RecommendationResult(
                recipe_id=data['recipe_id'],
                recipe_name=recipe_name,
                score=total_score,
                confidence=confidence,
                method='hybrid_ensemble',
                features={
                    'method_scores': data['scores'],
                    'num_methods': num_methods,
                    **data['features']
                }
            ))

        # Sort by score and return top N
        final_recommendations.sort(key=lambda x: x.score, reverse=True)

        print(
            f"✅ Generated {len(final_recommendations)} hybrid recommendations")
        return final_recommendations[:n_recommendations]

    def evaluate_model(self, test_size: float = 0.2) -> Dict[str, float]:
        """
        Evaluate the hybrid recommendation system

        Args:
            test_size: Proportion of data to use for testing

        Returns:
            Dictionary containing evaluation metrics
        """
        print("📊 Evaluating hybrid recommendation system...")

        # Split data for evaluation
        train_data, test_data = train_test_split(
            self.interactions_df,
            test_size=test_size,
            random_state=self.config['random_state']
        )

        # Calculate metrics
        metrics = {}

        # RMSE and MAE for rating prediction
        predictions = []
        actuals = []

        for _, row in test_data.iterrows():
            customer_id = row['customer_id']
            actual_rating = row['rating']

            # Get hybrid recommendations for this customer
            recs = self.get_hybrid_recommendations(customer_id, 1)

            if recs:
                predicted_rating = recs[0].score
                predictions.append(predicted_rating)
                actuals.append(actual_rating)

        if predictions:
            metrics['rmse'] = np.sqrt(mean_squared_error(actuals, predictions))
            metrics['mae'] = mean_absolute_error(actuals, predictions)
        else:
            metrics['rmse'] = float('inf')
            metrics['mae'] = float('inf')

        # Coverage: percentage of items that can be recommended
        all_recipes = set(self.interactions_df['recipe_name'].unique())
        recommended_recipes = set()

        sample_customers = self.interactions_df['customer_id'].unique()[
            :100]  # Sample for efficiency
        for customer_id in sample_customers:
            recs = self.get_hybrid_recommendations(customer_id, 10)
            recommended_recipes.update([rec.recipe_name for rec in recs])

        metrics['coverage'] = len(recommended_recipes) / len(all_recipes)

        # Diversity: average intra-list diversity
        diversity_scores = []
        for customer_id in sample_customers[:20]:  # Sample for efficiency
            recs = self.get_hybrid_recommendations(customer_id, 10)
            if len(recs) > 1:
                # Calculate pairwise diversity (simplified)
                recipe_features = []
                for rec in recs:
                    # Get recipe features
                    recipe_data = self.interactions_df[self.interactions_df['recipe_name']
                                                       == rec.recipe_name].iloc[0]
                    features = [
                        recipe_data.get('estimated_calories', 0),
                        recipe_data.get('preparation_time_minutes', 0),
                        recipe_data.get('ingredient_count', 0),
                        recipe_data.get('difficulty_code', 0),
                        recipe_data.get('meal_time_code', 0)
                    ]
                    recipe_features.append(features)

                if len(recipe_features) > 1:
                    # Calculate average pairwise distance
                    distances = []
                    for i in range(len(recipe_features)):
                        for j in range(i+1, len(recipe_features)):
                            dist = np.linalg.norm(
                                np.array(recipe_features[i]) - np.array(recipe_features[j]))
                            distances.append(dist)

                    if distances:
                        diversity_scores.append(np.mean(distances))

        metrics['diversity'] = np.mean(
            diversity_scores) if diversity_scores else 0

        print("✅ Evaluation completed")
        print(f"   RMSE: {metrics['rmse']:.4f}")
        print(f"   MAE: {metrics['mae']:.4f}")
        print(f"   Coverage: {metrics['coverage']:.4f}")
        print(f"   Diversity: {metrics['diversity']:.4f}")

        return metrics

    def save_model(self, filepath: str):
        """Save the trained model to disk"""
        print(f"💾 Saving model to {filepath}...")

        # Prepare data for saving (exclude large objects)
        save_data = {
            'config': self.config,
            'encoders': self.encoders,
            'scalers': self.scalers,
            'ensemble_weights': self.ensemble_weights,
            'user_item_matrix': self.user_item_matrix,
            'models': {}
        }

        # Save specific models (exclude large matrices)
        for model_name, model in self.models.items():
            if model_name in ['user_similarity', 'item_similarity', 'content_similarity']:
                continue  # Skip large similarity matrices
            elif model_name == 'neural_cf' and TENSORFLOW_AVAILABLE:
                # Save neural network separately
                model.save(f"{filepath}_neural_cf.h5")
                continue
            else:
                save_data['models'][model_name] = model

        # Save main data
        with open(filepath, 'wb') as f:
            pickle.dump(save_data, f)

        print("✅ Model saved successfully")

    def load_model(self, filepath: str):
        """Load a trained model from disk"""
        print(f"📁 Loading model from {filepath}...")

        try:
            with open(filepath, 'rb') as f:
                save_data = pickle.load(f)

            self.config = save_data['config']
            self.encoders = save_data['encoders']
            self.scalers = save_data['scalers']
            self.ensemble_weights = save_data['ensemble_weights']
            self.user_item_matrix = save_data['user_item_matrix']
            self.models = save_data['models']

            # Load neural network if available
            neural_cf_path = f"{filepath}_neural_cf.h5"
            if os.path.exists(neural_cf_path) and TENSORFLOW_AVAILABLE:
                self.models['neural_cf'] = tf.keras.models.load_model(
                    neural_cf_path)

            print("✅ Model loaded successfully")

        except Exception as e:
            print(f"❌ Error loading model: {e}")

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the trained models"""
        info = {
            'config': self.config,
            'data_shape': {
                'interactions': len(self.interactions_df) if self.interactions_df is not None else 0,
                'customers': len(self.encoders['customer'].classes_) if 'customer' in self.encoders else 0,
                'recipes': len(self.encoders['recipe'].classes_) if 'recipe' in self.encoders else 0,
                'user_item_matrix': self.user_item_matrix.shape if self.user_item_matrix is not None else None
            },
            'trained_models': list(self.models.keys()),
            'ensemble_weights': self.ensemble_weights,
            'tensorflow_available': TENSORFLOW_AVAILABLE,
            'surprise_available': SURPRISE_AVAILABLE
        }

        return info


# Example usage and testing functions
def demo_hybrid_system():
    """Demonstrate the hybrid recommendation system"""
    print("🎯 HYBRID RECOMMENDATION SYSTEM DEMO")
    print("=" * 50)

    # Initialize system
    system = HybridRecommendationSystem()

    # Load data (adjust paths as needed)
    interactions_path = "interactions_enhanced_final.csv"

    if os.path.exists(interactions_path):
        system.load_data(interactions_path)

        # Train all models
        system.train_all_models()

        # Test recommendations
        sample_customer = system.interactions_df['customer_id'].iloc[0]
        print(f"\n🔍 Testing recommendations for customer: {sample_customer}")

        # Get hybrid recommendations
        recommendations = system.get_hybrid_recommendations(sample_customer, 5)

        print("\n🎯 TOP HYBRID RECOMMENDATIONS:")
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec.recipe_name}")
            print(
                f"   Score: {rec.score:.4f} | Confidence: {rec.confidence:.4f}")
            print(f"   Method: {rec.method}")
            print(f"   Features: {rec.features}")
            print()

        # Evaluate system
        metrics = system.evaluate_model()

        # Save model
        system.save_model("hybrid_recommendation_model.pkl")

        # Get model info
        info = system.get_model_info()
        print("\n📊 MODEL INFORMATION:")
        print(json.dumps(info, indent=2, default=str))

    else:
        print(f"❌ Data file not found: {interactions_path}")
        print("Please ensure the interactions data file is available.")


if __name__ == "__main__":
    demo_hybrid_system()
