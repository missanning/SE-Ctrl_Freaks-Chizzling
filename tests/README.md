# ChizzlingPOS Test Suite

## Setup

1. Install test dependencies:
```bash
pip install -r requirements-test.txt
```

## Running Tests

Run all tests:
```bash
pytest tests/
```

Run with verbose output:
```bash
pytest tests/ -v
```

Run specific test class:
```bash
pytest tests/test_chizzling_pos.py::TestLogin -v
```

Run specific test:
```bash
pytest tests/test_chizzling_pos.py::TestLogin::test_database_connection -v
```

Show print statements:
```bash
pytest tests/ -v -s
```

## Test Coverage

The test suite covers:

### 1. Login & Authentication
- Database connection
- User credentials validation

### 2. Product Management
- Loading products from database
- Category validation
- Stock level checks

### 3. Cart Operations
- Cart logic (add, remove, clear)
- Quantity management logic

### 4. Transactions
- Date format validation
- Stock updates after purchase
- Payment calculations

### 5. Data Integrity
- Price validation
- Transaction referential integrity
- No null values in critical fields

## Test Structure

```
tests/
├── test_chizzling_pos.py    # Main test file
├── requirements-test.txt     # Test dependencies
└── README.md                 # This file
```

## Notes

- Tests use the actual database in `src/sales_inventory.db`
- Some tests modify data but restore it afterwards
- Tests focus on business logic and database operations without GUI interaction
