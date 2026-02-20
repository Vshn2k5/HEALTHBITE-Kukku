from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from dependencies import get_current_user
from models import User, HealthProfile, Order
from schemas import OrderCreate, OrderResponse
from services.recommendation_service import RecommendationService
from services.order_service import OrderService
import json

router = APIRouter(
    prefix="/api/menu",
    tags=["menu"]
)

# Mock Food Data (Extended with nutrition for AI analysis)
FOOD_ITEMS = [
    {"id": 101, "name": "Margherita Pizza", "price": 250, "image": "🍕", "calories": 650, "sugar": 8, "protein": 15, "sodium": 1200, "carbs": 80, "description": "Fresh mozzarella, basil & tomato sauce"},
    {"id": 102, "name": "Fresh Green Salad", "price": 180, "image": "🥗", "calories": 150, "sugar": 2, "protein": 5, "sodium": 150, "carbs": 10, "description": "Mixed greens with house dressing"},
    {"id": 103, "name": "Gourmet Burger", "price": 220, "image": "🍔", "calories": 850, "sugar": 12, "protein": 35, "sodium": 1500, "carbs": 60, "description": "Beef patty with cheese & veggies"},
    {"id": 104, "name": "Ramen Noodles", "price": 280, "image": "🍜", "calories": 550, "sugar": 4, "protein": 20, "sodium": 1800, "carbs": 70, "description": "Authentic Japanese noodle soup"},
    {"id": 105, "name": "Falafel Wrap", "price": 200, "image": "🥙", "calories": 420, "sugar": 3, "protein": 12, "sodium": 800, "carbs": 50, "description": "Crispy falafel with tahini sauce"},
    {"id": 106, "name": "Sushi Platter", "price": 320, "image": "🍱", "calories": 350, "sugar": 5, "protein": 18, "sodium": 900, "carbs": 45, "description": "Assorted sushi with wasabi"},
    {"id": 107, "name": "Spicy Tacos", "price": 190, "image": "🌮", "calories": 480, "sugar": 2, "protein": 22, "sodium": 1100, "carbs": 40, "description": "Seasoned meat with fresh toppings"},
    {"id": 108, "name": "Chocolate Cake", "price": 150, "image": "🍰", "calories": 520, "sugar": 45, "protein": 6, "sodium": 300, "carbs": 65, "description": "Rich & decadent chocolate delight"},
    {"id": 109, "name": "Grilled Salmon", "price": 350, "image": "🐟", "calories": 400, "sugar": 0, "protein": 42, "sodium": 400, "carbs": 0, "description": "Lean protein, zero carbs."},
    {"id": 110, "name": "Quinoa Bowl", "price": 230, "image": "🥣", "calories": 320, "sugar": 2, "protein": 14, "sodium": 200, "carbs": 45, "description": "Low GI, high protein."},
    {"id": 111, "name": "French Fries", "price": 120, "image": "🍟", "calories": 450, "sugar": 1, "protein": 4, "sodium": 800, "carbs": 60, "description": "Crispy golden fried potatoes"},
    {"id": 112, "name": "Pepperoni Pizza", "price": 290, "image": "🍕", "calories": 800, "sugar": 10, "protein": 30, "sodium": 1600, "carbs": 90, "description": "Spicy pepperoni with extra cheese"},
    {"id": 113, "name": "White Rice Bowl", "price": 90, "image": "🍚", "calories": 250, "sugar": 0, "protein": 4, "sodium": 10, "carbs": 55, "description": "Steamed premium white rice"},
    {"id": 114, "name": "Pasta Carbonara", "price": 270, "image": "🍝", "calories": 700, "sugar": 5, "protein": 25, "sodium": 1100, "carbs": 75, "description": "Creamy pasta with bacon and egg"},
    {"id": 115, "name": "Fried Chicken", "price": 240, "image": "🍗", "calories": 900, "sugar": 2, "protein": 40, "sodium": 1400, "carbs": 40, "description": "Deep-fried breaded chicken pieces"},
    {"id": 116, "name": "Vegetable Noodles", "price": 180, "image": "🥢", "calories": 450, "sugar": 6, "protein": 8, "sodium": 1200, "carbs": 65, "description": "Stir-fried noodles with farm veggies"},
    {"id": 117, "name": "Double Cheese Burger", "price": 320, "image": "🍔", "calories": 1100, "sugar": 15, "protein": 50, "sodium": 1800, "carbs": 70, "description": "Extra beef patty with double molten cheese"},
    {"id": 118, "name": "Crispy Onion Rings", "price": 140, "image": "🧅", "calories": 600, "sugar": 4, "protein": 5, "sodium": 950, "carbs": 55, "description": "Crispy batter-fried onion rings"},
    {"id": 119, "name": "Donut Assortment", "price": 160, "image": "🍩", "calories": 580, "sugar": 48, "protein": 6, "sodium": 420, "carbs": 75, "description": "Sugary glazed donuts with sprinkles"},
    {"id": 120, "name": "Sweet Iced Tea", "price": 80, "image": "🍹", "calories": 180, "sugar": 42, "protein": 0, "sodium": 30, "carbs": 45, "description": "Refreshing but highly sweetened tea"},
    {"id": 121, "name": "Beef Lasagna", "price": 300, "image": "🥘", "calories": 850, "sugar": 8, "protein": 35, "sodium": 1400, "carbs": 60, "description": "Layers of pasta with rich meat sauce and cheese"},
    {"id": 122, "name": "Mac & Cheese", "price": 180, "image": "🧀", "calories": 650, "sugar": 4, "protein": 20, "sodium": 1100, "carbs": 70, "description": "Classic creamy macaroni and cheese"},
    {"id": 123, "name": "Chicken Sandwich", "price": 210, "image": "🥪", "calories": 550, "sugar": 6, "protein": 28, "sodium": 950, "carbs": 45, "description": "Grilled chicken breast with mayo and lettuce"},
    {"id": 124, "name": "Fruit Custard", "price": 110, "image": "🍧", "calories": 280, "sugar": 35, "protein": 8, "sodium": 120, "carbs": 40, "description": "Creamy custard with seasonal fruits"},
    {"id": 125, "name": "Baked Potatoes", "price": 130, "image": "🥔", "calories": 300, "sugar": 2, "protein": 6, "sodium": 450, "carbs": 55, "description": "Fluffy baked potatoes with sour cream"},
    {"id": 126, "name": "Fruit Punch", "price": 100, "image": "🥤", "calories": 220, "sugar": 40, "protein": 1, "sodium": 50, "carbs": 55, "description": "Sweet mixed fruit juice blend"},
    {"id": 127, "name": "Quinoa Veggie Bowl", "price": 190, "image": "🥣", "calories": 320, "sugar": 0, "protein": 12, "sodium": 150, "carbs": 45, "description": "High fiber quinoa with mixed vegetables"},
    {"id": 128, "name": "Steamed Broccoli", "price": 120, "image": "🥦", "calories": 55, "sugar": 0, "protein": 4, "sodium": 25, "carbs": 10, "description": "Fresh steamed broccoli florets"},
    {"id": 129, "name": "Roasted Almonds", "price": 150, "image": "🥜", "calories": 160, "sugar": 0, "protein": 6, "sodium": 5, "carbs": 6, "description": "Unsalted dry roasted almonds"},
    {"id": 130, "name": "Greek Yogurt Plain", "price": 140, "image": "🍦", "calories": 100, "sugar": 0, "protein": 18, "sodium": 60, "carbs": 6, "description": "Creamy sugar-free greek yogurt"}
]

@router.get("/intelligent")
async def get_intelligent_menu(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get user profile
    profile_db = db.query(HealthProfile).filter(HealthProfile.user_id == current_user.id).first()
    
    # Simple profile if none exists
    profile = {
        "age": 25,
        "disease": [],
        "allergies": [],
        "dietary_preference": "Non-Veg",
        "target_calories": 2000
    }
    
    if profile_db:
        try:
            diseases = json.loads(profile_db.disease) if profile_db.disease else []
            allergies = json.loads(profile_db.allergies) if profile_db.allergies and profile_db.allergies != "None" else []
        except:
            diseases = []
            allergies = []
        
        profile = {
            "age": profile_db.age,
            "disease": diseases,
            "allergies": allergies,
            "dietary_preference": profile_db.dietary_preference or "Non-Veg",
            "target_calories": 2000 
        }

    # Initialize Recommendation Service
    recommender = RecommendationService(alpha=0.6)
    
    # Get intelligent menu (applies stock/availability filters internally)
    intelligent_menu = recommender.get_intelligent_menu(FOOD_ITEMS, profile)
        
    return intelligent_menu


@router.post("/order")
async def place_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_order = OrderService.create_order(db, current_user, order_data, FOOD_ITEMS)
    return new_order

@router.get("/history")
async def get_order_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    orders = db.query(Order).filter(Order.user_id == current_user.id).order_by(Order.id.desc()).all()
    return orders
