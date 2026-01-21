PRAGMA user_version = 1;

PRAGMA journal_mode = WAL;

CREATE TABLE receipt_url
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    'url' TEXT,
    fiscal_number VARCHAR(16) NOT NULL UNIQUE,
    fiscal_sign VARCHAR(16) NOT NULL UNIQUE,
    fiscal_datetime INTEGER NOT NULL,
    fiscal_datetime_string VARCHAR(32) NOT NULL,
    register_number VARCHAR(16) NOT NULL,
    'status' VARCHAR(16) -- todo
);

CREATE TABLE seller
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tin VARCHAR(16) UNIQUE NOT NULL,
    'name' TEXT
);

CREATE TABLE brand
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    'name' TEXT,
    normalized_name TEXT -- maybe unused
);

CREATE TABLE seller_brand
(
    seller_id INTEGER REFERENCES seller(id) ON DELETE CASCADE,
    brand_id INTEGER REFERENCES brand(id) ON DELETE CASCADE
);

CREATE TABLE cash_register
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    serial_number VARCHAR(32) NOT NULL UNIQUE,
    'name' TEXT
);

CREATE TABLE store
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    seller_id INTEGER REFERENCES seller(id) ON DELETE CASCADE,
    cash_register_id INTEGER REFERENCES cash_register(id) ON DELETE CASCADE,
    'address' TEXT
);

CREATE TABLE product
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pic VARCHAR(16) NOT NULL UNIQUE,
    pic_name TEXT,
    barcode VARCHAR(16) NOT NULL,
    'name' TEXT
);

CREATE TABLE receipt_meta
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fiscal_number VARCHAR(16) NOT NULL UNIQUE,
    fiscal_sign VARCHAR(16) NOT NULL UNIQUE,
    fiscal_datetime INTEGER NOT NULL,
    seller_id INTEGER REFERENCES Seller(id) ON DELETE CASCADE,
    cash_register_id INTEGER REFERENCES cash_register(id) ON DELETE CASCADE,
    register_number VARCHAR(16) NOT NULL,
    total_amount REAL NOT NULL,
    total_vat REAL NOT NULL,
    url_id INTEGER REFERENCES receipt_url(id) ON DELETE CASCADE
);

CREATE TABLE receipt
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_id INTEGER REFERENCES receipt(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES product(id) ON DELETE CASCADE,
    price REAL NOT NULL,
    quatity REAL NOT NULL,
    total_amount REAL NOT NULL,
    vat_amout REAL NOT NULL,
    vat_rate INTEGER NOT NULL,
    parsed_datetime INTEGER,
    unit TEXT,
    discount TEXT
);

CREATE TABLE payment_type
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code INTEGER NOT NULL, -- CASH, CARD, etc
    'name' TEXT
);

CREATE TABLE receipt_payment
(
    receipt_id INTEGER REFERENCES receipt(id) ON DELETE CASCADE,
    payment_type_id INTEGER REFERENCES payment_type(id) ON DELETE CASCADE,
    amount REAL,
    details TEXT,
    'datetime' INTEGER,
    currency VARCHAR(32)
);
