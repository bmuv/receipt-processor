from datetime import date, time

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import uuid
import math
from decimal import Decimal

app = FastAPI()

class Item(BaseModel):
    shortDescription: str
    price: Decimal

class Receipt(BaseModel):
    retailer: str
    purchaseDate: date # Expected format: YYYY-MM-DD
    purchaseTime: time # Expected format: HH:MM (24-hour clock)
    items: List[Item]
    total: Decimal

# In-memory store for receipt points
receipts_store = {}

def calculate_points(receipt: Receipt) -> int:
    points = 0

    # 1. One point per alphanumeric char in retailer
    points += sum(c.isalnum() for c in receipt.retailer)

    total = receipt.total

    #2. 50 points if total is a round dollar amount
    if total % 1 == 0:
        points += 50

    #3. 25 points if total is a multiple of .25
    if total % Decimal("0.25") == 0:
        points += 25

    #4. 5 points for every two items.
    points += (len(receipt.items) // 2) * 5

    #5. Points for item descriptions
    for item in receipt.items:
        desc = item.shortDescription.strip()
        if len(desc) % 3 == 0:
            price = item.price
            points += math.ceil(float(price * Decimal("0.2")))

    #6. 6 points if the day in purchaseDate is odd
    if receipt.purchaseDate.day % 2 == 1:
        points += 6

    #7. 10 points if purchaseTime is after 2:00pm and before 4:00pm
    if time(14, 0) < receipt.purchaseTime < time(16, 0):
        points += 10

    return points


@app.post("/receipts/process")
def process_receipt(receipt: Receipt):
    """
    Processes a receipt, calculates its points, and returns a unique receipt ID.
    """
    points = calculate_points(receipt)
    receipt_id = str(uuid.uuid4())
    receipts_store[receipt_id] = points
    return {"id": receipt_id}

@app.get("/receipts/{receipt_id}/points")
def get_points(receipt_id: str):
    """
    Retrieves the points awarded for a receipt given its ID.
    """
    if receipt_id not in receipts_store:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return {"points": receipts_store[receipt_id]}

