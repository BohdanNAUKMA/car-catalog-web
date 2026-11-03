# AutoHub — Каталог та сервіс бронювання автомобілів

## 1. Опис бізнес-логіки проєкту

**AutoHub** — це веб-платформа для перегляду, підбору та оформлення замовлення на купівлю авто. Сервіс дозволяє користувачам зручно обирати транспортні засоби за потрібними характеристиками, а адміністраторам — управляти асортиментом автосалону.

### Функціонал для звичайного відвідувача (гостя):
- Перегляд каталогу наявних автомобілів із пошуком за назвою моделі.
- Фільтрація списку за брендом, типом кузова (седан, кросовер тощо) та типом палива.
- Сортування машин за зростанням/спаданням ціни, роком випуску та пробігом.
- Окрема сторінка кожного авто з детальними технічними характеристиками, описом та фото.
- Сторінка каталогу брендів та окрема сторінка бренду з усіма його наявними авто.
- Інформаційні сторінки: «Про компанію», гарантійні зобов'язання, умови оформлення та доставки.

### Функціонал для авторизованого користувача:
- Реєстрація нового облікового запису та вхід у систему.
- Перегляд та редагування контактних даних у власному профілі.
- Додавання обраних авто до кошика.
- Швидке оформлення замовлення на авто в один клік (без необхідності онлайн-оплати).
- Перегляд історії власних замовлень та їхнього поточного статусу.

### Функціонал адміністратора (менеджера):
- Додавання нових марок (брендів) авто до каталогу.
- Редагування та видалення наявних брендів.
- Додавання нових моделей автомобілів з усіма характеристиками.
- Редагування цін, пробігу та описів наявних авто.
- Видалення проданих або неактуальних позицій.
- Перегляд усіх замовлень клієнтів та зміна їхнього статусу.

---

## 2. Схема бази даних (ERD)

![Схема бази даних](docs/db-schema.png)

---

## 3. Архітектура REST API

Всі запити та відповіді передаються у форматі `JSON`. Базовий префікс для всіх маршрутів: `/api/v1`.

### 3.1. Автентифікація та Користувачі

#### Реєстрація нового користувача
- **Використання:** створення нового облікового запису покупця.
- **Метод:** `POST /api/v1/auth/register`
- **Request Body:**
  ```json
  {
    "fullName": "Іван Коваленко",
    "email": "ivan@example.com",
    "password": "strongPassword123",
    "phone": "+380671234567"
  }
  ```
- **Response Status:** `201 Created`
- **Response Body:**
  ```json
  {
    "id": 1,
    "fullName": "Іван Коваленко",
    "email": "ivan@example.com",
    "role": "client"
  }
  ```

#### Вхід у систему (Логін)
- **Використання:** авторизація та отримання токена доступу.
- **Метод:** `POST /api/v1/auth/login`
- **Request Body:**
  ```json
  {
    "email": "ivan@example.com",
    "password": "strongPassword123"
  }
  ```
- **Response Status:** `200 OK`
- **Response Body:**
  ```json
  {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 1,
      "fullName": "Іван Коваленко",
      "email": "ivan@example.com",
      "role": "client"
    }
  }
  ```

#### Отримання профілю поточного користувача
- **Використання:** завантаження особистих даних у кабінеті користувача.
- **Метод:** `GET /api/v1/users/me`
- **Headers:** `Authorization: Bearer <token>`
- **Response Status:** `200 OK`
- **Response Body:**
  ```json
  {
    "id": 1,
    "fullName": "Іван Коваленко",
    "email": "ivan@example.com",
    "phone": "+380671234567",
    "role": "client"
  }
  ```

#### Оновлення даних профілю
- **Використання:** зміна імені чи контактного номера телефону.
- **Метод:** `PATCH /api/v1/users/me`
- **Headers:** `Authorization: Bearer <token>`
- **Request Body:**
  ```json
  {
    "fullName": "Іван Петренко",
    "phone": "+380509876543"
  }
  ```
- **Response Status:** `200 OK`
- **Response Body:**
  ```json
  {
    "id": 1,
    "fullName": "Іван Петренко",
    "email": "ivan@example.com",
    "phone": "+380509876543"
  }
  ```

---

### 3.2. Автомобілі (Каталог)

#### Отримання списку авто (з пошуком, фільтрацією та сортуванням)
- **Використання:** відображення списку машин на головній сторінці або в каталозі.
- **Метод:** `GET /api/v1/cars`
- **Query Parameters:**
  - `search` (рядок): пошук за назвою моделі (наприклад, `camry`)
  - `brandId` (число): фільтр за брендом (наприклад, `1`)
  - `bodyType` (рядок): фільтр за типом кузова (`sedan`, `suv`, `hatchback`)
  - `fuelType` (рядок): фільтр за типом палива (`petrol`, `diesel`, `electric`, `hybrid`)
  - `sort` (рядок): критерій сортування (`price_asc`, `price_desc`, `year_desc`, `mileage_asc`)
  - `page` (число, за замовчуванням `1`): номер сторінки
  - `limit` (число, за замовчуванням `12`): кількість елементів на сторінці
- **Response Status:** `200 OK`
- **Response Body:**
  ```json
  {
    "data": [
      {
        "id": 10,
        "brand": "Toyota",
        "model": "Camry",
        "year": 2021,
        "price": 24500,
        "bodyType": "sedan",
        "fuelType": "petrol",
        "mileage": 45000,
        "imageUrl": "[https://example.com/cars/camry2021.jpg](https://example.com/cars/camry2021.jpg)"
      }
    ],
    "pagination": {
      "totalItems": 1,
      "currentPage": 1,
      "totalPages": 1
    }
  }
  ```

#### Отримання детальної інформації про конкретне авто
- **Використання:** відображення картки автомобіля з усіма технічними даними.
- **Метод:** `GET /api/v1/cars/{id}`
- **Response Status:** `200 OK`
- **Response Body:**
  ```json
  {
    "id": 10,
    "brand": {
      "id": 1,
      "name": "Toyota"
    },
    "model": "Camry",
    "year": 2021,
    "price": 24500,
    "bodyType": "sedan",
    "fuelType": "petrol",
    "transmission": "automatic",
    "mileage": 45000,
    "description": "Офіційний автомобіль в ідеальному технічному стані, один власник, повна сервісна книга.",
    "imageUrl": "[https://example.com/cars/camry2021.jpg](https://example.com/cars/camry2021.jpg)"
  }
  ```

#### Додавання нового авто (Адміністратор)
- **Використання:** внесення нового автомобіля в асортимент.
- **Метод:** `POST /api/v1/cars`
- **Headers:** `Authorization: Bearer <token>`
- **Request Body:**
  ```json
  {
    "brandId": 1,
    "model": "RAV4",
    "year": 2022,
    "price": 31000,
    "bodyType": "suv",
    "fuelType": "hybrid",
    "transmission": "automatic",
    "mileage": 28000,
    "description": "Повний привід, стан нового автомобіля, максимальна комплектація.",
    "imageUrl": "[https://example.com/cars/rav4.jpg](https://example.com/cars/rav4.jpg)"
  }
  ```
- **Response Status:** `201 Created`
- **Response Body:**
  ```json
  {
    "id": 11,
    "brandId": 1,
    "model": "RAV4",
    "price": 31000,
    "status": "available"
  }
  ```

#### Оновлення даних про автомобіль (Адміністратор)
- **Використання:** зміна ціни, оновлення пробігу або опису.
- **Метод:** `PUT /api/v1/cars/{id}`
- **Headers:** `Authorization: Bearer <token>`
- **Request Body:**
  ```json
  {
    "price": 29900,
    "mileage": 29000,
    "description": "Ціну знижено! Повний комплект зимової гуми у подарунок."
  }
  ```
- **Response Status:** `200 OK`
- **Response Body:**
  ```json
  {
    "id": 11,
    "price": 29900,
    "mileage": 29000,
    "description": "Ціну знижено! Повний комплект зимової гуми у подарунок."
  }
  ```

#### Видалення авто з каталогу (Адміністратор)
- **Використання:** зняття авто з продажу чи видалення помилкового запису.
- **Метод:** `DELETE /api/v1/cars/{id}`
- **Headers:** `Authorization: Bearer <token>`
- **Response Status:** `204 No Content`

---

### 3.3. Бренди (Виробники)

#### Отримання списку всіх брендів
- **Використання:** виведення списку виробників у фільтрах та в розділі брендів.
- **Метод:** `GET /api/v1/brands`
- **Response Status:** `200 OK`
- **Response Body:**
  ```json
  [
    {
      "id": 1,
      "name": "Toyota",
      "country": "Японія",
      "carsCount": 14
    },
    {
      "id": 2,
      "name": "BMW",
      "country": "Німеччина",
      "carsCount": 8
    }
  ]
  ```

#### Отримання всіх авто обраного бренду
- **Використання:** відкриття сторінки конкретної марки з усіма наявними моделями.
- **Метод:** `GET /api/v1/brands/{id}/cars`
- **Response Status:** `200 OK`
- **Response Body:**
  ```json
  [
    {
      "id": 10,
      "model": "Camry",
      "year": 2021,
      "price": 24500,
      "bodyType": "sedan",
      "imageUrl": "[https://example.com/cars/camry2021.jpg](https://example.com/cars/camry2021.jpg)"
    },
    {
      "id": 11,
      "model": "RAV4",
      "year": 2022,
      "price": 31000,
      "bodyType": "suv",
      "imageUrl": "[https://example.com/cars/rav4.jpg](https://example.com/cars/rav4.jpg)"
    }
  ]
  ```

#### Додавання нового бренду (Адміністратор)
- **Використання:** реєстрація нової марки в каталозі.
- **Метод:** `POST /api/v1/brands`
- **Headers:** `Authorization: Bearer <token>`
- **Request Body:**
  ```json
  {
    "name": "Audi",
    "country": "Німеччина",
    "description": "Німецький преміум-виробник автомобілів."
  }
  ```
- **Response Status:** `201 Created`
- **Response Body:**
  ```json
  {
    "id": 3,
    "name": "Audi",
    "country": "Німеччина",
    "description": "Німецький преміум-виробник автомобілів."
  }
  ```

#### Оновлення бренду (Адміністратор)
- **Використання:** редагування назви або опису бренду.
- **Метод:** `PATCH /api/v1/brands/{id}`
- **Headers:** `Authorization: Bearer <token>`
- **Request Body:**
  ```json
  {
    "description": "Оновлений опис бренду та історія компанії."
  }
  ```
- **Response Status:** `200 OK`
- **Response Body:**
  ```json
  {
    "id": 3,
    "name": "Audi",
    "country": "Німеччина",
    "description": "Оновлений опис бренду та історія компанії."
  }
  ```

#### Видалення бренду (Адміністратор)
- **Використання:** видалення марки авто з каталогу.
- **Метод:** `DELETE /api/v1/brands/{id}`
- **Headers:** `Authorization: Bearer <token>`
- **Response Status:** `204 No Content`

---

### 3.4. Кошик та Замовлення

#### Створення замовлення (Бронювання/Купівля)
- **Використання:** оформлення заявки на купівлю вибраних у кошику автомобілів.
- **Метод:** `POST /api/v1/orders`
- **Headers:** `Authorization: Bearer <token>`
- **Request Body:**
  ```json
  {
    "carIds": [10]
  }
  ```
- **Response Status:** `201 Created`
- **Response Body:**
  ```json
  {
    "orderId": 105,
    "userId": 1,
    "totalPrice": 24500,
    "status": "pending",
    "createdAt": "2026-11-03T12:00:00Z"
  }
  ```

#### Перегляд історії замовлень користувача
- **Використання:** перегляд оформлених замовлень в особистому кабінеті клієнта.
- **Метод:** `GET /api/v1/orders/my`
- **Headers:** `Authorization: Bearer <token>`
- **Response Status:** `200 OK`
- **Response Body:**
  ```json
  [
    {
      "orderId": 105,
      "status": "pending",
      "totalPrice": 24500,
      "createdAt": "2026-11-03T12:00:00Z",
      "items": [
        {
          "carId": 10,
          "brand": "Toyota",
          "model": "Camry",
          "price": 24500
        }
      ]
    }
  ]
  ```

#### Перегляд усіх замовлень (Адміністратор)
- **Використання:** отримання переліку замовлень усіх клієнтів для подальшої обробки менеджером.
- **Метод:** `GET /api/v1/orders`
- **Headers:** `Authorization: Bearer <token>`
- **Response Status:** `200 OK`
- **Response Body:**
  ```json
  [
    {
      "orderId": 105,
      "userId": 1,
      "customerName": "Іван Коваленко",
      "customerPhone": "+380671234567",
      "status": "pending",
      "totalPrice": 24500,
      "createdAt": "2026-10-03T12:00:00Z"
    }
  ]
  ```

#### Зміна статусу замовлення (Адміністратор)
- **Використання:** переведення замовлення в статус "confirmed", "completed" або "cancelled".
- **Метод:** `PATCH /api/v1/orders/{id}/status`
- **Headers:** `Authorization: Bearer <token>`
- **Request Body:**
  ```json
  {
    "status": "confirmed"
  }
  ```
- **Response Status:** `200 OK`
- **Response Body:**
  ```json
  {
    "orderId": 105,
    "status": "confirmed",
    "updatedAt": "2026-10-03T12:30:00Z"
  }
  ```

---

### 3.5. Загальна інформація про компанію

#### Отримання контакту та інформації про сервіс
- **Використання:** відображення сторінки «Про нас», гарантійних правил та умов доставки.
- **Метод:** `GET /api/v1/info`
- **Response Status:** `200 OK`
- **Response Body:**
  ```json
  {
    "companyName": "AutoHub Ukraine",
    "address": "м. Київ, вул. Велика Васильківська, 100",
    "phone": "+380441234567",
    "email": "info@autohub.ua",
    "warrantyPolicy": "12 місяців гарантії або 20 000 км пробігу на кожен перевірений автомобіль.",
    "deliveryInfo": "Доставка власним автовозом у будь-яке місто України протягом 3-х робочих днів."
  }
  ```