# ChizzlingPOS Test Suite

## Overview
Comprehensive automated tests for the ChizzlingPOS application covering 6 test cases with 26 individual tests.

## Test Cases

### Test Case 1: Product Browsing and Filtering by Category (5 tests)
- Load all products
- Filter by meals category
- Filter by snacks category
- Filter by drinks category
- Filter by alcohol category

### Test Case 2: Add to Cart Operations (4 tests)
- Add single product to cart
- Add multiple different products
- Add same product multiple times (quantity increment)
- Cart remains empty when no product selected

### Test Case 3: Cart Management (5 tests)
- Increase quantity with + button
- Decrease quantity with - button
- Remove item when quantity reaches 0
- Total updates correctly when quantity changes
- Cart display updates correctly

### Test Case 4: Payment Processing and Transaction Saving (4 tests)
- Successful payment with exact amount
- Successful payment with overpayment (change calculation)
- Transaction saved to database
- Stock decremented after purchase

### Test Case 5: Error Handling for Invalid Payment (5 tests)
- Error on empty payment field
- Error on non-numeric payment
- Error on insufficient payment
- Error on negative payment
- Error on zero payment

### Test Case 6: Cancel Order Functionality (3 tests)
- Cancel order clears cart
- Cancel order resets total to 0
- Cancel order clears payment entry

## Setup

1. Install test dependencies:
```bash
pip install -r requirements-test.txt
```

2. Ensure the database is set up:
```bash
python ../src/database_setup.py
```

## Running Tests

Run all tests:
```bash
pytest test_chizzling_pos.py -v
```

Run specific test:
```bash
pytest test_chizzling_pos.py::test_add_single_product_to_cart -v
```

Run tests with output:
```bash
pytest test_chizzling_pos.py -v -s
```

## Test Results
All 26 tests should pass if the ChizzlingPOS application is functioning correctly.
