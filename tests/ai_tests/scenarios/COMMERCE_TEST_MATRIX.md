# Commerce / Autobiz test matrix (not implemented in Stud)

The following scenarios were specified for a **product ordering + payment + logistics** stack. **Stud** is a **medical education** platform and does **not** ship:

- Product catalog, variants (e.g. iPhone colors), inventory
- Bank details / payment links in database
- Payment verification, PDF receipts, Autobiz integration
- Vendor or logistics HTTP APIs

This file preserves the **intended** acceptance criteria so you can:

1. Port these scenarios to a **commerce microservice**, or  
2. Add a **mock commerce API** and wire `tests/ai_tests/agents/vendor_agent.py` and `logistics_agent.py` to it.

## 1. Product available

Capture: product name, price, attributes, quantity demanded.

## 2. Product not available / similar products

- Variant mismatch: desired attribute not in stock but another variant exists (e.g. black vs red).
- Product not available at all.

## 3. Purchase decision — payment in DB

User buys; bank details or payment link returned from DB.

## 4. Payment not in DB

Graceful handling when credentials missing.

## 5. Payment verification (vendor)

Match date, product, price before notifying vendor; PDF receipt to Autobiz.

- Inappropriate receipt
- Invalid receipt
- Valid receipt

## 6. Logistics

- Customer accepts suggested delivery date.
- Rescheduling (customer unavailable).
- Vendor receives: time, date, delivery cost, address.

## Chat history variants (for future implementation)

- Long vs short history
- History with many prior products
- Fresh session

When a commerce API exists, add `test_commerce_*.py` and point `BASE_URL` at that service (or add a second env `COMMERCE_BASE_URL`).
