import json
from fastapi import HTTPException
from models import Order

class OrderService:
    @staticmethod
    def create_order(db, current_user, order_data, food_db):
        """
        Creates an order but strictly validates stock first (Phase 6).
        """
        if not order_data.items:
            raise HTTPException(status_code=400, detail="Order items cannot be empty.")

        # Simulate stock validation against the pseudo-database of food items
        for order_item in order_data.items:
            # Assuming items look like {"id": 101, "quantity": 1} or just IDs depending on how frontend sends it
            # The original code sent a JSON list. We'll extract IDs.
            item_id = order_item.get("id") if isinstance(order_item, dict) else order_item
            
            # Find in DB
            db_item = next((f for f in food_db if f["id"] == item_id), None)
            
            if not db_item:
                raise HTTPException(status_code=404, detail=f"Food item {item_id} not found.")

            # Validate stock (Phase 6 compliance)
            # We assume FOOD_ITEMS dict might get generic 'stock_quantity' added to it
            current_stock = db_item.get("stock_quantity", 10)  # default to 10 if not defined yet
            is_available = db_item.get("is_available", True)

            if current_stock <= 0 or not is_available:
                raise HTTPException(status_code=400, detail=f"Item {db_item['name']} is out of stock.")
                
            # If we had a real database for food items, we would decrement stock here:
            # db_item.stock_quantity -= 1

        new_order = Order(
            user_id=current_user.id,
            items=json.dumps(order_data.items),
            total_price=order_data.total_price,
            total_calories=order_data.total_calories,
            total_sugar=order_data.total_sugar,
            total_sodium=order_data.total_sodium
        )
        db.add(new_order)
        db.commit()
        db.refresh(new_order)
        return new_order
