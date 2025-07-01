"""
🔗 HYBRID SYSTEM INTEGRATION FOR FLASK APP
==========================================

This module integrates the hybrid recommendation system with the existing Flask application,
providing enhanced recommendation capabilities.

Author: AI Assistant
Date: June 19, 2025
"""

from hybrid_recommendation_system import HybridRecommendationSystem, RecommendationResult
import os
import sys
import json
import time
import threading
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


class HybridRecommendationService:
    """
    Service class for integrating hybrid recommendations with Flask app
    """

    def __init__(self, config: Optional[Dict] = None):
        """Initialize the hybrid recommendation service"""
        self.config = config or self._get_default_config()
        self.system = None
        self.is_trained = False
        self.last_training_time = None
        self.training_lock = threading.Lock()

        # Cache for performance
        self.recommendation_cache = {}
        self.cache_timeout = 300  # 5 minutes

        print("🔗 Hybrid Recommendation Service initialized")

    def _get_default_config(self) -> Dict:
        """Get default configuration optimized for production"""
        return {
            'min_interactions': 2,
            'min_recipe_ratings': 2,
            'test_size': 0.15,
            'random_state': 42,
            'n_recommendations': 10,
            'similarity_threshold': 0.05,
            'ensemble_method': 'weighted_average',
            'deep_learning_epochs': 20,  # Reduced for faster training
            'deep_learning_batch_size': 128,
            'matrix_factorization_factors': 25,  # Reduced for performance
            'content_tfidf_max_features': 300,   # Reduced for performance
            'auto_retrain_hours': 24,  # Auto-retrain every 24 hours
            'cache_recommendations': True
        }

    def initialize_system(self, interactions_path: str, force_retrain: bool = False) -> bool:
        """
        Initialize and train the hybrid system

        Args:
            interactions_path: Path to interactions data
            force_retrain: Force retraining even if model exists

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.training_lock:
                print("🚀 Initializing hybrid recommendation system...")

                # Check if model exists and is recent
                model_path = "hybrid_recommendation_model.pkl"
                if (os.path.exists(model_path) and not force_retrain and
                        self._is_model_recent(model_path)):

                    print("📁 Loading existing trained model...")
                    self.system = HybridRecommendationSystem(self.config)
                    self.system.load_model(model_path)

                    # Still need to load data for new predictions
                    if os.path.exists(interactions_path):
                        self.system.load_data(interactions_path)
                        self.is_trained = True
                        self.last_training_time = datetime.now()
                        print("✅ System loaded from existing model")
                        return True

                # Train new model
                if not os.path.exists(interactions_path):
                    print(f"❌ Data file not found: {interactions_path}")
                    return False

                print("🎯 Training new hybrid model...")
                start_time = time.time()

                self.system = HybridRecommendationSystem(self.config)
                self.system.load_data(interactions_path)
                self.system.train_all_models()

                # Save model
                self.system.save_model(model_path)

                training_time = time.time() - start_time
                self.is_trained = True
                self.last_training_time = datetime.now()

                print(
                    f"✅ Hybrid system trained and ready in {training_time:.2f} seconds")
                return True

        except Exception as e:
            print(f"❌ Error initializing hybrid system: {e}")
            return False

    def _is_model_recent(self, model_path: str) -> bool:
        """Check if the saved model is recent enough"""
        try:
            model_time = os.path.getmtime(model_path)
            hours_old = (time.time() - model_time) / 3600
            return hours_old < self.config['auto_retrain_hours']
        except:
            return False

    def get_recommendations(self, customer_id: str, n_recommendations: int = 10,
                            method: str = 'hybrid') -> Dict[str, Any]:
        """
        Get recommendations for a customer

        Args:
            customer_id: Customer ID
            n_recommendations: Number of recommendations
            method: Recommendation method ('hybrid', 'collaborative', 'content', 'matrix_factorization', 'deep_learning')

        Returns:
            Dictionary with recommendations and metadata
        """
        if not self.is_trained or not self.system:
            return {
                'success': False,
                'error': 'System not trained. Please initialize first.',
                'recommendations': []
            }

        try:
            # Check cache first
            cache_key = f"{customer_id}_{method}_{n_recommendations}"
            if (self.config['cache_recommendations'] and
                    cache_key in self.recommendation_cache):

                cached_result = self.recommendation_cache[cache_key]
                if time.time() - cached_result['timestamp'] < self.cache_timeout:
                    cached_result['from_cache'] = True
                    return cached_result

            start_time = time.time()

            # Get recommendations based on method
            if method == 'hybrid':
                recommendations = self.system.get_hybrid_recommendations(
                    customer_id, n_recommendations)
            elif method == 'collaborative':
                recommendations = self.system.get_collaborative_recommendations(
                    customer_id, n_recommendations)
            elif method == 'content':
                recommendations = self.system.get_content_based_recommendations(
                    customer_id, n_recommendations)
            elif method == 'matrix_factorization':
                recommendations = self.system.get_matrix_factorization_recommendations(
                    customer_id, n_recommendations)
            elif method == 'deep_learning':
                recommendations = self.system.get_deep_learning_recommendations(
                    customer_id, n_recommendations)
            else:
                return {
                    'success': False,
                    'error': f'Unknown method: {method}',
                    'recommendations': []
                }

            recommendation_time = time.time() - start_time

            # Format recommendations for API response
            formatted_recs = []
            for rec in recommendations:
                # Get additional recipe details if available
                recipe_details = self._get_recipe_details(rec.recipe_name)

                formatted_rec = {
                    'recipe_id': rec.recipe_id,
                    'recipe_name': rec.recipe_name,
                    'score': round(rec.score, 4),
                    'confidence': round(rec.confidence, 4),
                    'method': rec.method,
                    'features': rec.features,
                    **recipe_details
                }
                formatted_recs.append(formatted_rec)

            result = {
                'success': True,
                'customer_id': customer_id,
                'method': method,
                'recommendations': formatted_recs,
                'metadata': {
                    'recommendation_time': round(recommendation_time, 4),
                    'total_recommendations': len(formatted_recs),
                    'timestamp': datetime.now().isoformat(),
                    'system_info': {
                        'last_training': self.last_training_time.isoformat() if self.last_training_time else None,
                        'is_trained': self.is_trained
                    }
                },
                'from_cache': False
            }

            # Cache result
            if self.config['cache_recommendations']:
                result['timestamp'] = time.time()
                self.recommendation_cache[cache_key] = result.copy()

                # Clean old cache entries
                self._clean_cache()

            return result

        except Exception as e:
            return {
                'success': False,
                'error': f'Error getting recommendations: {str(e)}',
                'recommendations': [],
                'customer_id': customer_id,
                'method': method
            }

    def _get_recipe_details(self, recipe_name: str) -> Dict[str, Any]:
        """Get additional recipe details from interactions data"""
        try:
            recipe_data = self.system.interactions_df[
                self.system.interactions_df['recipe_name'] == recipe_name
            ].iloc[0]

            return {
                'nutrition_category': recipe_data.get('nutrition_category', 'unknown'),
                'estimated_calories': int(recipe_data.get('estimated_calories', 0)),
                'preparation_time_minutes': int(recipe_data.get('preparation_time_minutes', 0)),
                'difficulty': recipe_data.get('difficulty', 'unknown'),
                'meal_time': recipe_data.get('meal_time', 'unknown'),
                'ingredient_count': int(recipe_data.get('ingredient_count', 0)),
                'estimated_price_vnd': int(recipe_data.get('estimated_price_vnd', 0)),
                'recipe_url': recipe_data.get('recipe_url', '')
            }
        except:
            return {
                'nutrition_category': 'unknown',
                'estimated_calories': 0,
                'preparation_time_minutes': 0,
                'difficulty': 'unknown',
                'meal_time': 'unknown',
                'ingredient_count': 0,
                'estimated_price_vnd': 0,
                'recipe_url': ''
            }

    def _clean_cache(self):
        """Clean old cache entries"""
        current_time = time.time()
        keys_to_remove = []

        for key, value in self.recommendation_cache.items():
            if current_time - value.get('timestamp', 0) > self.cache_timeout:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.recommendation_cache[key]

    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics and health information"""
        if not self.system:
            return {'status': 'not_initialized'}

        try:
            info = self.system.get_model_info()

            stats = {
                'status': 'ready' if self.is_trained else 'not_trained',
                'last_training': self.last_training_time.isoformat() if self.last_training_time else None,
                'data_stats': info['data_shape'],
                'trained_models': info['trained_models'],
                'ensemble_weights': info['ensemble_weights'],
                'library_support': {
                    'tensorflow': info['tensorflow_available'],
                    'surprise': info['surprise_available']
                },
                'cache_stats': {
                    'cached_entries': len(self.recommendation_cache),
                    'cache_enabled': self.config['cache_recommendations']
                },
                'config': self.config
            }

            return stats

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

    def evaluate_system(self) -> Dict[str, Any]:
        """Evaluate system performance"""
        if not self.is_trained:
            return {'error': 'System not trained'}

        try:
            metrics = self.system.evaluate_model()
            return {
                'success': True,
                'metrics': metrics,
                'evaluation_time': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def retrain_system(self, interactions_path: str) -> Dict[str, Any]:
        """Retrain the system with updated data"""
        try:
            success = self.initialize_system(
                interactions_path, force_retrain=True)

            if success:
                return {
                    'success': True,
                    'message': 'System retrained successfully',
                    'training_time': self.last_training_time.isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to retrain system'
                }

        except Exception as e:
            return {
                'success': False,
                'error': f'Error retraining system: {str(e)}'
            }

    def clear_cache(self):
        """Clear recommendation cache"""
        self.recommendation_cache.clear()
        return {'success': True, 'message': 'Cache cleared'}


# Global service instance
hybrid_service = HybridRecommendationService()


def get_hybrid_service() -> HybridRecommendationService:
    """Get the global hybrid service instance"""
    return hybrid_service


def initialize_hybrid_service(interactions_path: str = "interactions_enhanced_final.csv") -> bool:
    """Initialize the hybrid service"""
    return hybrid_service.initialize_system(interactions_path)


# Flask integration functions
def add_hybrid_routes(app):
    """Add hybrid recommendation routes to Flask app"""

    @app.route('/api/hybrid/recommendations/<customer_id>')
    def get_hybrid_recommendations(customer_id):
        """Get hybrid recommendations for a customer"""
        from flask import request, jsonify

        method = request.args.get('method', 'hybrid')
        n_recommendations = int(request.args.get('n', 10))

        result = hybrid_service.get_recommendations(
            customer_id, n_recommendations, method)
        return jsonify(result)

    @app.route('/api/hybrid/stats')
    def get_hybrid_stats():
        """Get hybrid system statistics"""
        from flask import jsonify

        stats = hybrid_service.get_system_stats()
        return jsonify(stats)

    @app.route('/api/hybrid/evaluate')
    def evaluate_hybrid_system():
        """Evaluate hybrid system performance"""
        from flask import jsonify

        evaluation = hybrid_service.evaluate_system()
        return jsonify(evaluation)

    @app.route('/api/hybrid/retrain', methods=['POST'])
    def retrain_hybrid_system():
        """Retrain the hybrid system"""
        from flask import request, jsonify

        interactions_path = request.json.get(
            'interactions_path', 'interactions_enhanced_final.csv')
        result = hybrid_service.retrain_system(interactions_path)
        return jsonify(result)

    @app.route('/api/hybrid/cache/clear', methods=['POST'])
    def clear_hybrid_cache():
        """Clear recommendation cache"""
        from flask import jsonify

        result = hybrid_service.clear_cache()
        return jsonify(result)

    print("✅ Hybrid recommendation routes added to Flask app")


# Example usage
if __name__ == "__main__":
    # Test the service
    service = HybridRecommendationService()

    if service.initialize_system("interactions_enhanced_final.csv"):
        # Test recommendations
        customer_id = "CUS00001"

        print(f"\n🎯 Testing recommendations for {customer_id}...")

        methods = ['hybrid', 'collaborative', 'content']
        for method in methods:
            result = service.get_recommendations(customer_id, 3, method)
            if result['success']:
                print(f"\n{method.upper()} RECOMMENDATIONS:")
                for rec in result['recommendations']:
                    print(
                        f"  • {rec['recipe_name']} (Score: {rec['score']:.3f})")
            else:
                print(f"❌ Error with {method}: {result['error']}")

        # Test stats
        stats = service.get_system_stats()
        print(f"\nSYSTEM STATUS: {stats['status']}")
        print(f"TRAINED MODELS: {', '.join(stats.get('trained_models', []))}")

    else:
        print("❌ Failed to initialize hybrid service")
