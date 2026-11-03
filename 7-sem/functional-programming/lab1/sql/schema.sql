-- =====================================================================
-- Інформаційна система "Мережева газета факультету"
-- Запуск: mysql -u news -p --default-character-set=utf8mb4 newspaper < sql/schema.sql
-- =====================================================================

SET NAMES utf8mb4;

DROP TABLE IF EXISTS material_views;
DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS publication_files;
DROP TABLE IF EXISTS material_authors;
DROP TABLE IF EXISTS materials;
DROP TABLE IF EXISTS readers;
DROP TABLE IF EXISTS authors;
DROP TABLE IF EXISTS categories;

-- 1. Рубрики газети
CREATE TABLE categories (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE,
    description TEXT         NOT NULL
) ENGINE = InnoDB;

-- 2. Автори матеріалів: студенти, викладачі, співробітники
CREATE TABLE authors (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    email     VARCHAR(150) NOT NULL UNIQUE,
    status    VARCHAR(20)  NOT NULL,          -- student / teacher / staff
    unit      VARCHAR(100) NOT NULL,          -- академічна група або кафедра
    CONSTRAINT chk_author_status CHECK (status IN ('student', 'teacher', 'staff'))
) ENGINE = InnoDB;

-- 3. Матеріали газети: статті та графічні матеріали
CREATE TABLE materials (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    title        VARCHAR(255) NOT NULL,
    kind         VARCHAR(20)  NOT NULL,       -- article / graphic
    annotation   TEXT         NOT NULL,       -- текст анотації
    category_id  INT          NOT NULL,
    published_on DATE         NOT NULL,
    status       VARCHAR(20)  NOT NULL,       -- draft / published / archived
    CONSTRAINT chk_material_kind   CHECK (kind IN ('article', 'graphic')),
    CONSTRAINT chk_material_status CHECK (status IN ('draft', 'published', 'archived')),
    CONSTRAINT fk_material_category FOREIGN KEY (category_id)
        REFERENCES categories (id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE = InnoDB;

-- 4. Зв'язок "багато-до-багатьох": у матеріалу може бути кілька авторів,
--    а автор може мати багато матеріалів
CREATE TABLE material_authors (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    material_id INT         NOT NULL,
    author_id   INT         NOT NULL,
    role        VARCHAR(50) NOT NULL,         -- автор тексту, фотограф, ілюстратор ...
    CONSTRAINT uq_material_author UNIQUE (material_id, author_id),
    CONSTRAINT fk_ma_material FOREIGN KEY (material_id)
        REFERENCES materials (id) ON DELETE CASCADE,
    CONSTRAINT fk_ma_author FOREIGN KEY (author_id)
        REFERENCES authors (id) ON DELETE CASCADE
) ENGINE = InnoDB;

-- 5. Де записані файли публікації
CREATE TABLE publication_files (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    material_id INT          NOT NULL,
    file_path   VARCHAR(500) NOT NULL,        -- шлях або адреса в мережі
    file_format VARCHAR(20)  NOT NULL,        -- pdf, docx, jpg, png ...
    size_kb     INT          NOT NULL,
    uploaded_on DATE         NOT NULL,
    CONSTRAINT chk_file_size CHECK (size_kb >= 0),
    CONSTRAINT fk_file_material FOREIGN KEY (material_id)
        REFERENCES materials (id) ON DELETE CASCADE
) ENGINE = InnoDB;

-- 6. Читачі газети
CREATE TABLE readers (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    full_name      VARCHAR(150) NOT NULL,
    email          VARCHAR(150) NOT NULL UNIQUE,
    academic_group VARCHAR(50)  NOT NULL,     -- група / посада
    registered_on  DATE         NOT NULL
) ENGINE = InnoDB;

-- 7. Відгуки читачів про матеріали
CREATE TABLE reviews (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    material_id INT  NOT NULL,
    reader_id   INT  NOT NULL,
    rating      INT  NOT NULL,                -- оцінка 1..5
    comment     TEXT NOT NULL,
    created_on  DATE NOT NULL,
    CONSTRAINT chk_review_rating CHECK (rating BETWEEN 1 AND 5),
    CONSTRAINT fk_review_material FOREIGN KEY (material_id)
        REFERENCES materials (id) ON DELETE CASCADE,
    CONSTRAINT fk_review_reader FOREIGN KEY (reader_id)
        REFERENCES readers (id) ON DELETE CASCADE
) ENGINE = InnoDB;

-- 8. Перегляди матеріалів (джерело статистики).
--    reader_id може бути NULL: анонімний перегляд
CREATE TABLE material_views (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    material_id INT      NOT NULL,
    reader_id   INT      NULL,
    viewed_at   DATETIME NOT NULL,
    CONSTRAINT fk_view_material FOREIGN KEY (material_id)
        REFERENCES materials (id) ON DELETE CASCADE,
    CONSTRAINT fk_view_reader FOREIGN KEY (reader_id)
        REFERENCES readers (id) ON DELETE SET NULL
) ENGINE = InnoDB;