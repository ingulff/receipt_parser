PRAGMA user_version = 1;

PRAGMA journal_mode = WAL;

CREATE TABLE receipt_identity
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    'url' TEXT,
    fiscal_number VARCHAR(16) NOT NULL,
    fiscal_sign VARCHAR(16) NOT NULL,
    fiscal_datetime VARCHAR(32) NOT NULL,
    register_number VARCHAR(16) NOT NULL,
    'status' INTEGER,
    updated_datetime VARCHAR(32),
    
    UNIQUE(fiscal_number, fiscal_sign)
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
    seller_id INTEGER NOT NULL,
    brand_id INTEGER NOT NULL,

    FOREIGN KEY(seller_id) REFERENCES seller(id) ON DELETE CASCADE,
    FOREIGN KEY(brand_id) REFERENCES brand(id) ON DELETE CASCADE,
    PRIMARY KEY(seller_id, brand_id)
);

CREATE TABLE store
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    seller_id INTEGER NOT NULL,
    'address' TEXT,

    FOREIGN KEY(seller_id) REFERENCES seller(id) ON DELETE CASCADE
);

CREATE TABLE cash_register
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    serial_number VARCHAR(32) NOT NULL UNIQUE,
    'name' TEXT,
    store_id INTEGER,

    FOREIGN KEY(store_id) REFERENCES store(id) ON DELETE CASCADE
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
    receipt_identity_id INTEGER NOT NULL UNIQUE,
    seller_id INTEGER NOT NULL,
    cash_register_id INTEGER NOT NULL,
    total_amount REAL NOT NULL,
    total_vat REAL NOT NULL,
    update_datetime VARCHAR(32),

    FOREIGN KEY(receipt_identity_id) REFERENCES receipt_identity(id) ON DELETE CASCADE,
    FOREIGN KEY(seller_id) REFERENCES seller(id) ON DELETE CASCADE,
    FOREIGN KEY(cash_register_id) REFERENCES cash_register(id) ON DELETE CASCADE
);

CREATE TABLE receipt_item
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_meta_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    price REAL NOT NULL,
    quantity REAL NOT NULL,
    vat_amount REAL NOT NULL,
    vat_rate INTEGER NOT NULL,
    unit TEXT,
    discount TEXT,

    FOREIGN KEY(receipt_meta_id) REFERENCES receipt_meta(id) ON DELETE CASCADE,
    FOREIGN KEY(product_id) REFERENCES product(id) ON DELETE CASCADE
);

CREATE TABLE payment_type
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code INTEGER NOT NULL,
    'name' TEXT
);

CREATE TABLE receipt_payment
(
    receipt_meta_id INTEGER NOT NULL,
    payment_type_id INTEGER NOT NULL,
    amount REAL,
    paid_datetime VARCHAR(32),
    currency VARCHAR(32),
    details TEXT,

    FOREIGN KEY(receipt_meta_id) REFERENCES receipt_meta(id) ON DELETE CASCADE,
    FOREIGN KEY(payment_type_id) REFERENCES payment_type(id),
    PRIMARY KEY (receipt_meta_id, payment_type_id)
);

INSERT INTO
    payment_type(
        code,
        name
    )
VALUES
    (1, "cash"),
    (2, "card")
