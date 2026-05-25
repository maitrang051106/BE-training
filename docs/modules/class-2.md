# 🚀 Backend Training — Class 2
### Chủ đề: Docker · Git nâng cao · SQL nâng cao · Testing · Logging · Config & Env
---

# MỤC LỤC

1. [Docker](#1-docker)
2. [Git nâng cao](#2-git-nâng-cao)
3. [SQL nâng cao](#3-sql-nâng-cao)
4. [Testing](#4-testing)
5. [Logging & Observability](#5-logging--observability)
6. [Config & Environment](#6-config--environment)

---

# 1. Docker

## 1.1 Docker là gì?

**Analogy:**
> Docker giống như hộp cơm bento — bên trong đã có đủ cơm, thức ăn, nước chấm. Dù bạn ăn ở nhà hay ở công ty, hộp cơm đó luôn có vị như nhau. Không còn chuyện "máy tôi chạy được, máy bạn không chạy."

**Vấn đề Docker giải quyết:**
```
Không có Docker:
  Dev: "App chạy ngon trên máy tôi!"
  Server: App crash vì Python 3.8 thay vì 3.11, thiếu libpq-dev, ...

Có Docker:
  Mọi người chạy cùng 1 image → cùng OS, cùng dependencies, cùng config
```

**Các khái niệm cốt lõi:**

| Khái niệm | Giải thích | Analogy |
|-----------|-----------|---------|
| **Image** | Blueprint, template bất biến | Công thức nấu ăn |
| **Container** | Instance đang chạy từ image | Tô phở được nấu ra từ công thức |
| **Dockerfile** | Script để build image | Bản hướng dẫn viết công thức |
| **Registry** | Kho lưu image (Docker Hub, ECR) | Siêu thị bán nguyên liệu |
| **Volume** | Lưu data bền vững ngoài container | USB cắm vào container |
| **Network** | Container giao tiếp với nhau | Mạng LAN nội bộ |

---

## 1.2 Dockerfile thực tế

```dockerfile
# Base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy và install dependencies TRƯỚC (tận dụng layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code SAU
COPY . .

# Không chạy với root — security best practice
RUN adduser --disabled-password appuser
USER appuser

# Expose port (chỉ mang tính document, không tự mở port)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=5s \
  CMD curl -f http://localhost:8080/health || exit 1

# Lệnh chạy app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

**Tại sao copy requirements trước source code?**
```
Docker build theo từng layer. Nếu code thay đổi nhưng requirements không đổi
→ Layer cài pip được cache lại → Build nhanh hơn nhiều

Layer 1: FROM python          [cache]
Layer 2: COPY requirements    [cache nếu requirements.txt không đổi]
Layer 3: RUN pip install      [cache nếu requirements.txt không đổi]
Layer 4: COPY . .             [rebuild khi code thay đổi]
```

---

## 1.3 Docker Compose

Chạy nhiều service cùng lúc:

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/mydb
      - REDIS_URL=redis://redis:6379
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    volumes:
      - ./:/app          # Mount code để hot reload (dev only)

  db:
    image: postgres:15
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: mydb
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru

volumes:
  postgres_data:
```

**Lệnh hay dùng:**
```bash
docker compose up -d          # Chạy ngầm
docker compose logs -f api    # Xem log realtime
docker compose exec api bash  # Vào trong container
docker compose down -v        # Tắt và xoá volume
docker compose build --no-cache  # Build lại từ đầu
```

---

## 1.4 Khi nào dùng Docker, khi nào không?

**✅ Dùng Docker khi:**
- Cần environment nhất quán giữa dev/staging/prod
- Microservice với nhiều service khác nhau
- CI/CD pipeline
- Cần isolate dependencies giữa các project

**❌ Không cần Docker khi:**
- Script nhỏ, chạy 1 lần
- Môi trường đã chuẩn hoá hoàn toàn (managed cloud functions)
- Team chưa quen, deadline gấp — có thể thêm complexity không cần thiết

---

## 1.5 Best Practice Docker

```dockerfile
# ✅ Multi-stage build — image production nhỏ hơn nhiều
FROM python:3.11 AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim AS production
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
USER nobody
CMD ["python", "main.py"]

# ✅ .dockerignore — không copy rác vào image
# File .dockerignore:
# __pycache__/
# .git/
# .env
# *.pyc
# venv/
# tests/
```

---

# 2. Git nâng cao

## 2.1 Tại sao cần Git workflow?

Làm một mình: commit lung tung không sao.
Làm team 5 người: không có workflow → conflict, mất code, không biết ai làm gì.

---

## 2.2 Branch Strategy

**Git Flow (phổ biến với release cycle rõ ràng):**
```
main          ──●──────────────────────────────●──  (production)
                │                              │
hotfix        ──┤── fix-login-bug ─────────────┤──
                │                              │
develop       ──●──────────────────────────────●──
                │
feature/      ──┤── feature/payment ─────────────┤
                └── feature/auth ──────────────┘
```

**Trunk-based (phổ biến với CI/CD nhanh):**
```
main    ──●──●──●──●──●──  (commit thường xuyên, deploy thường xuyên)
           │
feature ───┤ (branch sống ngắn, merge vào main trong 1-2 ngày)
```

---

## 2.3 Các lệnh Git hay bị bỏ qua

**Rebase — viết lại lịch sử sạch hơn:**
```bash
# Tình huống: branch của bạn bị lag so với main
git checkout feature/payment
git rebase main          # Rebase lên main thay vì merge

# Interactive rebase — gom commit lại trước khi PR
git rebase -i HEAD~3     # Gom 3 commit gần nhất
# squash = gộp vào commit trước
# reword = đổi tên commit
# drop = xoá commit
```

**Cherry-pick — lấy 1 commit cụ thể:**
```bash
# Chỉ muốn lấy 1 fix từ branch khác mà không merge cả branch
git cherry-pick abc1234
```

**Stash — lưu tạm thay đổi:**
```bash
git stash push -m "work in progress: payment form"
git stash list
git stash pop            # Lấy lại stash mới nhất
git stash apply stash@{2}  # Lấy stash cụ thể
```

**Reflog — cứu code đã mất:**
```bash
git reflog               # Xem toàn bộ lịch sử, kể cả đã bị xoá
git reset --hard HEAD@{3}  # Quay lại trạng thái 3 action trước
```

---

## 2.4 Commit Message Convention

**Conventional Commits (chuẩn được dùng rộng rãi):**
```
<type>(<scope>): <description>

feat(auth): add refresh token rotation
fix(payment): handle timeout when charging card
docs(api): update authentication docs
refactor(user): extract email validation to utils
test(order): add integration test for checkout flow
chore(deps): bump fastapi from 0.100 to 0.104
```

**Tại sao cần chuẩn này?**
- Tự động generate CHANGELOG
- Trigger CI/CD theo loại commit
- Code review dễ hơn vì biết scope ảnh hưởng

---

## 2.5 Pull Request Best Practice

```
PR tốt:
  ✅ Tiêu đề rõ ràng: "feat(auth): add refresh token rotation"
  ✅ Description: Tại sao thay đổi? Cách test? Screenshot nếu có UI
  ✅ < 400 lines changed — reviewer không muốn review 2000 dòng
  ✅ Tự review trước khi request review
  ✅ Link ticket/issue liên quan

PR tệ:
  ❌ "fix bug"
  ❌ 3000 lines, 20 files
  ❌ Không có mô tả
  ❌ Mix nhiều feature vào 1 PR
```

---

# 3. SQL nâng cao

## 3.1 Tại sao SQL vẫn quan trọng dù dùng ORM?

ORM tạo ra query tự động — nhưng đôi khi query đó rất tệ. Hiểu SQL giúp bạn:
- Phát hiện N+1 query
- Tối ưu slow query
- Đọc được `EXPLAIN ANALYZE` output
- Viết query phức tạp ORM không làm được

---

## 3.2 JOIN — hiểu thật sự

```sql
-- INNER JOIN: chỉ lấy row có match ở CẢ HAI bảng
SELECT u.name, o.total
FROM users u
INNER JOIN orders o ON u.id = o.user_id;
-- User không có order → không xuất hiện

-- LEFT JOIN: lấy tất cả user, kể cả không có order
SELECT u.name, COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id, u.name;
-- User không có order → order_count = 0

-- Tình huống thực tế: lấy user có order trong 30 ngày qua
SELECT DISTINCT u.*
FROM users u
INNER JOIN orders o ON u.id = o.user_id
WHERE o.created_at >= NOW() - INTERVAL '30 days'
  AND o.status = 'completed';
```

---

## 3.3 Index — tại sao query chậm

```sql
-- Không có index: Full Table Scan
-- Postgres phải đọc 10 triệu rows để tìm 1 email
SELECT * FROM users WHERE email = 'a@example.com';

-- Tạo index
CREATE INDEX idx_users_email ON users(email);
-- Bây giờ: B-Tree lookup, O(log n)

-- Compound index — thứ tự CỰC KỲ QUAN TRỌNG
CREATE INDEX idx_orders_user_status ON orders(user_id, status);
-- Query này DÙNG được index:
SELECT * FROM orders WHERE user_id = 123 AND status = 'pending';
-- Query này KHÔNG dùng được index:
SELECT * FROM orders WHERE status = 'pending';  -- Thiếu user_id (cột đầu)

-- Partial index — index chỉ subset của data
CREATE INDEX idx_orders_pending ON orders(created_at)
WHERE status = 'pending';
-- Nhỏ hơn nhiều, nhanh hơn cho query cụ thể này
```

---

## 3.4 EXPLAIN ANALYZE — đọc query plan

```sql
EXPLAIN ANALYZE
SELECT u.name, COUNT(o.id)
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.created_at >= '2024-01-01'
GROUP BY u.id;

-- Output:
-- HashAggregate  (cost=1250.00..1300.00 rows=500)
--   ->  Hash Left Join  (cost=450.00..1100.00)
--         Hash Cond: (o.user_id = u.id)
--         ->  Seq Scan on orders    ← ĐÂY LÀ VẤN ĐỀ! Seq Scan = không có index
--         ->  Index Scan on users   ← Tốt, có index

-- Seq Scan = đọc toàn bộ bảng → cần index
-- Index Scan = dùng index → tốt
-- Nested Loop với rows lớn → có thể cần index khác
```

---

## 3.5 Transaction và ACID

```sql
-- Transaction đảm bảo hoặc tất cả thành công hoặc tất cả thất bại
BEGIN;

UPDATE accounts SET balance = balance - 500000 WHERE id = 1;
UPDATE accounts SET balance = balance + 500000 WHERE id = 2;

-- Kiểm tra sau khi update
DO $$
BEGIN
  IF (SELECT balance FROM accounts WHERE id = 1) < 0 THEN
    RAISE EXCEPTION 'Insufficient balance';
  END IF;
END $$;

COMMIT;  -- Hoặc ROLLBACK nếu có lỗi

-- Với Python psycopg2:
-- with conn.transaction():  -- Tự động ROLLBACK nếu exception
--     cur.execute(...)
```

**Isolation Levels:**
| Level | Dirty Read | Non-repeatable Read | Phantom Read |
|-------|-----------|---------------------|--------------|
| READ UNCOMMITTED | Có | Có | Có |
| READ COMMITTED (default PG) | Không | Có | Có |
| REPEATABLE READ | Không | Không | Có |
| SERIALIZABLE | Không | Không | Không |

---

## 3.6 N+1 Query — vấn đề phổ biến nhất

```python
# ❌ N+1: 1 query lấy orders + N query lấy user
orders = db.query(Order).all()           # 1 query
for order in orders:
    print(order.user.name)               # N query! 1 query mỗi order

# ✅ Eager loading: 2 query tổng
orders = db.query(Order).options(
    joinedload(Order.user)               # JOIN users trong 1 query
).all()

# ✅ Hoặc raw SQL với JOIN
SELECT o.*, u.name FROM orders o
JOIN users u ON o.user_id = u.id;
```

---

# 4. Testing

## 4.1 Tại sao cần viết test?

```
Không có test:
  "Tôi fix bug A" → Bug B xuất hiện → "Tôi fix bug B" → Bug A quay lại
  → Vòng lặp vô tận, không dám refactor

Có test:
  Fix bug A → Chạy test → Test báo bug B xuất hiện ngay lập tức
  → Sửa cả 2 → Tự tin refactor vì test sẽ bắt regression
```

---

## 4.2 Testing Pyramid

```
         /\
        /e2e\          ← Ít, chậm, đắt (Playwright, Cypress)
       /------\
      /integrat\       ← Vừa (test DB, API endpoint thật)
     /----------\
    /  unit test  \    ← Nhiều, nhanh, rẻ (test function đơn lẻ)
   /--------------\
```

**Rule of thumb:** 70% unit, 20% integration, 10% e2e.

---

## 4.3 Unit Test với pytest

```python
# services/order_service.py
def calculate_total(items: list[dict], discount_percent: float = 0) -> float:
    subtotal = sum(item["price"] * item["quantity"] for item in items)
    discount = subtotal * (discount_percent / 100)
    return round(subtotal - discount, 2)

# tests/test_order_service.py
import pytest
from services.order_service import calculate_total

def test_calculate_total_no_discount():
    items = [{"price": 100000, "quantity": 2}]
    assert calculate_total(items) == 200000

def test_calculate_total_with_discount():
    items = [{"price": 100000, "quantity": 2}]
    assert calculate_total(items, discount_percent=10) == 180000

def test_calculate_total_empty_cart():
    assert calculate_total([]) == 0

def test_calculate_total_multiple_items():
    items = [
        {"price": 50000, "quantity": 3},
        {"price": 20000, "quantity": 1},
    ]
    assert calculate_total(items) == 170000

# Parametrize — test nhiều case trong 1 test
@pytest.mark.parametrize("discount,expected", [
    (0,   200000),
    (10,  180000),
    (50,  100000),
    (100, 0),
])
def test_discounts(discount, expected):
    items = [{"price": 100000, "quantity": 2}]
    assert calculate_total(items, discount_percent=discount) == expected
```

---

## 4.4 Mock — giả lập dependency

```python
# Khi function gọi external service (DB, API), dùng mock để isolate
from unittest.mock import patch, MagicMock

def test_send_welcome_email():
    with patch("services.email.send_email") as mock_send:
        mock_send.return_value = {"status": "sent"}

        result = register_user({"email": "test@example.com", "name": "Alice"})

        # Assert email được gọi đúng
        mock_send.assert_called_once_with(
            to="test@example.com",
            subject="Chào mừng Alice!",
            template="welcome"
        )
        assert result["success"] == True

# Mock DB
def test_get_user_not_found():
    with patch("repositories.user_repo.find_by_id") as mock_find:
        mock_find.return_value = None

        with pytest.raises(UserNotFoundException):
            get_user_profile(user_id="nonexistent")
```

---

## 4.5 Integration Test với FastAPI

```python
# tests/test_api_auth.py
from fastapi.testclient import TestClient
from main import app
import pytest

client = TestClient(app)

def test_login_success():
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "correct_password"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "Bearer"

def test_login_wrong_password():
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "wrong_password"
    })
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"

def test_protected_endpoint_without_token():
    response = client.get("/api/v1/profile")
    assert response.status_code == 401

def test_protected_endpoint_with_token():
    # Login trước
    login = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "correct_password"
    })
    token = login.json()["access_token"]

    # Dùng token
    response = client.get(
        "/api/v1/profile",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
```

---

## 4.6 Best Practice Testing

```python
# ✅ Test tên rõ ràng — đọc là hiểu ngay test gì
def test_order_creation_fails_when_item_out_of_stock(): ...
def test_discount_not_applied_when_user_not_eligible(): ...

# ✅ AAA Pattern: Arrange → Act → Assert
def test_apply_voucher():
    # Arrange
    order = Order(total=500000)
    voucher = Voucher(code="SAVE10", discount_percent=10)

    # Act
    result = apply_voucher(order, voucher)

    # Assert
    assert result.total == 450000
    assert result.voucher_applied == "SAVE10"

# ✅ Fixtures cho setup tái sử dụng
@pytest.fixture
def authenticated_client():
    token = create_test_token(user_id="test_user")
    return TestClient(app, headers={"Authorization": f"Bearer {token}"})

# ✅ Test edge cases
def test_empty_input():    ...
def test_max_limit():      ...
def test_negative_values(): ...
def test_unicode_strings(): ...
```

---

# 5. Logging & Observability

## 5.1 Tại sao Logging quan trọng?

```
Production crash lúc 2 giờ sáng. Không có log:
  → Không biết lỗi ở đâu
  → Không biết user nào bị ảnh hưởng
  → Không biết timeline của sự kiện
  → Debug mò kim đáy bể

Có structured logging:
  → Tìm request_id → thấy ngay toàn bộ flow
  → Filter theo error level → thấy pattern
  → Alert tự động khi error rate tăng
```

---

## 5.2 Structured Logging

```python
# ❌ Không nên — string log khó parse
print(f"User {user_id} login failed at {datetime.now()}")
logging.error("Payment failed for order 123")

# ✅ Structured log — JSON, dễ query và filter
import structlog

logger = structlog.get_logger()

logger.info(
    "user.login.failed",
    user_id=user_id,
    email=email,
    reason="invalid_password",
    ip="1.2.3.4",
    request_id=request_id
)

# Output JSON:
# {
#   "event": "user.login.failed",
#   "user_id": "usr_123",
#   "email": "a@example.com",
#   "reason": "invalid_password",
#   "ip": "1.2.3.4",
#   "request_id": "req_abc",
#   "timestamp": "2024-01-15T10:30:00Z",
#   "level": "info"
# }
```

---

## 5.3 Log Levels — dùng đúng level

| Level | Dùng khi | Ví dụ |
|-------|----------|-------|
| `DEBUG` | Development, thông tin chi tiết | "Executing query: SELECT..." |
| `INFO` | Sự kiện bình thường quan trọng | "User logged in", "Order created" |
| `WARNING` | Không lỗi nhưng cần chú ý | "Retry attempt 2/3", "Cache miss rate > 50%" |
| `ERROR` | Lỗi xảy ra, cần xử lý | "Payment failed", "DB connection timeout" |
| `CRITICAL` | Hệ thống sắp sập | "Out of memory", "DB unreachable" |

```python
# Production config: chỉ INFO trở lên
# Development: DEBUG để xem chi tiết
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
```

---

## 5.4 Correlation ID — trace request qua nhiều service

```python
# Middleware gán request_id cho mọi request
import uuid
from starlette.middleware.base import BaseHTTPMiddleware

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Gán vào context để mọi log trong request này đều có request_id
        structlog.contextvars.bind_contextvars(request_id=request_id)

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

# Mọi log sau đó tự có request_id
logger.info("Processing payment", order_id="ord_123", amount=500000)
# → {"event": "Processing payment", "request_id": "req_abc", "order_id": "ord_123", ...}

# Trace toàn bộ flow 1 request:
# grep "req_abc" production.log
```

---

## 5.5 What NOT to log

```python
# ❌ KHÔNG BAO GIỜ log thông tin nhạy cảm
logger.info("Login attempt", password=password)          # KHÔNG!
logger.info("Payment", card_number=card_number)          # KHÔNG!
logger.info("User data", ssn=user.ssn)                   # KHÔNG!
logger.info("Token", access_token=token)                 # KHÔNG!

# ✅ Log identifier, không log content
logger.info("Login attempt", email=email)
logger.info("Payment initiated", order_id=order_id, amount=amount)
logger.info("User updated", user_id=user_id, fields_changed=["email", "name"])
```

---

# 6. Config & Environment

## 6.1 12-Factor App — Config

**Nguyên tắc:** Config là thứ thay đổi giữa các môi trường (dev, staging, prod). Code không được chứa config.

```python
# ❌ Sai — hardcode trong code
DB_URL = "postgresql://user:pass@localhost/mydb"
JWT_SECRET = "supersecret"
STRIPE_KEY = "sk_live_abc123"

# ✅ Đúng — lấy từ environment
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    stripe_api_key: str
    redis_url: str = "redis://localhost:6379"  # Default cho dev
    debug: bool = False
    log_level: str = "INFO"

    class Config:
        env_file = ".env"  # Load từ .env file trong dev

settings = Settings()
```

---

## 6.2 .env File

```bash
# .env (local development — KHÔNG commit vào git!)
DATABASE_URL=postgresql://user:pass@localhost:5432/mydb
JWT_SECRET=local-dev-secret-not-for-prod
REDIS_URL=redis://localhost:6379
DEBUG=true
LOG_LEVEL=DEBUG

# .env.example (commit vào git — template cho team)
DATABASE_URL=postgresql://user:pass@host:5432/dbname
JWT_SECRET=your-secret-here
REDIS_URL=redis://host:6379
DEBUG=false
LOG_LEVEL=INFO
```

```bash
# .gitignore
.env
.env.local
*.env
```

---

## 6.3 Secret Management Production

| Môi trường | Cách quản lý secret |
|-----------|---------------------|
| Development | `.env` file local |
| Docker Compose | `environment:` hoặc `env_file:` |
| Kubernetes | `Secret` object |
| AWS | AWS Secrets Manager / Parameter Store |
| GCP | Secret Manager |
| HashiCorp | Vault |

**Kubernetes Secret:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: api-secrets
type: Opaque
stringData:
  JWT_SECRET: "your-production-secret"
  DATABASE_URL: "postgresql://..."

# Trong deployment:
env:
  - name: JWT_SECRET
    valueFrom:
      secretKeyRef:
        name: api-secrets
        key: JWT_SECRET
```

---

## 6.4 Checklist Config

```
✅ Không có secret nào trong code repository
✅ .env trong .gitignore
✅ .env.example được commit và cập nhật
✅ Mỗi môi trường có config riêng (dev/staging/prod)
✅ Secret production chỉ có người cần biết mới biết
✅ Rotate secret định kỳ hoặc khi có nhân viên nghỉ
✅ App khởi động fail-fast nếu thiếu config bắt buộc
```

```python
# Fail-fast khi thiếu config
class Settings(BaseSettings):
    jwt_secret: str        # Bắt buộc — app crash ngay khi thiếu
    database_url: str      # Bắt buộc
    redis_url: str = "redis://localhost:6379"  # Có default

# Nếu JWT_SECRET không có trong env → ValueError ngay khi khởi động
# Tốt hơn crash lúc deploy thay vì crash lúc production đang chạy
```