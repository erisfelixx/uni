# Travel Agency Web Application (lab2)

Full-stack SPA для управління туристичною агенцією. У другій лабораторній роботі архітектуру бекенду було повністю мігровано на сучасний фреймворк Spring Boot з використанням Spring Data JPA для роботи з базою даних та інтеграцією Keycloak для управління авторизацією. Фронтенд залишається на базі React.

---

## Основний функціонал

- **Каталог турів:** Перегляд доступних путівок із поділом на категорії (Відпочинок, Екскурсія, Шопінг).
- **Керування доступом на основі ролей (RBAC):**
  - **Клієнт (CUSTOMER):** Може переглядати тури, бронювати їх та бачити власну історію замовлень.
  - **Турагент (AGENT):** Має доступ до панелі керування для створення нових турів та визначення їх як "гарячих".
- **Система лояльності:** Автоматичний розрахунок та застосування знижки для постійних клієнтів.
- **Безпека та Ідентифікація:** Захист маршрутів та REST API за допомогою JWT-токенів через OAuth2 Resource Server (Keycloak).

---

## Технологічний стек

### Backend (Java)

| Категорія | Технологія |
|---|---|
| Мова | Java 21 |
| Фреймворк | Spring Boot 3.2 (Web, Data JPA, Security) |
| База даних | PostgreSQL, Spring Data JPA (Hibernate) |
| Міграції БД | Liquibase |
| Безпека | Spring Security, Keycloak (OAuth2, JWT) |
| Інструменти | Maven, Lombok, MapStruct (DTO Mapping) |
| Тестування | JUnit 5, Mockito |

### Frontend (React)

| Категорія | Технологія |
|---|---|
| Бібліотека | React 18 |
| Збірка | Vite |
| Маршрутизація | React Router DOM |
| HTTP-клієнт | Axios (з автоматичним додаванням токенів) |

---

## Структура проєкту

Проєкт використовує підхід Monorepo:

```text
/TravelAgency/src/main/java/ua/oop/...  — вихідний код Spring Boot бекенду
/TravelAgency/src/main/resources        — конфігурація application.yml та міграції Liquibase
/TravelAgency/src/test/java/ua/oop/...  — модульні тести (JUnit + Mockito)
/frontend                               — вихідний код React-додатка
```

---

## Інструкція із запуску
### 1. Налаштування бази даних (PostgreSQL)
1. Встановіть та запустіть PostgreSQL на порту 5432.
2. Створіть порожню базу даних postgres (або іншу, вказану в `application.yml`).
3. Структура таблиць створиться автоматично при запуску бекенду завдяки Liquibase. Ніяких SQL-скриптів вручну виконувати не потрібно.

### 2. Запуск сервера авторизації (Keycloak)
Для генерації та перевірки JWT-токенів використовується Keycloak. Запустіть його локально через Docker:

```Bash
docker run -p 8080:8080 -e KEYCLOAK_ADMIN=admin -e KEYCLOAK_ADMIN_PASSWORD=admin quay.io/keycloak/keycloak:24.0.4 start-dev
```
Потрібно буде зайти в панель адміністратора [http://localhost:8080](http://localhost:8080), створити realm travel-realm та клієнта travel-client.

### 3. Запуск Backend-сервера (Spring Boot)
1. Відкрийте папку TravelAgency у вашому IDE.
2. Завантажте залежності Maven.
3. Запустіть головний клас TravelAgencyApplication.java.
4. Сервер запуститься на порту 8081.

### 4. Запуск Frontend-клієнта
Перейдіть у папку фронтенду, встановіть залежності та запустіть сервер розробки:

```Bash
cd frontend
npm install
npm run dev
```
Відкрийте [http://localhost:5173](http://localhost:5173) у браузері.

---
## Тестування
Проєкт покритий модульними тестами для перевірки бізнес-логіки. Для їх запуску виконайте:

```Bash
cd TravelAgency
./mvnw test
```