CREATE DATABASE IF NOT EXISTS `pharmacy_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `pharmacy_db`;

CREATE TABLE IF NOT EXISTS `auth_user` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(150) NOT NULL UNIQUE,
    `password` VARCHAR(128) NOT NULL,
    `first_name` VARCHAR(150) NOT NULL DEFAULT '',
    `last_name` VARCHAR(150) NOT NULL DEFAULT '',
    `email` VARCHAR(254) NOT NULL DEFAULT '',
    `is_staff` TINYINT(1) NOT NULL DEFAULT 0,
    `is_active` TINYINT(1) NOT NULL DEFAULT 1,
    `is_superuser` TINYINT(1) NOT NULL DEFAULT 0,
    `last_login` DATETIME(6) NULL,
    `date_joined` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `inventory_category` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL UNIQUE,
    `description` TEXT NULL,
    `icon` VARCHAR(50) NOT NULL DEFAULT 'bi-capsule',
    `color` VARCHAR(20) NOT NULL DEFAULT '#0068C2',
    `bg_color` VARCHAR(20) NOT NULL DEFAULT '#E8F4FD'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `inventory_product` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(150) NOT NULL UNIQUE,
    `description` TEXT NULL,
    `instruction` TEXT NULL,
    `warning` TEXT NULL,
    `price` DECIMAL(10, 2) NOT NULL DEFAULT 50.00,
    `stock_quantity` INT NOT NULL DEFAULT 0,
    `expiry_date` DATE NULL,
    `rx_required` TINYINT(1) NOT NULL DEFAULT 0,
    `dosage_form` VARCHAR(100) NOT NULL DEFAULT 'Таблетки',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `category_id` INT NOT NULL,
    CONSTRAINT `fk_product_category` FOREIGN KEY (`category_id`)
        REFERENCES `inventory_category` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `inventory_order` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `created_by_id` INT NOT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `status` VARCHAR(20) NOT NULL DEFAULT 'COMPLETED',
    `total_amount` DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    `stock_deducted` TINYINT(1) NOT NULL DEFAULT 1,
    CONSTRAINT `fk_order_user` FOREIGN KEY (`created_by_id`)
        REFERENCES `auth_user` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `inventory_orderitem` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `order_id` INT NOT NULL,
    `product_id` INT NOT NULL,
    `quantity` INT NOT NULL DEFAULT 1,
    `unit_price` DECIMAL(10, 2) NOT NULL,
    CONSTRAINT `fk_orderitem_order` FOREIGN KEY (`order_id`)
        REFERENCES `inventory_order` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_orderitem_product` FOREIGN KEY (`product_id`)
        REFERENCES `inventory_product` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
