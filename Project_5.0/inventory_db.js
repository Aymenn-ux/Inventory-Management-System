inventory_db NOSQL

use inventory_db

db.createCollection("products")
db.createCollection("suppliers")
db.createCollection("transactions")
db.createCollection("categories")
db.createCollection("admins")
orders_collection = db['orders']
db.products.insertMany([{
  
    product_id: "P001",
    name: "Laptop",
    category_id: "C001",
    supplier_id: "S001",
    price: 1000,
    quantity: 50
  },
  {
    product_id: "P002",
    name: "Smartphone",
    category_id: "C002",
    supplier_id: "S002",
    price: 600,
    quantity: 100
  },
  {
    product_id: "P003",
    name: "Desk Chair",
    category_id: "C003",
    supplier_id: "S003",
    price: 150,
    quantity: 75
  }
  ]
)


db.suppliers.insertMany([
  {
    supplier_id: "S001",
    name: "TechSupply Co.",
    contact: {
      phone: "123-456-7890",
      email: "contact@techsupply.com"
    },
    address: {
      street: "123 Tech Ave",
      city: "Tech City",
      state: "TX",
      zip: "75001"
    }
  },
  {
    supplier_id: "S002",
    name: "Mobile Solutions",
    contact: {
      phone: "987-654-3210",
      email: "info@mobilesolutions.com"
    },
    address: {
      street: "456 Mobile St",
      city: "Mobile Town",
      state: "CA",
      zip: "90001"
    }
  },
  {
    supplier_id: "S003",
    name: "Office Gear",
    contact: {
      phone: "555-123-4567",
      email: "support@officegear.com"
    },
    address: {
      street: "789 Office Blvd",
      city: "Office City",
      state: "NY",
      zip: "10001"
    }
  }
]
)

db.categories.insertMany([
  {
    category_id: "C001",
    name: "Electronics",
    description: "Devices and gadgets related to technology."
  },
  {
    category_id: "C002",
    name: "Mobile Phones",
    description: "Handheld communication devices."
  },
  {
    category_id: "C003",
    name: "Office Supplies",
    description: "Furniture and accessories for office use."
  }
]
)

db.transactions.insertMany([
  {
    transaction_id: "T001",
    product_id: "P001",
    date: "2025-01-10",
    quantity: 5,
    total_price: 5000,
    customer_name: "John Doe",
    payment_method: "Credit Card"
  },
  {
    transaction_id: "T002",
    product_id: "P002",
    date: "2025-01-11",
    quantity: 10,
    total_price: 6000,
    customer_name: "Jane Smith",
    payment_method: "PayPal"
  },
  {
    transaction_id: "T003",
    product_id: "P003",
    date: "2025-01-11",
    quantity: 3,
    total_price: 450,
    customer_name: "Alice Johnson",
    payment_method: "Debit Card"
  }
])

