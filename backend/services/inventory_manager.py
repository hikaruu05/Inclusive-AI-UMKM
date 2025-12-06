import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Dict, List
import json
import os

from backend.models.database import Product, StockMovement, Invoice, PaymentItem, Payment
from backend.services.payment_ocr import PaymentOCR

class InventoryManager:
    """
    Service to manage inventory tracking and predictive analysis
    """
    
    def __init__(self):
        self.ocr = PaymentOCR()
        self.low_stock_threshold = int(os.getenv("LOW_STOCK_THRESHOLD", "10"))
        self.forecast_days = int(os.getenv("FORECAST_DAYS", "7"))
    
    async def process_invoice_image(self, image_path: str, db: Session) -> Dict:
        """
        Process supplier invoice using OCR + LLM
        Extracts items and quantities to update inventory
        """
        # Extract text using OCR
        ocr_result = self.ocr.extract_text(image_path)
        full_text = ' '.join([result[1] for result in ocr_result])
        
        # Parse with LLM (using OpenAI or Gemini)
        parsed_items = await self._parse_invoice_with_llm(full_text)
        
        # Create invoice record
        invoice = Invoice(
            image_path=image_path,
            ocr_text=full_text,
            parsed_items=json.dumps(parsed_items),
            invoice_date=datetime.utcnow(),
            is_processed=False
        )
        
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        
        # Update inventory
        items_added = 0
        for item in parsed_items:
            product = db.query(Product).filter(
                Product.name.ilike(f"%{item['name']}%")
            ).first()
            
            if product:
                # Update existing product stock
                previous_stock = product.current_stock
                new_stock = previous_stock + item['quantity']
                
                movement = StockMovement(
                    product_id=product.id,
                    movement_type="restock",
                    quantity=item['quantity'],
                    previous_stock=previous_stock,
                    new_stock=new_stock,
                    reference_type="invoice",
                    reference_id=invoice.id,
                    notes=f"Restocked from invoice {invoice.id}"
                )
                
                product.current_stock = new_stock
                product.last_restocked_at = datetime.utcnow()
                
                db.add(movement)
                items_added += 1
        
        invoice.is_processed = True
        invoice.processed_at = datetime.utcnow()
        db.commit()
        
        return {
            "invoice_id": invoice.id,
            "items_count": items_added,
            "items": parsed_items
        }
    
    async def _parse_invoice_with_llm(self, text: str) -> List[Dict]:
        """
        Use LLM to parse invoice text into structured data
        Falls back to simple regex if LLM not available
        """
        try:
            # Try OpenAI first
            import openai
            openai.api_key = os.getenv("OPENAI_API_KEY")
            
            if openai.api_key:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an invoice parser. Extract items, quantities, and units from the invoice text. Return JSON array with format: [{\"name\": \"item_name\", \"quantity\": 10, \"unit\": \"kg\"}]"
                        },
                        {
                            "role": "user",
                            "content": f"Parse this invoice:\n\n{text}"
                        }
                    ],
                    temperature=0.1
                )
                
                result = response.choices[0].message.content
                return json.loads(result)
        
        except Exception as e:
            print(f"LLM parsing failed: {e}, falling back to regex")
        
        # Fallback: Simple regex parsing
        return self._parse_invoice_regex(text)
    
    def _parse_invoice_regex(self, text: str) -> List[Dict]:
        """
        Fallback invoice parser using regex
        """
        import re
        
        items = []
        
        # Pattern: quantity + unit + name
        # Example: "50 kg Gula Pasir" or "100 pcs Kopi Bubuk"
        pattern = r'(\d+(?:[.,]\d+)?)\s*(kg|gram|liter|pcs|box|karton|pack)\s+([A-Za-z\s]+)'
        
        matches = re.findall(pattern, text, re.IGNORECASE)
        
        for match in matches:
            quantity_str, unit, name = match
            quantity = float(quantity_str.replace(',', '.'))
            
            items.append({
                "name": name.strip(),
                "quantity": quantity,
                "unit": unit.lower()
            })
        
        return items
    
    def deduct_stock_from_payment(
        self,
        db: Session,
        payment_id: int,
        items: List[Dict]
    ) -> Dict:
        """
        Deduct inventory when payment is verified
        
        items: List of {"product_id": int, "quantity": float}
        """
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        
        if not payment or not payment.is_verified:
            return {"status": "error", "message": "Payment not verified"}
        
        deducted_items = []
        
        for item in items:
            product = db.query(Product).filter(Product.id == item['product_id']).first()
            
            if not product:
                continue
            
            previous_stock = product.current_stock
            new_stock = previous_stock - item['quantity']
            
            # Create stock movement
            movement = StockMovement(
                product_id=product.id,
                movement_type="sale",
                quantity=-item['quantity'],  # Negative for sale
                previous_stock=previous_stock,
                new_stock=new_stock,
                reference_type="payment",
                reference_id=payment_id,
                notes=f"Sold via payment {payment_id}"
            )
            
            # Update product
            product.current_stock = new_stock
            product.total_sold += item['quantity']
            
            # Create payment item record
            payment_item = PaymentItem(
                payment_id=payment_id,
                product_id=product.id,
                quantity=item['quantity'],
                unit_price=product.price,
                subtotal=product.price * item['quantity']
            )
            
            db.add(movement)
            db.add(payment_item)
            deducted_items.append(product.name)
        
        db.commit()
        
        return {
            "status": "success",
            "items_deducted": deducted_items,
            "count": len(deducted_items)
        }
    
    async def forecast_stock_needs(
        self,
        product_id: int,
        days: int,
        db: Session
    ) -> Dict:
        """
        Forecast stock needs for next N days using time-series analysis
        """
        product = db.query(Product).filter(Product.id == product_id).first()
        
        if not product:
            return {"error": "Product not found"}
        
        # Get sales history (last 30 days)
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        movements = db.query(StockMovement).filter(
            StockMovement.product_id == product_id,
            StockMovement.movement_type == "sale",
            StockMovement.created_at >= cutoff_date
        ).all()
        
        if len(movements) < 3:
            return {
                "product": product.name,
                "message": "Not enough data for forecast",
                "recommendation": "Need at least 3 sales transactions"
            }
        
        # Calculate average daily sales
        total_sold = sum(abs(m.quantity) for m in movements)
        days_tracked = (datetime.utcnow() - movements[-1].created_at).days or 1
        avg_daily_sales = total_sold / days_tracked
        
        # Forecast
        predicted_sales = avg_daily_sales * days
        current_stock = product.current_stock
        stock_after_forecast = current_stock - predicted_sales
        
        # Determine if restocking needed
        needs_restock = stock_after_forecast < product.min_stock
        
        if needs_restock:
            needed_quantity = product.min_stock - stock_after_forecast + (avg_daily_sales * 3)  # Add 3 days buffer
        else:
            needed_quantity = 0
        
        return {
            "product": product.name,
            "current_stock": current_stock,
            "unit": product.unit,
            "forecast_period_days": days,
            "avg_daily_sales": round(avg_daily_sales, 2),
            "predicted_sales_next_n_days": round(predicted_sales, 2),
            "stock_after_n_days": round(stock_after_forecast, 2),
            "min_stock_threshold": product.min_stock,
            "needs_restock": needs_restock,
            "recommended_order_quantity": round(needed_quantity, 2) if needs_restock else 0,
            "warning": f"⚠️ Order {round(needed_quantity, 2)} {product.unit} now!" if needs_restock else "✅ Stock sufficient"
        }
    
    def get_inventory_summary(self, db: Session) -> Dict:
        """
        Get overall inventory summary
        """
        total_products = db.query(Product).count()
        
        low_stock_count = db.query(Product).filter(
            Product.current_stock <= Product.min_stock
        ).count()
        
        out_of_stock_count = db.query(Product).filter(
            Product.current_stock <= 0
        ).count()
        
        total_value = db.query(
            func.sum(Product.current_stock * Product.price)
        ).scalar() or 0
        
        return {
            "total_products": total_products,
            "low_stock_alerts": low_stock_count,
            "out_of_stock": out_of_stock_count,
            "total_inventory_value": round(total_value, 2),
            "status": "⚠️ Attention needed" if low_stock_count > 0 else "✅ All good"
        }
