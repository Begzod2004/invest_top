CREATE TABLE `users`(
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `user_id` BIGINT NOT NULL,
    `telegram_user_id` DOUBLE NOT NULL,
    `image_url` VARCHAR(255) NULL,
    `first_name` VARCHAR(255) NOT NULL,
    `last_name` VARCHAR(255) NULL,
    `phone_number` VARCHAR(255) NOT NULL,
    `is_admin` BOOLEAN NOT NULL DEFAULT '0',
    `admin_role_id` BIGINT NULL,
    `is_blocked` BOOLEAN NOT NULL DEFAULT '0',
    `created_at` TIMESTAMP NOT NULL,
    `updated_at` TIMESTAMP NULL
);
ALTER TABLE
    `users` ADD INDEX `users_id_user_id_telegram_user_id_phone_number_index`(
        `id`,
        `user_id`,
        `telegram_user_id`,
        `phone_number`
    );
ALTER TABLE
    `users` ADD UNIQUE `users_user_id_unique`(`user_id`);
ALTER TABLE
    `users` ADD UNIQUE `users_telegram_user_id_unique`(`telegram_user_id`);
ALTER TABLE
    `users` ADD UNIQUE `users_phone_number_unique`(`phone_number`);
CREATE TABLE `admin_roles`(
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(255) NOT NULL,
    `permissions` JSON NOT NULL
);
CREATE TABLE `payment_methods`(
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `title` VARCHAR(255) NOT NULL,
    `type` ENUM('card', 'crypto') NOT NULL,
    `image_url` VARCHAR(255) NULL,
    `details` JSON NOT NULL,
    `is_active` BOOLEAN NOT NULL DEFAULT '1',
    `created_at` TIMESTAMP NOT NULL,
    `updated_at` TIMESTAMP NULL
);
ALTER TABLE
    `payment_methods` ADD INDEX `payment_methods_id_index`(`id`);
CREATE TABLE `subscription_plans`(
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `title` VARCHAR(255) NOT NULL,
    `duration_days` INT NOT NULL DEFAULT '1',
    `price` DOUBLE NOT NULL DEFAULT '0',
    `created_at` TIMESTAMP NOT NULL,
    `updated_at` TIMESTAMP NULL
);
ALTER TABLE
    `subscription_plans` ADD INDEX `subscription_plans_id_index`(`id`);
CREATE TABLE `subscriptions`(
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `user_id` BIGINT NOT NULL,
    `subscription_plan_id` BIGINT NOT NULL,
    `start_date` TIMESTAMP NOT NULL,
    `end_date` TIMESTAMP NOT NULL,
    `status` ENUM(
        'pending_user',
        'active',
        'expired',
        'canceled'
    ) NOT NULL,
    `created_at` TIMESTAMP NOT NULL,
    `created_admin_id` BIGINT NOT NULL
);
ALTER TABLE
    `subscriptions` ADD INDEX `subscriptions_id_user_id_subscription_plan_id_index`(
        `id`,
        `user_id`,
        `subscription_plan_id`
    );
CREATE TABLE `payments`(
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `user_id` BIGINT NOT NULL,
    `subscription_plan_id` BIGINT NOT NULL,
    `payment_method_id` BIGINT NOT NULL,
    `amount` DOUBLE NOT NULL DEFAULT '0',
    `transaction_id` BIGINT NULL,
    `status` ENUM(
        'pending_approval',
        'admin_approved',
        'admin_declined',
        'error'
    ) NOT NULL DEFAULT 'draft',
    `created_at` TIMESTAMP NOT NULL,
    `updated_at` TIMESTAMP NULL,
    `updated_admin_id` BIGINT NULL
);
ALTER TABLE
    `payments` ADD INDEX `payments_id_user_id_subscription_plan_id_payment_method_id_index`(
        `id`,
        `user_id`,
        `subscription_plan_id`,
        `payment_method_id`
    );
CREATE TABLE `reviews`(
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `user_id` BIGINT NOT NULL,
    `text` TEXT NOT NULL,
    `status` ENUM(
        'pending_approval',
        'admin_approved',
        'admin_declined'
    ) NOT NULL,
    `created_at` TIMESTAMP NOT NULL,
    `updated_at` TIMESTAMP NULL,
    `updated_admin_id` BIGINT NULL
);
CREATE TABLE `signals`(
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `admin_id` BIGINT NOT NULL,
    `instrument_id` BIGINT NOT NULL,
    `order_type` ENUM('buy', 'sell') NOT NULL,
    `target_position` DOUBLE NOT NULL,
    `stop_loss` JSON NOT NULL COMMENT '{\"132\",\"123\",\"N\"}',
    `take_profit` JSON NOT NULL COMMENT '{\"132\",\"123\",\"N\"}',
    `created_at` TIMESTAMP NOT NULL,
    `updated_at` TIMESTAMP NULL
);
ALTER TABLE
    `signals` ADD INDEX `signals_created_at_index`(`created_at`);
CREATE TABLE `instruments`(
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `title` VARCHAR(255) NOT NULL,
    `image_url` VARCHAR(255) NULL
);
CREATE TABLE `signal_reviews`(
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `user_id` BIGINT NOT NULL,
    `signal_id` BIGINT NOT NULL,
    `review` ENUM('like', 'dislike') NOT NULL,
    `created_at` TIMESTAMP NOT NULL
);
ALTER TABLE
    `signal_reviews` ADD INDEX `signal_reviews_signal_id_index`(`signal_id`);
ALTER TABLE
    `payments` ADD CONSTRAINT `payments_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`user_id`);
ALTER TABLE
    `reviews` ADD CONSTRAINT `reviews_updated_admin_id_foreign` FOREIGN KEY(`updated_admin_id`) REFERENCES `users`(`user_id`);
ALTER TABLE
    `payments` ADD CONSTRAINT `payments_subscription_plan_id_foreign` FOREIGN KEY(`subscription_plan_id`) REFERENCES `subscription_plans`(`id`);
ALTER TABLE
    `signal_reviews` ADD CONSTRAINT `signal_reviews_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`user_id`);
ALTER TABLE
    `reviews` ADD CONSTRAINT `reviews_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`user_id`);
ALTER TABLE
    `users` ADD CONSTRAINT `users_admin_role_id_foreign` FOREIGN KEY(`admin_role_id`) REFERENCES `admin_roles`(`id`);
ALTER TABLE
    `subscriptions` ADD CONSTRAINT `subscriptions_subscription_plan_id_foreign` FOREIGN KEY(`subscription_plan_id`) REFERENCES `subscription_plans`(`id`);
ALTER TABLE
    `subscriptions` ADD CONSTRAINT `subscriptions_created_admin_id_foreign` FOREIGN KEY(`created_admin_id`) REFERENCES `users`(`user_id`);
ALTER TABLE
    `signals` ADD CONSTRAINT `signals_instrument_id_foreign` FOREIGN KEY(`instrument_id`) REFERENCES `instruments`(`id`);
ALTER TABLE
    `subscriptions` ADD CONSTRAINT `subscriptions_user_id_foreign` FOREIGN KEY(`user_id`) REFERENCES `users`(`user_id`);
ALTER TABLE
    `signal_reviews` ADD CONSTRAINT `signal_reviews_signal_id_foreign` FOREIGN KEY(`signal_id`) REFERENCES `signals`(`id`);
ALTER TABLE
    `signals` ADD CONSTRAINT `signals_admin_id_foreign` FOREIGN KEY(`admin_id`) REFERENCES `users`(`user_id`);
ALTER TABLE
    `payments` ADD CONSTRAINT `payments_updated_admin_id_foreign` FOREIGN KEY(`updated_admin_id`) REFERENCES `users`(`user_id`);
ALTER TABLE
    `payments` ADD CONSTRAINT `payments_payment_method_id_foreign` FOREIGN KEY(`payment_method_id`) REFERENCES `payment_methods`(`id`);