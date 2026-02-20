from .model_loader import ModelLoader

def get_ml_probability(user_profile, food_item):
    """
    Interface connecting recommendation_service to the ML model.
    Extracts features and returns MLProbability.
    """
    loader = ModelLoader()
    model = loader.get_model()

    # In a real scenario, extract array of features
    # features = extract_features(user_profile, food_item)
    features = [[
        user_profile.get("age", 30),
        user_profile.get("bmi", 22.0),
        food_item.get("calories", 0),
        food_item.get("sugar", 0)
    ]]

    try:
        # Assuming model has predict_proba
        probabilities = model.predict_proba(features)
        # Probability of class 1 (healthy/recommended)
        return probabilities[0][1]
    except Exception as e:
        print(f"ML Inference Error: {e}")
        # Return neutral probability if inference fails
        return 0.5
