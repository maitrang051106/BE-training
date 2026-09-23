# So sánh Django và Sanic trong hai project Library API

Tài liệu này đối chiếu hai project trong `BE-training`:

- `Django_Library`: Library API dùng Django và Django REST Framework (DRF).
- `TrainingAPI`: Book Archive API dùng Sanic.

Hai project cùng giải quyết bài toán quản lý sách: CRUD, MongoDB, cache, JWT và phân quyền owner/admin. Khác biệt chính nằm ở cách framework tổ chức ứng dụng và mức độ thành phần được cung cấp sẵn.

## 1. Cấu trúc

### Django_Library

```text
Django_Library/
├── Django_Library/              # Project Django: settings, root URL, ASGI/WSGI
├── library_api/
│   ├── apis/                 # HTTP handler (view functions)
│   ├── cache/                # Cache adapter và cache key
│   ├── constants/            # Hằng số collection MongoDB
│   ├── databases/            # Kết nối và gateway MongoDB
│   ├── decorators/           # JWT và role authorization
│   ├── hooks/                # Chuẩn hóa JSON error response
│   ├── models/               # Domain factory: Book, User
│   ├── security/             # Hash/check password
│   ├── services/             # Business logic, cache invalidation
│   └── serializers.py        # DRF validation
├── templates/                # Giao diện HTML
├── tests/                    # Django test suite
├── manage.py                 # CLI chuẩn của Django
└── library_db.py             # Seed dữ liệu
```

Django có hai cấp tổ chức chuẩn: **project** (`MTT_Library`) và **app** (`library_api`). Project quản lý cấu hình chung; app chứa chức năng nghiệp vụ Library API. Logic được tách thành handler, serializer, service và database gateway.

### TrainingAPI (Sanic)

```text
TrainingAPI/
├── app/
│   ├── apis/                 # Blueprint và API handlers
│   ├── constants/            # MongoDB/cache constants
│   ├── databases/            # MongoDB và Redis client
│   ├── decorators/           # JWT và JSON Schema validation
│   ├── hooks/                # Startup/shutdown, middleware, error handler
│   ├── models/               # Book và JSON Schema
│   ├── utils/                # JWT, datetime, logger utilities
│   └── extensions.py         # App factory, routes, extensions
├── config.py                 # Server, Redis, MongoDB config
├── main.py                   # Entry point chạy server
├── docker-compose.yml        # App + MongoDB containers
└── testing.py                # Test script
```

Sanic không áp đặt mô hình project/app như Django. Project dùng **application factory** (`create_app`), **Blueprint** cho nhóm route và **hooks/listeners** cho lifecycle. Trong bản hiện tại, nhiều logic nghiệp vụ vẫn nằm trực tiếp trong `app/apis/books_blueprint.py`.

### Nhận xét

- Django phân tầng rõ hơn; phù hợp codebase lớn, nhiều người cùng phát triển và yêu cầu bảo trì dài hạn.
- Sanic gọn hơn và ít quy ước hơn; phù hợp API nhỏ hoặc cần chủ động thiết kế kiến trúc.
- Để Sanic dễ mở rộng, nên tách `books_blueprint.py` thành `services/` và `repositories/` tương tự Django.

## 2. Luồng hoạt động

### Django

```text
HTTP request
  → Django URLconf (MTT_Library/urls.py)
  → API handler (library_api/apis)
  → DRF Serializer validate dữ liệu
  → Service xử lý nghiệp vụ/cache
  → MongoDB gateway truy cập MongoDB
  → JsonResponse
```

Ví dụ tạo book:

1. Client gửi `POST /books/create/` với Bearer JWT.
2. `require_jwt` kiểm tra token, token type, key ID và blacklist.
3. `BookSerializer` kiểm tra title, publisher, authors.
4. `BookService.create_book` tạo và lưu book qua MongoDB gateway.
5. Service xóa các cache key liên quan.
6. API trả `JsonResponse` với HTTP 201.

### Sanic

```text
HTTP request
  → Sanic route / Blueprint
  → Decorator (JWT, JSON Schema)
  → Async API handler
  → MongoDB / Redis client
  → sanic.response.json
```

Ví dụ tạo book:

1. Client gửi `POST /books/` với Bearer JWT.
2. `@protected` decode JWT và thêm `username`, `role` vào handler.
3. `@validate_with_jsonschema` kiểm tra request body.
4. `create_book` tạo `Book`, gọi MongoDB để insert và Redis để invalid cache.
5. API trả `json(..., status=201)`.

Sanic chạy listener `before_server_start` để kết nối Redis và đặt client tại `request.app.ctx.cache`; listener `after_server_stop` đóng kết nối. Django cấu hình cache trong `settings.py` và truy cập qua lớp cache của Django.

> Lưu ý: Sanic handler là `async def`, nhưng PyMongo là synchronous. Các truy vấn MongoDB hiện có thể block event loop. Khi cần tải đồng thời cao, dùng Motor (async MongoDB driver) hoặc chạy truy vấn blocking trong executor.

## 3. Thư viện, framework

### Django_Library

- **Django 5.1**: framework full-stack; cung cấp settings, URL routing, middleware, template, test runner, management commands, ASGI/WSGI.
- **Django REST Framework 3.15**: `Serializer` để validation và chuẩn hóa dữ liệu API.
- **PyMongo 4.16**: truy cập MongoDB. Project không dùng Django ORM cho users/books.
- **django-redis / redis**: Redis cache; fallback sang `LocMemCache` khi không cấu hình `REDIS_URL`.
- **PyJWT**: tạo, decode và kiểm tra JWT.
- **bcrypt**: hash và verify password.

### TrainingAPI

- **Sanic 24.12**: async web framework/server, route decorator, Blueprint, middleware và lifecycle listener.
- **sanic-ext**: OpenAPI/Swagger, khai báo endpoint và Bearer security scheme.
- **Sanic-Cors**: cấu hình Cross-Origin Resource Sharing.
- **jsonschema**: validate JSON request body qua decorator tự viết.
- **PyMongo 4.16**: persistence MongoDB.
- **redis 7.1**: cache và lưu JWT bị revoke theo TTL.
- **PyJWT, bcrypt, python-dotenv**: JWT, password hashing và nạp biến môi trường.

### Khác biệt framework

Django là framework “batteries included”: nhiều thành phần tích hợp sẵn và có convention chặt chẽ. Sanic là framework async nhỏ hơn: server và routing mạnh, nhưng validation, tổ chức service, cache policy hay security policy chủ yếu do project tự chọn và ghép thư viện.

## 4. Bảo mật

### Điểm chung

- Password được hash bằng `bcrypt`, không lưu password dạng plaintext.
- Xác thực dùng JWT bearer token qua header `Authorization: Bearer <token>`.
- Access token và refresh token có thời hạn riêng.
- Update/delete book chỉ dành cho owner hoặc admin.
- Refresh token được rotate và token cũ bị revoke.

### Django_Library

- Dùng `SecurityMiddleware`, `AuthenticationMiddleware`, `XFrameOptionsMiddleware`, CSRF middleware và password validators do Django cung cấp.
- JWT chứa `kid`; server dùng `JWT_ACTIVE_KID` và `JWT_SECRET_KEYS`, hỗ trợ thay đổi signing key có kiểm soát.
- Token revoke được lưu trong MongoDB collection `revoked_tokens`, với TTL index theo `expires_at`.
- Cache dùng Redis nếu có; nếu thiếu Redis, fallback `LocMemCache` chỉ phù hợp local hoặc một worker.
- Endpoint API được `csrf_exempt` vì dùng Bearer header. Điều này phù hợp với token không tự gửi bởi browser; nếu chuyển JWT sang cookie thì phải bật CSRF protection lại.
- `DEBUG = True` hiện chỉ nên dùng khi development; production phải đặt `DEBUG=False`, cấu hình `ALLOWED_HOSTS` chính xác và dùng `SECRET_KEY` từ environment.

### TrainingAPI

- `@protected` chỉ cho phép `typ = access` và kiểm tra JWT `jti` đã bị revoke trong Redis hay chưa.
- Redis lưu revoked token với TTL còn lại của token.
- `create_admin()` bắt buộc `ADMIN_USERNAME` và `ADMIN_PASSWORD` từ environment, không hard-code admin account.
- CORS đang đặt `CORS_ORIGINS = "*"`; production nên giới hạn chính xác domain frontend.
- `SECRET_KEY`, MongoDB URI, Redis password và admin credential phải chỉ nằm trong `.env` hoặc secret manager; không commit vào Git.

## 5. API, syntax

### Routing

Django khai báo route tập trung bằng `path`:

```python
urlpatterns = [
    path('books/', books_api.list_books),
    path('books/create/', books_api.create_book),
    path('books/<int:id>/', books_api.get_book),
]
```

Sanic dùng Blueprint và decorator:

```python
books_bp = Blueprint('books_blueprint', url_prefix='/books')

@books_bp.get('/')
async def get_all_books(request):
    return json({'status': 'success'})

@books_bp.post('/')
@protected
async def create_book(request, username=None, role='user'):
    return json({'status': 'success'}, status=201)
```

### Handler và response

Django dùng function view đồng bộ và `JsonResponse`:

```python
@require_jwt
@require_http_methods(['POST'])
def create_book(request):
    serializer = BookSerializer(data=_payload(request))
    if not serializer.is_valid():
        return JsonResponse({'errors': serializer.errors}, status=400)
```

Sanic dùng async function và `sanic.response.json`:

```python
@books_bp.put('/<id>')
@protected
@validate_with_jsonschema(jsonschema=create_book_json_schema)
async def update_book(request, id, username, role='user'):
    return json({'status': 'success', 'book': book}, status=200)
```

### Validation

- Django: DRF `BookSerializer` quy định kiểu dữ liệu, độ dài, danh sách authors và custom validation như `validate_title`.
- Sanic: JSON Schema (`create_book_json_schema`) và decorator `@validate_with_jsonschema`.

### API hiện có

Cả hai cùng có nhóm API:

- `POST /register/`, `POST /login/`, refresh/logout JWT.
- `GET` danh sách và chi tiết books là public.
- `POST` tạo book cần JWT.
- `PUT` và `DELETE` book cần JWT và kiểm tra owner/admin.
- Django có thêm nhóm quản trị user qua `/admin/users/...`.

Khác biệt naming: Django dùng `/books/create/` cho tạo mới, còn Sanic tuân REST convention hơn với `POST /books/`. Với API mới, nên thống nhất convention: `POST /books/`, `GET /books/<id>/`, `PUT/PATCH /books/<id>/`, `DELETE /books/<id>/`.

## Kết luận

Chọn Django/DRF khi cần hệ sinh thái đầy đủ, convention rõ, khả năng mở rộng nghiệp vụ và bảo mật mặc định tốt. Chọn Sanic khi API cần async, lightweight, WebSocket/streaming hoặc cần tự kiểm soát stack. Trong hai project này, Django có sự tách lớp tốt hơn; Sanic có entry point và lifecycle async rõ hơn nhưng cần tách service/repository, đồng thời thay hoặc bao bọc PyMongo đồng bộ nếu muốn đạt lợi ích async thực sự.
