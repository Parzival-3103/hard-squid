CREATE DATABASE IF NOT EXISTS hard_squid CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE hard_squid;

CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  email VARCHAR(160) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('admin','empleado','cliente') NOT NULL DEFAULT 'cliente',
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS products (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(160) NOT NULL,
  description TEXT NOT NULL,
  price DECIMAL(10,2) NOT NULL,
  cost DECIMAL(10,2) NOT NULL DEFAULT 0,
  stock INT NOT NULL DEFAULT 0,
  category ENUM('Dama','Caballero','Unisex') NOT NULL,
  size VARCHAR(80) NOT NULL DEFAULT 'Unitalla',
  image VARCHAR(255) NOT NULL,
  featured BOOLEAN NOT NULL DEFAULT FALSE,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS orders (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  total DECIMAL(10,2) NOT NULL,
  status ENUM('pendiente','pagada','cancelada') NOT NULL DEFAULT 'pagada',
  payment_method VARCHAR(50) NOT NULL,
  shipping_address VARCHAR(255) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_orders_users FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS order_items (
  id INT AUTO_INCREMENT PRIMARY KEY,
  order_id INT NOT NULL,
  product_id INT NULL,
  product_name VARCHAR(160) NOT NULL,
  unit_price DECIMAL(10,2) NOT NULL,
  quantity INT NOT NULL,
  subtotal DECIMAL(10,2) NOT NULL,
  CONSTRAINT fk_items_orders FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
  CONSTRAINT fk_items_products FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
) ENGINE=InnoDB;

INSERT INTO products (name,description,price,cost,stock,category,size,image,featured)
SELECT * FROM (SELECT 'Playera Core Training','Playera deportiva transpirable de secado rápido para entrenamientos intensos.',499.00,245.00,28,'Caballero','CH, M, G, XG','img/producto-hombre.jpg',TRUE) seed
WHERE NOT EXISTS (SELECT 1 FROM products LIMIT 1);
INSERT INTO products (name,description,price,cost,stock,category,size,image,featured)
SELECT 'Leggings Deep Motion','Leggings de cintura alta, soporte medio y tejido flexible que no transparenta.',749.00,360.00,19,'Dama','CH, M, G','img/producto-mujer.jpg',TRUE
WHERE (SELECT COUNT(*) FROM products)=1;
INSERT INTO products (name,description,price,cost,stock,category,size,image,featured)
SELECT 'Sudadera Kraken Essential','Sudadera unisex de tacto suave y corte relajado para antes y después del entrenamiento.',899.00,430.00,15,'Unisex','CH, M, G, XG','img/producto-unisex.jpg',TRUE
WHERE (SELECT COUNT(*) FROM products)=2;

