import json
from ml_engine.inference_service import get_ml_probability
from config.severity_weights import SEVERITY_WEIGHTS

class RecommendationService:
    def __init__(self, alpha=0.6):
        # α = 0.6 (rule-heavy for medical safety)
        self.alpha = alpha
        
    def _parse_lists(self, raw_data):
        if not raw_data or raw_data == "None":
            return []
        if isinstance(raw_data, str):
            try:
                return json.loads(raw_data)
            except:
                return []
        return raw_data

    def evaluate_food_item(self, food_item, profile_dict):
        """
        Evaluate a single food item combining RuleScore and MLProbability.
        Returns (final_score, risk_level, insight, tag)
        """
        # --- 1. Hard Binary Safety Filters ---
        allergies = self._parse_lists(profile_dict.get('allergies', []))
        diseases = [d.lower() for d in self._parse_lists(profile_dict.get('disease', []))]
        
        # Block allergens
        food_name = food_item['name'].lower()
        for alg in allergies:
            alg_name = alg.get('name', '').lower() if isinstance(alg, dict) else alg.lower() if isinstance(alg, str) else ""
            if not alg_name: continue
            
            # Simple stemming for plural (e.g., 'peanuts' -> 'peanut')
            base_alg_name = alg_name[:-1] if alg_name.endswith('s') else alg_name
            
            if base_alg_name in food_name or alg_name in food_name:
                return 0, 2, f"Blocked: Contains {alg.get('name', alg_name)} (Allergen)", "Danger"

        # Block extreme sugar if diabetic severe
        severity = profile_dict.get('severity', {})
        if isinstance(severity, str):
            try:
                severity = json.loads(severity)
            except:
                severity = {}
                
        is_diabetic = 'diabetes' in diseases
        diabetic_severity = severity.get("Diabetes", "Moderate")
        
        if is_diabetic and diabetic_severity == "Severe" and food_item.get('sugar', 0) > 15:
            return 0, 2, "Blocked: Excessive sugar for Severe Diabetes", "Danger"
            
        # Block high sodium if hypertension severe
        is_hypertensive = 'hypertension' in diseases
        ht_severity = severity.get("Hypertension", "Moderate")
        
        if is_hypertensive and ht_severity == "Severe" and food_item.get('sodium', 0) > 1200:
            return 0, 2, "Blocked: Excessive sodium for Severe Hypertension", "Danger"

        # --- 2. Calculate RuleScore (0-100) ---
        rule_score = 95
        penalties = []
        
        # Apply severity multipliers to penalties
        if is_diabetic:
            sugar_mult = SEVERITY_WEIGHTS.get(diabetic_severity, 1.0)
            if food_item.get('sugar', 0) > 10:
                rule_score -= 20 * sugar_mult
                penalties.append("High Sugar")
            if food_item.get('carbs', 0) > 50:
                rule_score -= 10 * sugar_mult
                penalties.append("High Carbs")
                
        if is_hypertensive:
            sodium_mult = SEVERITY_WEIGHTS.get(ht_severity, 1.0)
            if food_item.get('sodium', 0) > 800:
                rule_score -= 25 * sodium_mult
                penalties.append("High Sodium")

        # Dietary preference logic
        diet = profile_dict.get('dietary_preference', 'Non-Veg')
        meat_keywords = ['chicken', 'beef', 'fish', 'salmon', 'pepperoni', 'meat', 'bacon']
        if diet == 'Veg' and any(k in food_name for k in meat_keywords):
            return 0, 2, "Violates Vegetarian Preference", "Danger"
            
        rule_score = max(0, min(100, rule_score))
        
        # Normalize rule_score to 0-1 for formula matching
        normalized_rule_score = rule_score / 100.0

        # --- 3. Calculate MLProbability (0-1) ---
        ml_prob = get_ml_probability(profile_dict, food_item)
        
        # --- 4. Final Hybrid Score ---
        # FinalScore = α * RuleScore + (1 - α) * MLProbability
        final_probability = (self.alpha * normalized_rule_score) + ((1 - self.alpha) * ml_prob)
        final_score = int(final_probability * 100)
        
        # Formulate insights
        if final_score >= 80:
            risk_level = 0
            insight = "Perfect match for your health profile."
        elif final_score >= 50:
            risk_level = 1
            insight = f"Caution: {', '.join(penalties)}" if penalties else "Moderate nutrition match."
        else:
            risk_level = 2
            insight = f"Restricted: {', '.join(penalties)}" if penalties else "High risk for your profile."

        # Assign tag
        low_gi_keywords = ['quinoa', 'oats', 'lentils', 'broccoli', 'almonds']
        if food_item.get('sugar', 0) == 0: tag = "Sugar Free"
        elif any(k in food_name for k in low_gi_keywords): tag = "Low GI"
        elif food_item.get('carbs', 0) < 20: tag = "Low Carb"
        elif food_item.get('protein', 0) > 25: tag = "High Protein"
        elif food_item.get('sugar', 0) < 5: tag = "Low Sugar"
        else: tag = "Standard"

        return final_score, risk_level, insight, tag

    def get_intelligent_menu(self, food_items, profile_dict):
        """
        Process the entire menu and return scored items.
        (Phase 6 Stock Synchronization is also applied before returning)
        """
        intelligent_menu = []
        for item in food_items:
            # Phase 6: Ensure out-of-stock items aren't recommended
            if item.get("stock_quantity", 1) <= 0 or not item.get("is_available", True):
                continue
                
            score, risk, insight, tag = self.evaluate_food_item(item, profile_dict)
            
            item_copy = item.copy()
            item_copy['match_score'] = score
            item_copy['risk_level'] = risk
            item_copy['insight'] = insight
            item_copy['tag'] = tag
            
            intelligent_menu.append(item_copy)
            
        return intelligent_menu
