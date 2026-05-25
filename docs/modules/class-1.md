# 🚀 Backend Engineering Training — Tài liệu Nội bộ
---

# MỤC LỤC

1. [Asynchronous Programming](#1-asynchronous-programming)
2. [HTTP / HTTPS](#2-http--https)
3. [HTTP Request / Response](#3-http-request--response)
4. [MongoDB](#4-mongodb)
5. [RESTful API](#5-restful-api)
6. [Authentication & Authorization](#6-authentication--authorization)
7. [Caching](#7-caching)
8. [Nginx](#8-nginx)
9. [Kiến trúc Backend hiện đại](#9-kiến-trúc-tổng-thể-backend-hiện-đại)
10. [System Design thực tế](#10-system-design-thực-tế)

---
![img_2.png](img_2.png)
![img_3.png](img_3.png)
---

![img_1.png](img_1.png)

# 1. Asynchronous Programming

## 1.1 Khái niệm

**Analogy thực tế:**
> Bạn vào quán phở. Gọi món xong, bạn không đứng ở quầy chờ tô phở — bạn đi ngồi xuống, lướt điện thoại. Khi phở chín, nhân viên mang ra. Đây là **async**.
>
> Nếu bạn đứng nhìn chằm chằm vào bếp từng giây — đó là **synchronous (blocking)**.

**Synchronous (Blocking):**
```
Request A → [xử lý A...........] → Response A
Request B →                         [xử lý B...........] → Response B
```

**Asynchronous (Non-blocking):**
```
Request A → [gửi I/O, chờ] ─────────────────────────────→ Response A
Request B →   [gửi I/O, chờ] ──────────────────────────→ Response B
            (cả 2 chạy song song, không block nhau)
```

---

## 1.2 Event Loop là gì?

Event Loop là **vòng lặp vô tận** liên tục kiểm tra: "Có task nào xong chưa? Có callback nào cần chạy không?"

```
┌──────────────────────────────────────┐
│              EVENT LOOP              │
│                                      │
│  ┌─────────┐    ┌──────────────────┐ │
│  │  Call   │    │   Callback Queue │ │
│  │  Stack  │◄───│  (I/O done,      │ │
│  │         │    │   timers, etc.)  │ │
│  └─────────┘    └──────────────────┘ │
│       │                              │
│       ▼                              │
│  ┌─────────┐                         │
│  │  I/O    │  (Network, File, DB)    │
│  │  Pool   │                         │
│  └─────────┘                         │
└──────────────────────────────────────┘
```

**Python (asyncio) Event Loop:**
```python
import asyncio

async def fetch_user(user_id):
    await asyncio.sleep(1)  # Giả lập DB query
    return {"id": user_id, "name": "Alice"}

async def main():
    # Chạy song song, không tuần tự
    users = await asyncio.gather(
        fetch_user(1),
        fetch_user(2),
        fetch_user(3),
    )
    print(users)  # Xong sau ~1 giây, không phải 3 giây

asyncio.run(main())
```

---

## 1.3 Blocking vs Non-blocking

| Tình huống | Blocking | Non-blocking |
|------------|----------|--------------|
| Đọc file lớn | Thread chờ đến khi đọc xong | Gửi lệnh đọc, làm việc khác, callback khi xong |
| Query DB | Thread ngủ chờ DB | Gửi query, xử lý request khác, nhận kết quả sau |
| HTTP call | Thread đợi response | Await, tiếp tục nhận request mới |
| CPU tính toán nặng | Không thể async hoá được | Phải dùng thread/process riêng |

**Code ví dụ — Blocking vs Non-blocking:**
```python
# ❌ BLOCKING — Thread bị chiếm hết
import requests
def get_price_blocking(symbol):
    r = requests.get(f"https://api.exchange.com/price/{symbol}")
    return r.json()

# ✅ NON-BLOCKING — Thread được giải phóng trong lúc chờ
import aiohttp
async def get_price_async(symbol):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.exchange.com/price/{symbol}") as r:
            return await r.json()
```

---

## 1.4 I/O Bound vs CPU Bound

**Đây là điểm cực kỳ quan trọng.**

| Loại | Mô tả | Ví dụ | Giải pháp |
|------|-------|-------|-----------|
| **I/O Bound** | Thời gian chủ yếu chờ I/O | DB query, HTTP call, đọc file | `async/await`, event loop |
| **CPU Bound** | CPU tính toán liên tục | Mã hoá, image processing, ML | Thread pool, multiprocessing |

```
I/O Bound:
[====CPU====][........chờ DB........][====CPU====]
                   ↑
             Async giải quyết đây

CPU Bound:
[====CPU tính toán liên tục, không chờ gì====]
                   ↑
       Async KHÔNG giúp ích gì ở đây!
```

**Khi nào async KHÔNG hiệu quả:**
- Tính hash bcrypt (CPU intensive)
- Compress video/image
- ML inference với NumPy/Pandas
- Vòng lặp Python thuần túy nặng

→ Giải pháp: `ThreadPoolExecutor` hoặc `ProcessPoolExecutor`

```python
from concurrent.futures import ProcessPoolExecutor
import asyncio

def cpu_heavy_task(data):
    # Tính toán nặng
    return sum(x**2 for x in range(10_000_000))

async def main():
    loop = asyncio.get_event_loop()
    with ProcessPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, cpu_heavy_task, data)
```

---

## 1.5 Concurrency vs Parallelism

```
Concurrency (Đồng thời):          Parallelism (Song song):
  Task A: ──█─░░─█─░░──            Task A: ──████████──
  Task B: ──░░─█─░░─█──            Task B: ──████████──
  (1 CPU, luân phiên)              (2+ CPU, thực sự song song)
```

| | Concurrency | Parallelism |
|-|-------------|-------------|
| CPU cần | 1 core | Multi-core |
| Python tool | `asyncio`, `threading` | `multiprocessing` |
| Best for | I/O bound | CPU bound |
| GIL ảnh hưởng | Threading bị ảnh hưởng | Process không bị |

> **Python GIL (Global Interpreter Lock):** Python chỉ cho 1 thread chạy Python bytecode tại một thời điểm. Do đó threading trong Python KHÔNG thực sự parallel cho CPU-bound tasks.

---

## 1.6 Async/Await thực tế

```python
# FastAPI example — Production ready
from fastapi import FastAPI
import httpx
import asyncio

app = FastAPI()

@app.get("/dashboard/{user_id}")
async def get_dashboard(user_id: int):
    # Gọi 3 service cùng lúc — không tuần tự
    async with httpx.AsyncClient() as client:
        user_task = client.get(f"http://user-service/users/{user_id}")
        orders_task = client.get(f"http://order-service/orders?user={user_id}")
        wallet_task = client.get(f"http://wallet-service/balance/{user_id}")
        
        # Chạy song song — tổng thời gian = max(t1,t2,t3) thay vì t1+t2+t3
        user_r, orders_r, wallet_r = await asyncio.gather(
            user_task, orders_task, wallet_task
        )
    
    return {
        "user": user_r.json(),
        "orders": orders_r.json(),
        "wallet": wallet_r.json()
    }
```

---

## 1.7 So sánh Framework: Flask vs FastAPI vs Sanic vs Node.js

| | Flask | FastAPI | Sanic | Node.js (Express) |
|-|-------|---------|-------|-------------------|
| **Loại** | Sync (WSGI) | Async (ASGI) | Async | Async (Event Loop) |
| **Performance** | Thấp | Cao | Cao | Cao |
| **Type hints** | Không | Có (tự động docs) | Có | TypeScript |
| **Tự động API docs** | Không | Swagger + ReDoc | Không | Không |
| **Ecosystem** | Rất lớn | Lớn | Nhỏ | Rất lớn |
| **Học dễ không** | Rất dễ | Dễ | Dễ | Trung bình |
| **Production dùng** | Nhiều legacy | Trend mới nhất | Ít | Rất nhiều |
| **Best for** | Prototype, CRUD đơn giản | API service, microservice | High concurrency | Real-time, full-stack JS |

**Khi nào dùng gì:**
- Cần làm nhanh, ít traffic → **Flask**
- API mới, cần performance + docs đẹp → **FastAPI**
- High concurrency I/O → **FastAPI hoặc Sanic**
- Team biết JS, cần real-time → **Node.js**


```python
# ✅ DO: Dùng async client thay vì sync
import httpx  # Async HTTP client
import motor.motor_asyncio  # Async MongoDB driver

# ✅ DO: Gather tasks song song
results = await asyncio.gather(task1(), task2(), task3())

# ✅ DO: Timeout để tránh treo vô hạn
async with asyncio.timeout(5.0):
    result = await slow_db_query()

# ❌ DON'T: Dùng requests (sync) trong async function
import requests  # Sẽ block event loop!
response = requests.get(url)  # Block toàn bộ server!

# ❌ DON'T: time.sleep trong async code
import time
time.sleep(1)  # Block event loop!
# ✅ Thay bằng:
await asyncio.sleep(1)
```

---

# 2. HTTP / HTTPS

## 2.1 HTTP là gì?

**HTTP (HyperText Transfer Protocol)** là giao thức giao tiếp giữa client và server qua mạng. Nó định nghĩa cách request và response được format và truyền đi.

**Analogy:**
> HTTP giống như quy tắc của bưu điện: phong bì phải có địa chỉ người gửi, người nhận, tem. Nội dung bên trong là tuỳ bạn.

```
CLIENT                              SERVER
  │                                   │
  │──── HTTP Request ────────────────►│
  │     GET /api/users HTTP/1.1       │
  │     Host: api.example.com         │
  │     Authorization: Bearer token   │
  │                                   │
  │◄─── HTTP Response ────────────────│
  │     HTTP/1.1 200 OK               │
  │     Content-Type: application/json│
  │     {"users": [...]}              │
```

**HTTP là stateless:** Server không nhớ request trước. Mỗi request hoàn toàn độc lập. Đây là thiết kế cố ý để scale dễ — bất kỳ server nào cũng xử lý được request.

---

## 2.2 HTTPS và SSL/TLS

**HTTPS = HTTP + SSL/TLS encryption**

**Tại sao cần HTTPS?**
- HTTP truyền plaintext → ai cũng đọc được (man-in-the-middle attack)
- HTTPS mã hoá → chỉ client và server đọc được

**TLS Handshake Flow:**
```
CLIENT                                    SERVER
  │                                          │
  │──── ClientHello (TLS version, ciphers) ─►│
  │                                          │
  │◄─── ServerHello + Certificate ───────────│
  │     (Public key của server)              │
  │                                          │
  │  [Client verify certificate với CA]      │
  │                                          │
  │──── Pre-master secret (encrypted) ──────►│
  │     (dùng public key của server)         │
  │                                          │
  │  [Cả 2 bên tạo Session Key giống nhau]  │
  │                                          │
  │◄════════ Encrypted Communication ════════│
  │          (dùng Session Key)              │
```

**SSL vs TLS:**
| | SSL | TLS |
|-|-----|-----|
| Tình trạng | Deprecated, có lỗ hổng | Chuẩn hiện tại |
| Phiên bản dùng | Không dùng nữa | TLS 1.2, TLS 1.3 |
| Tốc độ | Chậm hơn | TLS 1.3 nhanh hơn nhiều |

> **Thực tế:** Khi nói "SSL certificate" thực ra là "TLS certificate". Thuật ngữ SSL vẫn dùng vì quen miệng.

---

## 2.3 HTTP/1.1 vs HTTP/2 vs HTTP/3

| Feature | HTTP/1.1 | HTTP/2 | HTTP/3 |
|---------|----------|--------|--------|
| **Protocol** | TCP | TCP | QUIC (UDP) |
| **Multiplexing** | Không | Có | Có |
| **Header compression** | Không | HPACK | QPACK |
| **Server Push** | Không | Có | Có |
| **HOL Blocking** | Có (request) | Có (TCP) | Không |
| **Connection** | Nhiều TCP | 1 TCP | QUIC streams |
| **HTTPS required** | Không | Thực tế có | Có |
| **Hỗ trợ** | Mọi nơi | Hầu hết | Đang tăng |

**HTTP/1.1 vấn đề:**
```
Request 1 ──────────────► Response 1
                                     Request 2 ──► Response 2
                                                              Request 3...
(Phải chờ tuần tự = Head-of-line blocking)
```

**HTTP/2 giải quyết:**
```
Request 1 ──────────────► Response 1
Request 2 ──────────────► Response 2  ← Cùng 1 TCP connection
Request 3 ──────────────► Response 3
(Multiplexing: nhiều stream trong 1 connection)
```

---

## 2.4 Keep-alive và Connection Management

```
HTTP/1.0 (không keep-alive):
  [TCP connect] → [Request] → [Response] → [TCP close]
  [TCP connect] → [Request] → [Response] → [TCP close]
  ↑ Tốn kém! Mỗi request mở TCP mới

HTTP/1.1 (keep-alive mặc định):
  [TCP connect] → [Request 1] → [Response 1] → [Request 2] → [Response 2] → [TCP close]
  ↑ 1 connection dùng nhiều lần
```

---

## 2.5 Compression

```
Client gửi header: Accept-Encoding: gzip, br
Server nén response body + trả header: Content-Encoding: gzip

JSON 100KB → gzip → ~15KB (giảm 85%)
```

Nginx config:
```nginx
gzip on;
gzip_types application/json text/plain text/html;
gzip_min_length 1000;
gzip_comp_level 6;
```

---

## 2.6 Reverse Proxy và SSL Termination

```
INTERNET                  DMZ                    INTERNAL
   │                       │                         │
   │  HTTPS (port 443)     │   HTTP (port 8080)      │
CLIENT ──────────────► NGINX ──────────────────► APP SERVER
                        │
                   [SSL Termination]
                   Giải mã HTTPS ở đây,
                   forward HTTP nội bộ
```

**Tại sao SSL Termination tại Nginx?**
- App server không cần xử lý mã hoá → nhẹ hơn
- Quản lý certificate 1 nơi thay vì nhiều server
- Dễ renew certificate

**Khi nào internal service vẫn dùng HTTP (không HTTPS)?**
- Trong Kubernetes cluster (mạng nội bộ, đã có Network Policy)
- Docker private network
- Service mesh có mTLS riêng (như Istio)
- Trust boundary rõ ràng, không expose ra ngoài

> **Nguyên tắc:** Nếu traffic đi qua internet hoặc untrusted network → LUÔN dùng HTTPS. Nội bộ cluster → có thể HTTP, nhưng cần mTLS cho production nghiêm túc.

---

# 3. HTTP Request / Response

## 3.1 Cấu trúc HTTP Request

```
POST /api/v1/orders HTTP/1.1
Host: api.example.com
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...
Accept: application/json
X-Request-ID: abc-123-def

{
  "product_id": "prod_789",
  "quantity": 2,
  "address_id": "addr_456"
}
```

| Thành phần | Ví dụ | Giải thích |
|------------|-------|------------|
| **Method** | `POST` | Loại hành động |
| **Path** | `/api/v1/orders` | Endpoint |
| **HTTP Version** | `HTTP/1.1` | Phiên bản protocol |
| **Host** | `api.example.com` | Domain |
| **Headers** | `Content-Type: application/json` | Metadata |
| **Body** | `{"product_id": ...}` | Dữ liệu gửi kèm |

---

## 3.2 HTTP Methods

| Method | Idempotent | Safe | Có Body | Dùng cho |
|--------|-----------|------|---------|----------|
| `GET` | ✅ | ✅ | Không | Lấy dữ liệu |
| `POST` | ❌ | ❌ | Có | Tạo mới |
| `PUT` | ✅ | ❌ | Có | Replace toàn bộ |
| `PATCH` | ❌ | ❌ | Có | Cập nhật một phần |
| `DELETE` | ✅ | ❌ | Tuỳ | Xoá |
| `HEAD` | ✅ | ✅ | Không | GET nhưng không có body |
| `OPTIONS` | ✅ | ✅ | Không | CORS preflight |

**Idempotent** = Gọi nhiều lần cho kết quả giống gọi 1 lần.
```
PUT /users/1 {"name": "Alice"}  → Gọi 100 lần → vẫn chỉ có 1 Alice
POST /users  {"name": "Alice"}  → Gọi 100 lần → 100 Alice mới!
```

---

## 3.3 Path Params vs Query Params

```
GET /api/v1/users/{user_id}/orders?status=pending&page=1&limit=20
              ↑                     ↑
         Path Param              Query Params
     (Định danh resource)      (Filter, pagination)
```

**Khi nào dùng Path Param:**
- Định danh resource: `/users/123`, `/products/abc`
- Hierarchical: `/orders/456/items/789`

**Khi nào dùng Query Param:**
- Filter: `?status=active`
- Pagination: `?page=2&limit=10`
- Sort: `?sort=created_at&order=desc`
- Search: `?q=iphone`

---

## 3.4 HTTP Status Codes

| Range | Category | Ví dụ |
|-------|----------|-------|
| 2xx | Success | 200 OK, 201 Created, 204 No Content |
| 3xx | Redirect | 301 Moved Permanently, 304 Not Modified |
| 4xx | Client Error | 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 422 Validation Error, 429 Too Many Requests |
| 5xx | Server Error | 500 Internal Server Error, 502 Bad Gateway, 503 Service Unavailable |

**Hay bị nhầm:**
- `401` = Chưa đăng nhập (Authentication)
- `403` = Đã đăng nhập nhưng không có quyền (Authorization)
- `404` = Không tìm thấy (cũng dùng khi không muốn lộ 403 vì security)
- `422` = Dữ liệu hợp lệ về format nhưng sai về logic (dùng trong FastAPI)
- `429` = Rate limit bị vượt quá

---

## 3.5 Headers quan trọng

**Request Headers:**
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
Accept: application/json
X-Request-ID: uuid-here          ← Trace distributed request
X-Forwarded-For: 1.2.3.4        ← IP thật của client qua proxy
User-Agent: Mozilla/5.0...
```

**Response Headers:**
```
Content-Type: application/json; charset=utf-8
X-Request-ID: uuid-here          ← Echo lại để trace
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1704067200
Cache-Control: no-store
```

---

## 3.6 REST Response Best Practice

**Success Response:**
```json
// GET /api/v1/users/123
{
  "data": {
    "id": "123",
    "name": "Nguyễn Văn A",
    "email": "a@example.com",
    "created_at": "2024-01-15T08:00:00Z"
  }
}

// GET /api/v1/users (list)
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "has_next": true
  }
}
```

**Error Response (chuẩn RFC 7807):**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Email không hợp lệ",
    "details": [
      {
        "field": "email",
        "message": "Phải là địa chỉ email hợp lệ"
      }
    ],
    "request_id": "req_abc123"
  }
}
```

---

## 3.7 Content-Type

| Content-Type | Dùng khi |
|-------------|----------|
| `application/json` | API trả JSON (phổ biến nhất) |
| `multipart/form-data` | Upload file |
| `application/x-www-form-urlencoded` | HTML form submit |
| `text/plain` | Text thuần |
| `application/octet-stream` | Binary data |

---

# 4. MongoDB

## 4.1 NoSQL là gì?

**SQL (Relational):** Dữ liệu theo bảng, hàng, cột. Schema cố định. JOIN nhiều bảng.

**NoSQL:** Nhiều mô hình lưu trữ khác nhau:
- **Document** (MongoDB): JSON-like documents
- **Key-Value** (Redis): key → value
- **Column-family** (Cassandra): Giống SQL nhưng column linh hoạt
- **Graph** (Neo4j): Quan hệ phức tạp

---

## 4.2 MongoDB — Document Database

**Analogy:**
> PostgreSQL giống file cabinet có ngăn kéo cố định — bạn phải biết trước sẽ lưu gì.
> MongoDB giống hộp đồ — bỏ gì vào cũng được, mỗi hộp khác nhau cũng không sao.

**Mapping khái niệm:**

| SQL | MongoDB |
|-----|---------|
| Database | Database |
| Table | Collection |
| Row | Document |
| Column | Field |
| JOIN | `$lookup` (aggregation) |
| Index | Index |
| Schema | Schema-less (optional validation) |

---

## 4.3 BSON

MongoDB lưu dữ liệu dưới dạng **BSON (Binary JSON)**:
- Superset của JSON
- Có thêm type: `Date`, `ObjectId`, `Binary`, `Decimal128`
- Compact hơn JSON thuần
- Hỗ trợ index hiệu quả hơn

```javascript
// Document example
{
  "_id": ObjectId("65a1b2c3d4e5f6789012abcd"),  // Auto-generated unique ID
  "user_id": "usr_123",
  "name": "Nguyễn Văn A",
  "email": "a@example.com",
  "addresses": [                           // Embedded array
    {
      "type": "home",
      "city": "Hà Nội",
      "street": "Đường ABC"
    }
  ],
  "created_at": ISODate("2024-01-15T08:00:00Z"),
  "metadata": {
    "last_login": ISODate("2024-01-20T10:30:00Z"),
    "login_count": 42
  }
}
```

---

## 4.4 Schema-less: Lợi và Hại

**Lợi:**
- Thêm field mới không cần migration
- Mỗi document có thể khác nhau
- Phù hợp dữ liệu không đồng đều

**Hại:**
- Dễ lưu dữ liệu không nhất quán
- Không có constraint như FOREIGN KEY
- Query dữ liệu linh hoạt nhưng khó validate

**Giải pháp:** Dùng **JSON Schema validation** của MongoDB:
```javascript
db.createCollection("users", {
  validator: {
    $jsonSchema: {
      required: ["name", "email"],
      properties: {
        email: { bsonType: "string", pattern: "^.+@.+$" }
      }
    }
  }
})
```

---

## 4.5 Index trong MongoDB

**Không có index = Full Collection Scan:**
```
Query: { email: "a@example.com" }
→ Scan toàn bộ 10 triệu documents
→ Slow!
```

**Có index:**
```
B-Tree index trên field "email"
→ O(log n) lookup
→ Fast!
```

**Các loại index:**
```javascript
// Single field
db.users.createIndex({ email: 1 })  // 1 = ascending, -1 = descending

// Compound (thứ tự quan trọng!)
db.orders.createIndex({ user_id: 1, created_at: -1 })

// Text search
db.products.createIndex({ name: "text", description: "text" })

// TTL Index (tự xoá document sau N giây)
db.sessions.createIndex({ created_at: 1 }, { expireAfterSeconds: 3600 })

// Partial index (chỉ index documents thoả điều kiện)
db.orders.createIndex(
  { user_id: 1 },
  { partialFilterExpression: { status: "active" } }
)
```

**ESR Rule (Equality → Sort → Range):**
```javascript
// Query: user_id = "123" AND status IN [...] ORDER BY created_at
// Index nên theo thứ tự:
db.orders.createIndex({ user_id: 1, status: 1, created_at: -1 })
```

---

## 4.6 Aggregation Pipeline

Aggregation giống "pipeline xử lý dữ liệu" — mỗi stage biến đổi output của stage trước.

```javascript
db.orders.aggregate([
  // Stage 1: Filter
  { $match: { status: "completed", created_at: { $gte: ISODate("2024-01-01") } } },
  
  // Stage 2: Group
  { $group: {
    _id: "$user_id",
    total_spent: { $sum: "$amount" },
    order_count: { $count: {} }
  }},
  
  // Stage 3: Filter sau group
  { $match: { total_spent: { $gt: 1000000 } } },
  
  // Stage 4: Sort
  { $sort: { total_spent: -1 } },
  
  // Stage 5: Limit
  { $limit: 10 },
  
  // Stage 6: Join với collection khác
  { $lookup: {
    from: "users",
    localField: "_id",
    foreignField: "_id",
    as: "user_info"
  }}
])
```

---

## 4.7 Replication

```
PRIMARY ──────────────────────────────────────────────
    │                                                 │
    ├─► SECONDARY 1 (sync replica)                   │
    ├─► SECONDARY 2 (sync replica)                   │
    └─► ARBITER (chỉ vote, không lưu data)           │
                                                      │
    Nếu Primary chết: Secondary vote bầu Primary mới ─┘
    (Auto-failover, thường < 10 giây)
```

**Write concern và Read preference:**
```javascript
// Write đến đa số replica mới confirm → đảm bảo không mất data
{ writeConcern: { w: "majority" } }

// Đọc từ Secondary → giảm tải Primary, chấp nhận đọc hơi trễ
{ readPreference: "secondaryPreferred" }
```

---

## 4.8 Sharding — Horizontal Scaling

Khi 1 server không đủ, chia data ra nhiều shard:

```
              MONGOS (Router)
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
    SHARD 1      SHARD 2     SHARD 3
  user_id        user_id     user_id
  0-9999         10000-19999  20000+
```

**Shard key quan trọng!**
- Bad: `_id` (ObjectId tăng dần → mọi write vào 1 shard)
- Bad: `timestamp` (tương tự)
- Good: `user_id` với hash sharding (phân phối đều)
- Good: `(country, user_id)` nếu query theo country nhiều

---

## 4.9 Khi nào dùng MongoDB, khi nào không

**✅ Dùng MongoDB khi:**
- Schema hay thay đổi (product catalog, content management)
- Document tự nhiên (user profile với embedded addresses)
- Cần scale horizontal dễ
- Semi-structured data
- Real-time analytics với aggregation

**❌ Không dùng MongoDB khi:**
- Cần ACID transaction phức tạp nhiều collection
- Dữ liệu quan hệ nhiều (nhiều JOIN → dùng PostgreSQL)
- Reporting phức tạp với nhiều JOIN
- Dữ liệu tài chính, kế toán (cần strict ACID)

---

## 4.10 MongoDB vs PostgreSQL

| | MongoDB | PostgreSQL |
|-|---------|-----------|
| **Data model** | Document (JSON) | Relational (Table) |
| **Schema** | Flexible | Strict |
| **ACID** | Có (v4.0+, nhưng hạn chế) | Đầy đủ |
| **JOIN** | `$lookup` (chậm hơn) | Native JOIN |
| **Scale** | Horizontal (sharding) | Vertical + Read replica |
| **Transaction** | Multi-document transaction | Full transaction |
| **Query** | MQL | SQL (mạnh hơn) |
| **Full-text search** | Cơ bản | Tốt hơn (+ pgvector) |
| **Best for** | Flexible schema, scale out | Complex queries, integrity |

> **Thực tế:** Nhiều hệ thống dùng cả 2. MongoDB cho product catalog, user profile. PostgreSQL cho order, payment, financial data.
# 5. RESTful API

## 5.1 REST Principles

REST (Representational State Transfer) là **architectural style**, không phải protocol hay standard.

**6 nguyên tắc của REST:**

1. **Client-Server:** Client và Server tách biệt, giao tiếp qua interface
2. **Stateless:** Server không lưu state của client giữa các request
3. **Cacheable:** Response phải nói rõ có cache được không
4. **Layered System:** Client không biết có bao nhiêu layer giữa nó và server
5. **Uniform Interface:** Resource-based, standard HTTP methods
6. **Code on Demand** (optional): Server có thể gửi code về client

---

## 5.2 Resource-based Design

**Sai:**
```
POST /getUser
POST /createUser
POST /deleteUser
POST /updateUserEmail
```

**Đúng (Resource-based):**
```
GET    /users              → Lấy danh sách users
POST   /users              → Tạo user mới
GET    /users/{id}         → Lấy user theo ID
PUT    /users/{id}         → Update toàn bộ user
PATCH  /users/{id}         → Update một phần user
DELETE /users/{id}         → Xoá user
```

**Nested Resources:**
```
GET    /users/{id}/orders              → Orders của user
POST   /users/{id}/orders              → Tạo order cho user
GET    /users/{id}/orders/{order_id}  → Chi tiết 1 order
```

---

## 5.3 CRUD API Mapping

| Operation | HTTP Method | Endpoint | Status Code |
|-----------|------------|----------|-------------|
| Create | POST | /resources | 201 Created |
| Read (list) | GET | /resources | 200 OK |
| Read (single) | GET | /resources/{id} | 200 OK |
| Update (full) | PUT | /resources/{id} | 200 OK |
| Update (partial) | PATCH | /resources/{id} | 200 OK |
| Delete | DELETE | /resources/{id} | 204 No Content |

---

## 5.4 Endpoint Naming Best Practice

```
✅ Đúng:
GET  /users
GET  /users/123
POST /users
GET  /users/123/orders
GET  /products?category=electronics&sort=price

❌ Sai:
GET  /getUsers
POST /createUser
GET  /user/123/getOrders
POST /users/123/delete     ← Dùng DELETE method thay vì
GET  /Users                ← lowercase
POST /user_orders/123      ← Không nhất quán
```

**Quy tắc đặt tên:**
- Dùng **noun**, không dùng verb
- **Lowercase**, dùng `-` (kebab-case): `/product-categories`
- Số nhiều: `/users` (không phải `/user`)
- Không có trailing slash: `/users` (không phải `/users/`)
- Version trong path: `/api/v1/users`

---

## 5.5 Versioning

```
# URL Versioning (phổ biến nhất, dễ test)
/api/v1/users
/api/v2/users

# Header Versioning
GET /api/users
API-Version: 2

# Query Param Versioning (ít dùng)
GET /api/users?version=2
```

**Khi nào tăng version:**
- Breaking change: xoá field, đổi tên field, đổi format
- Không tăng version khi: thêm field mới (backward compatible)

---

## 5.6 Pagination

**Offset Pagination (đơn giản, phổ biến):**
```
GET /orders?page=2&limit=20

Response:
{
  "data": [...],
  "pagination": {
    "page": 2,
    "limit": 20,
    "total": 500,
    "total_pages": 25,
    "has_next": true,
    "has_prev": true
  }
}
```
**Nhược điểm:** `OFFSET 10000` trên DB rất chậm với large dataset.

**Cursor Pagination (hiệu quả hơn với large data):**
```
GET /orders?limit=20&cursor=eyJpZCI6MTAwfQ==

Response:
{
  "data": [...],
  "next_cursor": "eyJpZCI6MTIwfQ==",
  "has_next": true
}
```
**Ưu điểm:** Không dùng OFFSET, luôn O(1) dù page bao nhiêu.

---

## 5.7 Filtering và Sorting

```
# Filter
GET /products?category=phone&brand=apple&min_price=5000000

# Sort
GET /orders?sort=created_at&order=desc

# Kết hợp
GET /products?category=phone&sort=price&order=asc&page=1&limit=20
```

---

## 5.8 Rate Limiting

```
Request → Nginx Rate Limit → App Server

Headers trả về:
X-RateLimit-Limit: 100         ← Giới hạn mỗi window
X-RateLimit-Remaining: 87      ← Còn lại
X-RateLimit-Reset: 1704067200  ← Reset lúc nào (Unix timestamp)

Khi vượt:
HTTP 429 Too Many Requests
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Quá nhiều request. Thử lại sau 60 giây.",
    "retry_after": 60
  }
}
```

---

## 5.9 REST vs GraphQL vs gRPC vs WebSocket

| | REST | GraphQL | gRPC | WebSocket |
|-|------|---------|------|-----------|
| **Giao thức** | HTTP | HTTP | HTTP/2 | TCP |
| **Format** | JSON/XML | JSON | Protobuf (binary) | Binary/Text |
| **Over-fetching** | Có | Không | Không | N/A |
| **Type safety** | Không (OpenAPI) | Có | Có | Không |
| **Real-time** | Polling | Subscription | Streaming | Native |
| **Complexity** | Thấp | Trung bình | Cao | Trung bình |
| **Best for** | Public API, CRUD | Flexible client needs | Microservice internal | Real-time, chat, gaming |

**Khi nào dùng gì:**

- **REST:** API public, CRUD operation, team không có kinh nghiệm đặc biệt
- **GraphQL:** Mobile app cần flexible query, BFF (Backend for Frontend), nhiều loại client khác nhau
- **gRPC:** Internal microservice communication, cần performance cao, strong typing
- **WebSocket:** Chat, game, live dashboard, notification, collaborative editing

---

# 6. Authentication & Authorization

## 6.1 Authentication vs Authorization

```
AUTHENTICATION (Xác thực): "Bạn là ai?"
  → Đăng nhập với username/password → Xác minh danh tính

AUTHORIZATION (Uỷ quyền): "Bạn được phép làm gì?"
  → Sau khi đăng nhập, kiểm tra quyền trước khi thực hiện action
```

**Analogy:**
> Authentication = Bảo vệ kiểm tra CMND ở cổng  
> Authorization = Nội quy phòng: nhân viên A được vào phòng server, nhân viên B không được

---

## 6.2 Session-based Auth

```
LOGIN FLOW:
  Client ──── POST /login {user, pass} ────► Server
  Server verify → Tạo session → Lưu vào Redis
  Server ◄──── Set-Cookie: session_id=abc ────

REQUEST FLOW:
  Client ──── Cookie: session_id=abc ────► Server
  Server → Redis lookup session_id → Lấy user data
  Server ◄──── Response ─────────────────
```

**Ưu điểm:** Dễ revoke (xoá session trong Redis là xong)
**Nhược điểm:** Stateful, khó scale horizontal, CSRF attack

---

## 6.3 JWT (JSON Web Token)

**Cấu trúc JWT:**
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9    ← Header (base64)
.
eyJ1c2VyX2lkIjoiMTIzIiwicm9sZSI6InVzZXIifQ   ← Payload (base64)
.
SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c   ← Signature (HMAC/RSA)
```

**Payload:**
```json
{
  "user_id": "123",
  "email": "a@example.com",
  "role": "admin",
  "iat": 1704067200,   ← Issued At
  "exp": 1704070800   ← Expires At (1 giờ sau)
}
```

**JWT Flow:**
```
ĐĂNG NHẬP:
Client ──── POST /auth/login ────► Server
Server verify credentials
Server tạo JWT (ký bằng secret key)
Server ◄──── { access_token, refresh_token } ────

REQUEST CÓ AUTH:
Client ──── Authorization: Bearer <jwt> ────► Server
Server verify signature → Decode payload → Lấy user_id, role
Server ◄──── Response ────
```

**JWT không cần DB lookup** → Nhanh, stateless!

**Nhưng: JWT không thể revoke trước khi hết hạn!**
```
Giải pháp:
1. Access token TTL ngắn (15 phút)
2. Refresh token TTL dài (7-30 ngày), lưu trong DB
3. Blacklist token trong Redis (compromise của stateless)
```

---

## 6.4 Access Token vs Refresh Token

```
ACCESS TOKEN                     REFRESH TOKEN
─────────────────────────────    ─────────────────────────────
TTL: 15 phút - 1 giờ            TTL: 7 - 30 ngày
Dùng: mọi API request           Dùng: lấy access token mới
Lưu: Memory (không localStorage) Lưu: HttpOnly Cookie
Revoke: Không dễ                 Revoke: Xoá trong DB

FLOW:
1. Đăng nhập → nhận cả 2 tokens
2. Dùng access_token cho API
3. Access_token hết hạn → Dùng refresh_token lấy access_token mới
4. Refresh_token hết hạn → Buộc đăng nhập lại
```

---

## 6.5 OAuth2

**Cho phép app third-party truy cập dữ liệu của user mà không cần biết password:**

```
USER        APP (Client)        GOOGLE (Authorization Server)     YOUR API
  │               │                         │                         │
  │── Click       │                         │                         │
  │  "Login       │                         │                         │
  │  with Google" │                         │                         │
  │               │──── Redirect to Google ─►│                         │
  │               │                         │                         │
  │◄──────────────│─────── Google Login Page─│                         │
  │               │                         │                         │
  │── Đăng nhập + Cho phép quyền ──────────►│                         │
  │               │                         │                         │
  │               │◄── Authorization Code ──│                         │
  │               │                         │                         │
  │               │──── Code + Secret ──────►│                         │
  │               │                         │                         │
  │               │◄─── Access Token ────────│                         │
  │               │                         │                         │
  │               │──── Access Token ────────────────────────────────►│
```

---

## 6.6 RBAC (Role-Based Access Control)

```
USER ──── has ──── ROLE ──── has ──── PERMISSION
 Alice        Admin              users:create
 Bob          Editor             users:read
 Charlie      Viewer             posts:publish

DB Design:
users:       { id, name, role_id }
roles:       { id, name }
permissions: { id, name, resource, action }
role_permissions: { role_id, permission_id }
```

**Code example:**
```python
# Decorator để check permission
def require_permission(permission: str):
    def decorator(func):
        async def wrapper(*args, current_user: User, **kwargs):
            if not current_user.has_permission(permission):
                raise HTTPException(403, "Forbidden")
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

@app.delete("/users/{user_id}")
@require_permission("users:delete")
async def delete_user(user_id: str, current_user: User = Depends(get_current_user)):
    ...
```

---

## 6.7 Security Best Practice

```python
# ✅ DO: Lưu password dưới dạng hash (bcrypt)
import bcrypt
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))

# ✅ DO: HTTPS only, Secure + HttpOnly cookie
response.set_cookie(
    "refresh_token", token,
    httponly=True,    # JS không đọc được → chống XSS
    secure=True,      # Chỉ gửi qua HTTPS
    samesite="strict" # Chống CSRF
)

# ✅ DO: JWT với short expiry
{"exp": time.time() + 900}  # 15 phút

# ✅ DO: Rate limit endpoint login
# Nginx: 5 requests/minute cho /auth/login

# ❌ DON'T: Lưu sensitive data trong JWT payload
{"user_id": 123, "credit_card": "4111..."}  # Payload chỉ encode, không encrypt!

# ❌ DON'T: JWT secret yếu
JWT_SECRET = "secret"  # Dễ brute force!
JWT_SECRET = secrets.token_hex(32)  # ✅

# ❌ DON'T: Lưu token trong localStorage
localStorage.setItem('token', jwt)  # Dễ bị XSS đánh cắp
```

---

## 6.8 Flow Login thực tế

```
POST /auth/login
{
  "email": "user@example.com",
  "password": "plaintext_password"
}

Server:
1. Tìm user theo email → nếu không có → 401
2. bcrypt.verify(password, hashed_password) → nếu sai → 401
3. Tạo access_token (JWT, 15 phút)
4. Tạo refresh_token (random UUID, 30 ngày, lưu vào DB)
5. Trả về:

{
  "access_token": "eyJ...",
  "token_type": "Bearer",
  "expires_in": 900
}
+ Set-Cookie: refresh_token=<uuid>; HttpOnly; Secure; SameSite=Strict
```

---

## 6.9 Khi nào JWT không phù hợp

- Cần **immediate revocation** (ban user ngay lập tức) → Dùng session + Redis
- Token **quá lớn** (nhiều claims) → Tăng size mỗi request
- Microservice cần **truyền user context** phức tạp → gRPC metadata hoặc service token riêng

---

# 7. Caching

## 7.1 Cache là gì?

**Analogy:**
> Cache như cuốn sổ tay ghi nhớ. Thay vì tra Google mỗi lần, bạn ghi số điện thoại hay dùng vào sổ tay. Lần sau lấy ra ngay, không cần tìm lại.

**Không có cache:**
```
Mỗi request → Query DB (10-100ms) → Response
1000 request/s → 1000 DB queries/s → DB quá tải
```

**Có cache:**
```
Request → Cache hit? → Yes → Return cached (< 1ms)
                    → No  → Query DB → Store in cache → Return
```

---

## 7.2 Cache Hit / Cache Miss

```
CACHE HIT (tốt):
  Request → Redis lookup → Found! → Return in < 1ms

CACHE MISS (phải xuống DB):
  Request → Redis lookup → Not found → Query DB (10-50ms) → 
  → Store in Redis → Return

Hit Rate = Cache Hits / Total Requests
Mục tiêu: > 80% hit rate
```

---

## 7.3 Redis

**Redis (Remote Dictionary Server)** là in-memory data structure store:
- **Tốc độ:** Sub-millisecond latency
- **Data types:** String, Hash, List, Set, Sorted Set, Bitmap, Stream
- **Persistence:** RDB snapshot + AOF log (optional)
- **Pub/Sub:** Hỗ trợ message pub/sub

**Use cases:**
```
1. Cache         → Lưu kết quả query DB, API response
2. Session store → Lưu session user
3. Rate limiting → Counter với TTL
4. Queue         → List LPUSH/RPOP
5. Pub/Sub       → Real-time notification
6. Leaderboard   → Sorted Set
7. Distributed lock → SET NX EX
```

---

## 7.4 Cache Patterns

**Cache Aside (Lazy Loading) — Phổ biến nhất:**
```
READ:
  App → Redis? → HIT: return
              → MISS: query DB → write to Redis → return

WRITE:
  App → Update DB → Delete (invalidate) Redis cache
```

```python
async def get_user(user_id: str):
    cache_key = f"user:{user_id}"
    
    # 1. Check cache
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # 2. Cache miss → query DB
    user = await db.users.find_one({"_id": user_id})
    
    # 3. Store in cache với TTL 1 giờ
    await redis.setex(cache_key, 3600, json.dumps(user))
    
    return user
```

**Write Through:**
```
WRITE:
  App → Write to Redis AND DB đồng thời

Ưu: Cache luôn fresh
Nhược: Write chậm hơn, có thể cache dữ liệu ít được đọc
```

**Write Behind (Write Back):**
```
WRITE:
  App → Write to Redis → Return (ngay lập tức)
  Background worker → Async write to DB

Ưu: Write rất nhanh
Nhược: Có thể mất data nếu Redis chết trước khi flush
```

---

## 7.5 Cache Invalidation

**"There are only two hard things in Computer Science: cache invalidation and naming things." — Phil Karlton**

**Strategies:**
```
1. TTL (Time To Live):
   redis.setex("key", 3600, value)  → Tự expire sau 1 giờ

2. Event-based invalidation:
   Khi update user → Delete cache "user:123"

3. Cache versioning:
   "user:123:v2" → Đổi version khi data thay đổi

4. Write-through:
   Update cache và DB cùng lúc
```

---

## 7.6 LRU (Least Recently Used)

Khi Redis đầy, cần evict keys nào?

```
Redis maxmemory-policy options:
  allkeys-lru        → Xoá key ít dùng nhất (phổ biến)
  volatile-lru       → Xoá key có TTL, ít dùng nhất
  allkeys-random     → Xoá ngẫu nhiên
  noeviction         → Từ chối write mới (không dùng cho cache)
```

---

## 7.7 CDN (Content Delivery Network)

```
User ở HN ──► CDN Edge (HN) ──► Cache hit → Response nhanh
                              ──► Cache miss → CDN Origin (US) → Cache → Response

Dùng CDN cho:
  - Static assets (JS, CSS, image)
  - Video streaming
  - API response có thể cache (public, không personalized)

Không dùng CDN cho:
  - Dynamic API cần user-specific data
  - Real-time data
  - POST/PUT/DELETE requests
```

---

## 7.8 Khi nào KHÔNG nên cache

- Dữ liệu **thay đổi liên tục** (stock price, live score)
- Dữ liệu **rất nhỏ, ít query** (không đáng complexity)
- **User-specific data** với độ phức tạp cao
- Dữ liệu cần **strong consistency** tuyệt đối (financial transactions)
- Khi **memory đắt** hơn DB query

---

## 7.9 Cache Consistency — Vấn đề thực tế

```
RACE CONDITION:
T1: Thread A read → Cache miss → Query DB (đang xử lý)
T2: Thread B update DB → Invalidate cache
T3: Thread A nhận DB result → Write stale data vào cache!

Giải pháp: Cache lock hoặc versioning
```

---

# 8. Nginx

## 8.1 Nginx là gì?

Nginx là **high-performance HTTP server** và **reverse proxy** được viết để xử lý C10k problem (10,000 concurrent connections).

**Nginx vs Apache:**

| | Nginx | Apache |
|-|-------|--------|
| **Architecture** | Event-driven, async | Process/Thread per connection |
| **Concurrency** | Hàng chục nghìn connection | Giới hạn hơn |
| **Memory** | Thấp, ổn định | Cao hơn với nhiều connection |
| **Static file** | Rất nhanh | Nhanh |
| **Dynamic content** | Qua upstream | Module trong process |
| **Config** | Declarative | Phức tạp hơn |
| **Phổ biến** | Web server, proxy | Web server truyền thống |

---

## 8.2 Nginx Architecture

```
                    NGINX MASTER PROCESS
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
     WORKER 1         WORKER 2         WORKER 3
   (1 CPU core)     (1 CPU core)     (1 CPU core)
       │                 │                 │
   Event Loop        Event Loop        Event Loop
   (Xử lý hàng      (Xử lý hàng      (Xử lý hàng
   nghìn conn)       nghìn conn)       nghìn conn)
```

---

## 8.3 Nginx Use Cases

### Web Server (Static Files)
```nginx
server {
    listen 80;
    server_name example.com;
    root /var/www/html;
    index index.html;
    
    location / {
        try_files $uri $uri/ =404;
    }
    
    # Cache static assets
    location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

### Reverse Proxy
```nginx
upstream app_servers {
    server app1:8080;
    server app2:8080;
    server app3:8080;
}

server {
    listen 443 ssl;
    server_name api.example.com;
    
    # SSL Termination
    ssl_certificate     /etc/ssl/cert.pem;
    ssl_certificate_key /etc/ssl/key.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    
    location /api/ {
        proxy_pass http://app_servers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Load Balancer
```nginx
upstream backend {
    # Round Robin (mặc định)
    server backend1:8080;
    server backend2:8080;
    server backend3:8080;
    
    # Hoặc Least Connections
    least_conn;
    
    # Hoặc IP Hash (sticky session)
    ip_hash;
    
    # Với weight
    server backend1:8080 weight=3;
    server backend2:8080 weight=1;
    
    # Health check
    server backend3:8080 backup;  # Chỉ dùng khi các server khác down
}
```

### Rate Limiting
```nginx
# Define zone
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;

server {
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        limit_req_status 429;
    }
    
    location /auth/login {
        limit_req zone=login burst=3;
    }
}
```

### WebSocket Proxy
```nginx
location /ws/ {
    proxy_pass http://websocket_backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 86400;  # 24h cho long-lived connections
}
```

---

## 8.4 Nginx trong Docker/Kubernetes

**Docker Compose:**
```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
    depends_on:
      - app

  app:
    build: .
    expose:
      - "8080"  # Không expose ra ngoài, chỉ internal
```

**Kubernetes — Ingress Controller:**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-ingress
  annotations:
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /api/
        backend:
          service:
            name: api-service
            port:
              number: 8080
```

---

# 9. Kiến trúc Tổng thể Backend Hiện đại

## 9.1 Full Stack Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           INTERNET                                   │
└─────────────────────────────┬───────────────────────────────────────┘
                              │ HTTPS (443)
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    CDN (CloudFlare / AWS CloudFront)                 │
│               Static assets, DDoS protection, SSL offload            │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         NGINX CLUSTER                                │
│  - SSL Termination                                                   │
│  - Rate Limiting                                                     │
│  - Load Balancing                                                    │
│  - Static file serving                                               │
└──────┬──────────────────────┬─────────────────────┬─────────────────┘
       │                      │                     │
       ▼                      ▼                     ▼
┌──────────────┐    ┌──────────────┐     ┌──────────────────┐
│  APP SERVER 1│    │  APP SERVER 2│     │  APP SERVER 3    │
│  (Sanic)     │    │  (Sanic)     │     │    (Sanic)       │
│              │    │              │     │                  │
│ 1. Auth MW   │    │ 1. Auth MW   │     │ 1. Auth MW       │
│ 2. Business  │    │ 2. Business  │     │ 2. Business      │
│    Logic     │    │    Logic     │     │    Logic         │
└──────┬───────┘    └──────┬───────┘     └─────────┬────────┘
       │                   │                        │
       └───────────────────┼────────────────────────┘
                           │
            ┌──────────────┴──────────────┐
            │                             │
            ▼                             ▼
┌─────────────────────┐       ┌─────────────────────┐
│   REDIS CLUSTER     │       │   MESSAGE QUEUE      │
│  - Session cache    │       │   (Kafka/RabbitMQ)   │
│  - Response cache   │       │  - Async tasks       │
│  - Rate limit       │       │  - Event streaming   │
│  - Pub/Sub          │       │  - Decoupling        │
└─────────────────────┘       └─────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         DATABASE LAYER                               │
│                                                                      │
│  ┌──────────────────────────┐    ┌───────────────────────────────┐  │
│  │     MONGODB CLUSTER       │    │      POSTGRESQL CLUSTER        │  │
│  │  Primary ─► Secondary     │    │  Primary ─► Replica 1         │  │
│  │           ─► Secondary    │    │           ─► Replica 2         │  │
│  │  (User profiles, Content) │    │  (Orders, Payments, Finance)  │  │
│  └──────────────────────────┘    └───────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 9.2 Request Lifecycle — Chi tiết từng bước

```
1. CLIENT gửi HTTPS request
   GET https://api.example.com/api/v1/products/123

2. DNS → IP của Load Balancer / CDN

3. NGINX nhận request:
   a. Terminate SSL/TLS
   b. Kiểm tra rate limit
   c. Route đến App Server (round-robin)
   d. Forward headers: X-Real-IP, X-Forwarded-For

4. APP SERVER nhận HTTP request:
   a. Middleware: CORS check
   b. Middleware: Authentication (verify JWT)
   c. Router: match /api/v1/products/{id}
   d. Middleware: Authorization (check permission)
   e. Handler: Business Logic
      i.  Check Redis cache: "product:123"
      ii. Cache HIT → Return cached data
      iii.Cache MISS → Query MongoDB
      iv. Store in Redis với TTL
      v.  Return data
   f. Response serialization

5. NGINX nhận response từ App, forward về Client

6. CLIENT nhận response
```

---

## 9.3 Middleware Stack thực tế (FastAPI)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import time

app = FastAPI()

# 1. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.example.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Request ID + Logging
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    logger.info(f"{request.method} {request.url} {response.status_code} {duration:.3f}s")
    
    response.headers["X-Request-ID"] = request_id
    return response

# 3. Authentication Dependency
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    payload = verify_jwt(token)
    user = await get_user_from_cache_or_db(payload["user_id"])
    return user

# 4. Route với auth
@app.get("/api/v1/products/{id}")
async def get_product(id: str, current_user: User = Depends(get_current_user)):
    ...
```

---

# 10. System Design thực tế

## 10.1 Hệ thống xác thực quốc gia (eKYC)

**Yêu cầu:**
- Xác thực CCCD, chụp ảnh selfie so khớp
- 500K request/ngày (~6 req/s average, peak 50 req/s)
- SLA: 99.9% uptime, < 3s response
- Lưu ảnh và kết quả lâu dài

```
ARCHITECTURE:

User ──► CDN ──► Nginx ──► API Gateway
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
              Auth Service  KYC Service  Notification
                                │           Service
                    ┌───────────┤
                    ▼           ▼
              Face Match    ID Card OCR
              Service       Service (AI)
              (External)    (External)
                    │
                    ▼
              ┌─────────────────────────────────┐
              │  PostgreSQL (Kết quả KYC,       │
              │  user info, audit log)           │
              │                                  │
              │  S3/MinIO (Lưu ảnh, document)   │
              │                                  │
              │  Redis (Session, rate limit,     │
              │  dedup check)                    │
              └─────────────────────────────────┘
```

**Key considerations:**
- **Idempotency:** Cùng 1 CCCD số không xác thực lại (Redis dedup)
- **Rate limiting:** 3 lần/ngày/CCCD, 5 lần/ngày/IP
- **Async:** AI processing chạy async với Celery/Kafka
- **Audit log:** Mọi request đều log với timestamp, IP, result
- **Data retention:** Ảnh lưu encrypted, policy xoá sau N năm

---

## 10.2 Hệ thống API chịu tải lớn

**Scenario:** Flash sale ecommerce — 100K users/phút, cần đặt hàng

```
PROBLEM: 100K users cùng lúc → DB không chịu nổi

SOLUTION — Multi-layer:

Layer 1: CDN
  → Cache product info, static pages

Layer 2: Nginx Rate Limit
  → 1000 req/s per IP → giảm DDoS

Layer 3: Redis Queue
  → Không ghi thẳng vào DB
  → Đẩy order vào Redis Queue trước
  → Return "Order received, processing..."

Layer 4: Order Workers
  → Pool of workers consume queue
  → Check tồn kho (Redis counter)
  → Ghi vào DB
  → Notify user qua WebSocket/Email

FLOW:
User click "Mua" → Nginx → API Server → 
→ Check inventory counter (Redis DECR) →
  → < 0: "Hết hàng" (Redis INCR rollback)
  → >= 0: Push to Kafka → Return 202 Accepted

Kafka Consumer → Validate → Write to DB → 
→ Notify user (WebSocket/Push notification)
```

**Key pattern:** Inventory counter trong Redis (DECR atomic), order processing async qua queue.

---

## 10.3 Microservice Architecture

```
API GATEWAY (Kong / AWS API GW)
        │
        ├──► User Service         (FastAPI + PostgreSQL)
        ├──► Product Service      (FastAPI + MongoDB)
        ├──► Order Service        (FastAPI + PostgreSQL)
        ├──► Payment Service      (FastAPI + PostgreSQL)
        ├──► Notification Service (FastAPI + Redis PubSub)
        └──► Search Service       (FastAPI + Elasticsearch)

COMMUNICATION:
  Sync:  gRPC (internal service-to-service)
  Async: Kafka (event-driven, decoupled)

SHARED INFRASTRUCTURE:
  - Redis (cache, session)
  - Kafka (events)
  - Elasticsearch (search, logging)
  - Jaeger/Zipkin (distributed tracing)
  - Prometheus + Grafana (monitoring)
```

**Trade-offs:**
| | Monolith | Microservice |
|-|---------|--------------|
| Development speed | Nhanh ban đầu | Chậm hơn ban đầu |
| Scale | Phải scale toàn bộ | Scale từng service |
| Complexity | Thấp | Cao (network, deploy) |
| Team size | Nhỏ | Lớn (team per service) |
| Best for | Startup, MVP | Scale-up, large team |

---

## 10.4 Docker và Kubernetes Deployment

**Docker Compose (Development/Staging):**
```yaml
version: '3.8'
services:
  api:
    build: .
    environment:
      - DATABASE_URL=mongodb://mongo:27017/mydb
      - REDIS_URL=redis://redis:6379
    depends_on:
      - mongo
      - redis
    deploy:
      replicas: 3

  nginx:
    image: nginx:alpine
    ports: ["80:80", "443:443"]
    volumes: ["./nginx.conf:/etc/nginx/nginx.conf"]

  mongo:
    image: mongo:7
    volumes: ["mongo_data:/data/db"]

  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
```

**Kubernetes (Production):**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-deployment
spec:
  replicas: 3
  selector:
    matchLabels: { app: api }
  template:
    spec:
      containers:
      - name: api
        image: myregistry/api:v1.2.3
        resources:
          requests: { cpu: "250m", memory: "256Mi" }
          limits:   { cpu: "500m", memory: "512Mi" }
        livenessProbe:
          httpGet: { path: /health, port: 8080 }
          initialDelaySeconds: 30
        readinessProbe:
          httpGet: { path: /ready, port: 8080 }
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
spec:
  scaleTargetRef: { kind: Deployment, name: api-deployment }
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target: { type: Utilization, averageUtilization: 70 }
```

---

## 10.5 Database Scaling Strategy

```
VERTICAL SCALING (Scale Up):
  - Tăng CPU, RAM, SSD
  - Đơn giản nhưng có giới hạn và đắt

READ SCALING:
  Primary ──► Read Replica 1 (đọc)
           ──► Read Replica 2 (đọc)
           ──► Read Replica 3 (đọc, báo cáo)
  
  App: Write → Primary
  App: Read  → Replica (load balanced)

SHARDING (Horizontal Write Scaling):
  Shard 1: user_id % 3 = 0  → Server A
  Shard 2: user_id % 3 = 1  → Server B
  Shard 3: user_id % 3 = 2  → Server C
  
  Cross-shard query = phức tạp!
  → Tránh query nhiều shard khi có thể

CQRS (Command Query Responsibility Segregation):
  Write (Command) → Primary DB → Event → 
  → Update Read Model (Elasticsearch/MongoDB)
  Read (Query) → Read Model (optimized for reads)
```

---

## 10.6 Hot/Cold Storage

```
HOT STORAGE (Recent data, fast access):
  - PostgreSQL/MongoDB Primary
  - Redis Cache
  - SSD storage
  - Cost: Cao
  - Access: < 10ms
  - Dữ liệu: 0-90 ngày

WARM STORAGE (Older data, occasional access):
  - Read Replicas
  - Object Storage với index (S3 + Athena)
  - HDD storage
  - Cost: Trung bình
  - Access: 10ms - 1s
  - Dữ liệu: 90 ngày - 2 năm

COLD STORAGE (Archive, rare access):
  - S3 Glacier / Azure Archive
  - Tape backup
  - Cost: Rất thấp
  - Access: Phút - Giờ
  - Dữ liệu: > 2 năm

AUTOMATION:
  - Data lifecycle policy tự động move data
  - Ví dụ: Orders > 1 năm → move sang cold storage
  - Giảm cost đáng kể
```

---

## 10.7 High Availability Design

```
SINGLE POINT OF FAILURE → Phải loại bỏ:

❌ 1 Nginx → ✅ Nginx cluster + Keepalived (VIP)
❌ 1 App Server → ✅ Nhiều replicas + Health check
❌ 1 DB → ✅ Primary + Replica + Auto-failover
❌ 1 Redis → ✅ Redis Sentinel / Redis Cluster
❌ 1 Datacenter → ✅ Multi-AZ / Multi-Region

AVAILABILITY CALCULATION:
  99.9%   = 8.7 giờ downtime/năm
  99.99%  = 52 phút downtime/năm
  99.999% = 5 phút downtime/năm (five nines)

ĐỂ ĐẠT 99.99%:
  - Redundancy ở mọi layer
  - Auto-failover < 30 giây
  - Zero-downtime deployment (rolling update, blue-green)
  - Circuit breaker (tự ngắt service lỗi)
  - Chaos engineering (Netflix Chaos Monkey)
```

---

## 10.8 Queue và Event Streaming

```
RABBITMQ (Task Queue):
  Producer → Exchange → Queue → Consumer
  Use case: Email, notification, report generation
  Best for: Task distribution, retry logic

KAFKA (Event Streaming):
  Producer → Topic (partitioned) → Consumer Group
  Use case: Event sourcing, log aggregation, real-time analytics
  Best for: High throughput, event streaming, audit trail

KHAI NIỆM QUAN TRỌNG:

  Message Queue (RabbitMQ):
    - Mỗi message xử lý 1 lần
    - Message xoá sau khi consumed
    - Task distribution

  Event Stream (Kafka):
    - Message persist, có thể replay
    - Multiple consumers đọc cùng 1 event
    - Event sourcing, audit log, stream processing

PATTERN THỰC TẾ:
  Order created → Kafka Event →
    ├─► Payment Service (charge card)
    ├─► Inventory Service (reserve stock)
    ├─► Notification Service (send email)
    └─► Analytics Service (update metrics)
  
  Mỗi service xử lý độc lập, không coupling
```

---

## Tổng kết — Checklist cho Junior Backend

### Khi build API mới:
- [ ] HTTPS only (không plain HTTP ra ngoài)
- [ ] Authentication (JWT với short TTL)
- [ ] Authorization (kiểm tra permission trước khi execute)
- [ ] Input validation (validate tất cả input từ client)
- [ ] Rate limiting (tránh abuse)
- [ ] Proper HTTP status codes
- [ ] Consistent error format
- [ ] Request ID để trace
- [ ] Logging với correlation ID
- [ ] Health check endpoint (`/health`)

### Khi design database:
- [ ] Index cho các field query nhiều
- [ ] EXPLAIN query để check query plan
- [ ] Connection pooling (không mở connection mới mỗi request)
- [ ] Không lưu password plaintext
- [ ] Backup strategy

### Khi deploy:
- [ ] Environment variables cho secrets (không hardcode)
- [ ] Graceful shutdown (xử lý xong request hiện tại trước khi tắt)
- [ ] Health check + Readiness probe
- [ ] Resource limits (CPU, memory)
- [ ] Monitoring + Alerting

### Câu hỏi luôn tự hỏi:
- "Nếu service này chết, hệ thống có vẫn hoạt động không?"
- "Data này có cần cache không? TTL bao lâu?"
- "API này có thể bị abuse không? Cần rate limit không?"
- "Nếu DB chậm, user experience như thế nào?"
- "Làm sao biết service đang healthy?"