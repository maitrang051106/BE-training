# MTT Library API

Django API cho bài thực hành backend: MongoDB, Redis cache, JWT, CRUD và clean architecture.

Project tham khảo:

- `TrainingAPI`: MongoDB/PyMongo, Redis cache-aside, CRUD books và JWT custom.
- `drf-course-api/Video29`: Django REST Framework, serializer, permission, cache và cách tách URL.

## Công nghệ

- Python 3.13+
- Django 5.1
- Django REST Framework: validation serializer
- PyMongo: persistence chính cho users và books
- MongoDB 6
- Redis tùy chọn; mặc định test local dùng `LocMemCache`
- PyJWT và bcrypt

## Kiến trúc

```text
MTT_Library/
├── MTT_Library/              # Django project settings và root URL
├── library_api/
│   ├── apis/                 # HTTP handlers, chỉ điều phối request/response
│   ├── cache/                # Cache adapter và cache keys
│   ├── constants/            # Tên collection MongoDB
│   ├── decorators/           # JWT và role authorization
│   ├── hooks/                # JSON error response
│   ├── models/               # Domain factory cho Book
│   ├── databases/            # MongoDB connection and data-access gateway
│   ├── security/             # Password hashing/checking
│   ├── serializers.py        # DRF input validation
│   ├── services/             # Business logic và cache invalidation
│   └── urls.py               # Library routes
├── templates/api.html
├── tests/test_api.py
├── library_db.py             # Seed 3 users và 5 books
├── api.http                  # REST Client requests
└── requirements.txt
```

Luồng xử lý chính:

```text
HTTP request
  -> URL
  -> API handler
  -> Serializer
  -> Service
  -> MongoDB gateway
```

API handler không chứa truy vấn MongoDB. Service xử lý nghiệp vụ và cache; MongoDB gateway chịu trách nhiệm truy cập dữ liệu.

## Cấu hình

Tạo `.env` từ `.env.example`:

```env
SECRET_KEY=change-me-in-production
JWT_EXPIRATION=3600
ALLOWED_HOSTS=localhost,127.0.0.1
MONGO_URI=mongodb://localhost:27017/
MONGO_DATABASE=training_django
REDIS_URL=redis://localhost:6379/0
```

Nếu `REDIS_URL` để trống, Django dùng `LocMemCache`. Đây là fallback cho local test, không phù hợp khi chạy nhiều worker production.

## Cài đặt và chạy

```bash
cd MTT_Library
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py check
python manage.py test tests
python manage.py runserver 127.0.0.1:8001
```

Mở `http://127.0.0.1:8001/` để xem trang API.

## Chạy MongoDB bằng Docker

Nếu máy chưa có MongoDB local:

```bash
docker run -d --name training-mongo -p 27017:27017 mongo:6.0
```

Kiểm tra container:

```bash
docker ps
```

Dừng container:

```bash
docker stop training-mongo
```

## Seed dữ liệu

`library_db.py` tạo dữ liệu idempotent: chạy lại không chèn trùng username hoặc book id. Book `id` là số nguyên tăng dần; counter được lưu trong collection `counters`.

```bash
python library_db.py
```

Tài khoản mẫu:

| Username | Password | Role |
|---|---|---|
| `admin` | `admin12345` | `admin` |
| `alice` | `password123` | `user` |
| `bob` | `password123` | `user` |

Không dùng Django ORM để lưu dữ liệu nghiệp vụ; các user/book này nằm trong MongoDB.

## JWT và phân quyền

`POST /login/` tạo access token và refresh token bằng PyJWT. Token chứa `username`, `role`, `typ`, `jti`, `kid` và thời hạn `exp`.

- Access token sống ngắn (`JWT_ACCESS_EXPIRATION`, mặc định 15 phút).
- Refresh token sống lâu hơn (`JWT_REFRESH_EXPIRATION`, mặc định 7 ngày).
- `/refresh/` rotate refresh token: refresh cũ bị blacklist.
- `/logout/` blacklist access token và refresh token.
- Blacklist lưu trong MongoDB `revoked_tokens`, có TTL index theo `expires_at`.
- Key rotation dùng `JWT_ACTIVE_KID` và `JWT_SECRET_KEYS`; giữ key cũ trong map trong thời gian chuyển đổi.

Gửi token trong header:

```text
Authorization: Bearer <token>
```

- User đăng nhập được tạo book.
- User chỉ update/delete book do chính mình sở hữu.
- Admin được quản lý user và thao tác trên mọi book.
- Endpoint đọc book là public.

`role = user.get('role', 'user')` lấy role đã lưu trong MongoDB khi login. Vì vậy user có `role: "admin"` đăng nhập bình thường và nhận token admin; role này được decorator dùng để bảo vệ `/admin/users/...`. Login không tự cấp quyền admin.

## API

### Authentication

| Method | Endpoint | Auth | Mục đích |
|---|---|---|---|
| `POST` | `/register/` | Không | Tạo user role `user` |
| `POST` | `/login/` | Không | Nhận access và refresh token |
| `POST` | `/refresh/` | Không | Rotate refresh token và cấp cặp token mới |
| `POST` | `/logout/` | Access JWT | Revoke access token |
| `GET` | `/admin/users/` | Admin | Danh sách user |
| `POST` | `/admin/users/create/` | Admin | Tạo user |
| `PUT` | `/admin/users/<username>/` | Admin | Đổi role/password |
| `DELETE` | `/admin/users/<username>/` | Admin | Xóa user |

### Books CRUD

| Method | Endpoint | Auth | Mục đích |
|---|---|---|---|
| `GET` | `/books/` | Không | Danh sách books, có cache |
| `POST` | `/books/create/` | JWT | Tạo book |
| `GET` | `/books/<id>/` | Không | Chi tiết book, có cache |
| `PUT` | `/books/<id>/` | JWT + owner/admin | Cập nhật book |
| `DELETE` | `/books/<id>/` | JWT + owner/admin | Xóa book |

Payload tạo/cập nhật book:

```json
{
  "title": "Clean Code",
  "authors": ["Robert C. Martin"],
  "publisher": "Prentice Hall",
  "description": "A practical guide to writing readable code."
}
```

## Cache

Cache dùng chiến lược cache-aside:

1. Đọc cache trước.
2. Cache miss thì đọc MongoDB.
3. Lưu kết quả vào cache với TTL 300 giây.
4. Create/update/delete xóa key liên quan.

Keys:

- `library:books:list`
- `library:book:<id>`

## Kiểm thử

```bash
python manage.py test tests -v 1
python manage.py check
```

Test hiện bao phủ:

- API home và list books.
- Register/login JWT.
- JWT bắt buộc khi create book.
- Owner update book.
- Service cache hit và cache invalidation.
- Serializer từ chối title rỗng.

Có thể dùng file `api.http` với VS Code REST Client để gọi tuần tự các endpoint.
