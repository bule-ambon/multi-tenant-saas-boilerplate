# Developer Guide

Complete guide for developing and deploying the Multi-Tenant SaaS Platform.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Getting Started](#getting-started)
3. [Multi-Tenant Architecture](#multi-tenant-architecture)
4. [Authentication & Security](#authentication--security)
5. [RBAC Implementation](#rbac-implementation)
6. [Billing Integration](#billing-integration)
7. [API Development](#api-development)
8. [Frontend Development](#frontend-development)
9. [Testing](#testing)
10. [Deployment](#deployment)
11. [Monitoring & Logging](#monitoring--logging)
12. [Troubleshooting](#troubleshooting)

## Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Internet/Users                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
           ┌───────────┴───────────┐
           │   Load Balancer/CDN   │
           └───────────┬───────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
┌───────▼────────┐           ┌────────▼───────┐
│  React Frontend│           │  FastAPI       │
│  (Port 3000)   │           │  Backend       │
│                │           │  (Port 8000)   │
└────────────────┘           └────────┬───────┘
                                      │
                     ┌────────────────┴────────────────┐
                     │                                  │
            ┌────────▼────────┐              ┌─────────▼────────┐
            │   PostgreSQL    │              │     Redis        │
            │   (Multi-tenant)│              │  (Cache/Queue)   │
            └─────────────────┘              └──────────────────┘
```

### Tech Stack

**Backend:**
- FastAPI (Python) - Web framework
- SQLAlchemy - ORM
- Alembic - Database migrations
- Celery - Background tasks
- Redis - Caching & message broker
- PostgreSQL - Primary database with RLS

**Frontend:**
- React 18 - UI library
- TypeScript - Type safety
- Vite - Build tool
- TanStack Query - Data fetching
- Zustand - State management

**DevOps:**
- Docker - Containerization
- Kubernetes - Orchestration
- Terraform - Infrastructure as Code
- Prometheus - Monitoring
- Grafana - Visualization

## Getting Started

### Prerequisites

```bash
# Required
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+

# Optional
- kubectl (for Kubernetes)
- terraform (for IaC)
```

### Local Development Setup

1. **Clone and Setup Environment:**

```bash
git clone <repository>
cd saas-template

# Copy environment variables
cp .env.example .env

# Edit .env with your settings
nano .env
```

2. **Start Services with Docker Compose:**

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

3. **Run Database Migrations:**

```bash
# Enter backend container
docker-compose exec backend bash

# Run migrations
alembic upgrade head

# Create super admin
python scripts/create_superadmin.py
```

4. **Access Services:**

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- pgAdmin: http://localhost:5050
- Grafana: http://localhost:3001

### Manual Development Setup

**Backend:**

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://saas_user:saas_password@localhost/saas_platform"
export SECRET_KEY="your-secret-key"

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

**Frontend:**

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Multi-Tenant Architecture

### Tenancy Modes

The platform supports two tenancy modes:

#### 1. Shared Database with RLS (Default)

All tenants share the same database with Row-Level Security policies enforcing data isolation.

**Advantages:**
- Cost-effective
- Easy to manage
- Simple backups
- Better resource utilization

**Configuration:**
```python
TENANCY_MODE=shared
```

**How it works:**
```python
# Set tenant context before queries
await set_tenant_context_async(db_session, tenant_id)

# RLS policy automatically filters data
users = await db.query(User).all()  # Only returns users from current tenant
```

#### 2. Database-Per-Tenant

Each tenant gets a separate database.

**Advantages:**
- Complete isolation
- Independent scaling
- Tenant-specific backups

**Configuration:**
```python
TENANCY_MODE=isolated
```

**How it works:**
```python
# Get tenant-specific database connection
async with get_tenant_db(tenant_id) as db:
    users = await db.query(User).all()
```

### Tenant Identification

Two methods supported:

1. **Subdomain** (Default): `tenant1.yourdomain.com`
2. **Header**: `X-Tenant-ID: tenant-uuid`

```python
# Configure in .env
TENANT_IDENTIFICATION=subdomain  # or 'header'
```

### Implementing RLS Policies

```sql
-- Enable RLS on table
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Create policy
CREATE POLICY tenant_isolation_policy ON users
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- Set tenant context
SET app.current_tenant_id = '<tenant-uuid>';
```

## Authentication & Security

### JWT Authentication

**Login Flow:**

```python
# 1. User submits credentials
POST /api/v1/auth/login
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "mfa_code": "123456"  # Optional
}

# 2. Server validates and returns tokens
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "expires_in": 1800
}

# 3. Client includes token in requests
Authorization: Bearer eyJ...
```

**Token Refresh:**

```python
POST /api/v1/auth/refresh
Authorization: Bearer <refresh_token>
```

### Multi-Factor Authentication (MFA)

**Setup MFA:**

```python
# 1. Generate secret
POST /api/v1/auth/mfa/setup

# Returns:
{
  "secret": "BASE32SECRET",
  "qr_code_uri": "otpauth://...",
  "backup_codes": ["CODE1", "CODE2", ...]
}

# 2. User scans QR code with authenticator app

# 3. Verify and enable
POST /api/v1/auth/mfa/enable
{
  "verification_code": "123456"
}
```

### OAuth Integration

**Google OAuth:**

```python
# 1. Redirect to Google
GET /api/v1/auth/google

# 2. Callback
GET /api/v1/auth/google/callback?code=...

# Returns access and refresh tokens
```

**GitHub OAuth:**

```python
GET /api/v1/auth/github
GET /api/v1/auth/github/callback?code=...
```

### Password Security

**Password Requirements:**

```python
PASSWORD_MIN_LENGTH=8
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_DIGIT=true
PASSWORD_REQUIRE_SPECIAL=true
```

**Account Lockout:**

```python
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=30
```

### Security Best Practices

1. **Use HTTPS in production**
2. **Implement rate limiting**
3. **Enable CORS properly**
4. **Use strong secret keys**
5. **Rotate API keys regularly**
6. **Enable audit logging**

## RBAC Implementation

### Role Structure

```python
class Role:
    - id: UUID
    - tenant_id: UUID  # Tenant-specific
    - name: str
    - permissions: List[Permission]
```

### Default Roles

1. **Super Admin** (Platform-level)
   - Full system access
   - Manage all tenants
   - System configuration

2. **Tenant Admin** (Tenant-level)
   - Full tenant access
   - User management
   - Billing management

3. **Manager**
   - Team management
   - Content creation

4. **Staff**
   - Limited operations

5. **Member**
   - Read-only access

### Creating Custom Roles

```python
POST /api/v1/roles
{
  "name": "Content Editor",
  "permissions": [
    "content:create",
    "content:update",
    "content:read"
  ]
}
```

### Checking Permissions

```python
from app.services.rbac import check_permission

# In route handler
if not await check_permission(current_user, "users:create", tenant_id):
    raise HTTPException(status_code=403, detail="Permission denied")
```

### Permission Naming Convention

Format: `resource:action`

Examples:
- `users:create`
- `users:read`
- `users:update`
- `users:delete`
- `billing:manage`
- `settings:update`

## Billing Integration

### Stripe Setup

1. **Create Stripe Account**: https://stripe.com

2. **Get API Keys:**
   - Dashboard → Developers → API keys

3. **Configure Webhook:**
   - Endpoint: `https://yourdomain.com/api/v1/billing/webhook/stripe`
   - Events: `customer.subscription.*`, `invoice.*`

4. **Environment Variables:**

```bash
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### Creating Subscriptions

**Via Checkout Session:**

```python
POST /api/v1/billing/checkout-session
{
  "price_id": "price_...",
  "success_url": "https://yourdomain.com/success",
  "cancel_url": "https://yourdomain.com/cancel"
}

# Returns:
{
  "checkout_url": "https://checkout.stripe.com/...",
  "session_id": "cs_..."
}
```

### Webhook Handling

```python
# backend/app/api/v1/billing.py

@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    event = stripe.Webhook.construct_event(
        payload,
        sig_header,
        settings.STRIPE_WEBHOOK_SECRET
    )

    if event["type"] == "customer.subscription.created":
        # Handle subscription created
        pass
    elif event["type"] == "invoice.paid":
        # Handle successful payment
        pass
```

### Usage-Based Billing

```python
# Track usage
POST /api/v1/billing/usage
{
  "metric": "api_calls",
  "quantity": 1000,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## API Development

### Creating New Endpoints

```python
# backend/app/api/v1/my_resource.py

from fastapi import APIRouter, Depends
from app.models.user import User
from app.api.v1.auth import get_current_user

router = APIRouter()

@router.get("/items")
async def list_items(
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(require_tenant),
    db: AsyncSession = Depends(get_async_db),
):
    """List items for current tenant"""
    # Your logic here
    return {"items": []}
```

### Database Queries with Tenant Context

```python
# Automatic tenant filtering with RLS
async with get_tenant_db(tenant_id) as db:
    items = await db.execute(
        select(Item).where(Item.is_active == True)
    )
    return items.scalars().all()
```

### API Documentation

FastAPI generates automatic documentation:
- Swagger UI: `/docs`
- ReDoc: `/redoc`

**Add description:**

```python
@router.post(
    "/items",
    summary="Create item",
    description="Create a new item for the current tenant",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
)
```

## Frontend Development

### Project Structure

```
frontend/
├── src/
│   ├── components/     # Reusable components
│   ├── pages/          # Page components
│   ├── hooks/          # Custom hooks
│   ├── services/       # API services
│   ├── stores/         # Zustand stores
│   ├── utils/          # Utility functions
│   └── types/          # TypeScript types
```

### API Calls

```typescript
// src/services/api.ts

import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
});

// Add auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
```

### Using TanStack Query

```typescript
// src/hooks/useUsers.ts

import { useQuery } from '@tanstack/react-query';
import api from '../services/api';

export function useUsers() {
  return useQuery({
    queryKey: ['users'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/users');
      return data;
    },
  });
}
```

### State Management

```typescript
// src/stores/authStore.ts

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  user: User | null;
  token: string | null;
  login: (token: string, user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      login: (token, user) => set({ token, user }),
      logout: () => set({ token: null, user: null }),
    }),
    { name: 'auth-storage' }
  )
);
```

## Testing

Prepare your local environment before running the suites: create/activate a Python virtual environment inside `backend/` and install its dependencies (`python -m venv venv && source venv/bin/activate` on Unix, then `pip install -r requirements.txt`); for the frontend run `npm install` once so Vitest/the tooling is available. You can run the commands below directly on your host machine without entering any Docker container unless you prefer the agent-focused workflow later in this document.

### Backend Testing

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_auth.py -v
```

If `pytest` is missing, install it via `pip install pytest` inside the active virtual environment; the same applies if you see missing dependencies before running the suite. You can also use `python -m pytest` if your shell’s PATH does not pick up the `pytest` binary.

**Example Test:**

```python
# tests/test_auth.py

import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "TestPass123!",
            "full_name": "Test User"
        }
    )
    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"
```

### Frontend Testing

```bash
cd frontend

# Run tests
npm test

# Run with coverage
npm test -- --coverage
```

Run `npm install` before invoking any of these commands so the Vitest dependencies exist locally.

## Deployment

### Docker Production

```bash
# Build images
docker-compose -f docker-compose.prod.yml build

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes Deployment

```bash
# Apply configurations
kubectl apply -f kubernetes/

# Check status
kubectl get pods
kubectl get services

# View logs
kubectl logs -f deployment/saas-backend

# Scale deployment
kubectl scale deployment saas-backend --replicas=5
```

### Terraform AWS Deployment

```bash
cd terraform/aws

# Initialize
terraform init

# Plan
terraform plan -var="domain_name=yourdomain.com"

# Apply
terraform apply -var="domain_name=yourdomain.com"

# Outputs
terraform output
```

## Monitoring & Logging

### Prometheus Metrics

Access Prometheus: http://localhost:9090

**Key Metrics:**
- `http_requests_total`
- `http_request_duration_seconds`
- `database_connections_active`

### Grafana Dashboards

Access Grafana: http://localhost:3001

**Default Credentials:**
- Username: admin
- Password: admin

### Application Logs

**Structured JSON Logging:**

```python
logger.info(
    "User login successful",
    extra={
        "user_id": user.id,
        "tenant_id": tenant.id,
        "ip_address": request.client.host,
    }
)
```

### Audit Logs

All critical actions are automatically logged in the `audit_logs` table.

## Troubleshooting

### Common Issues

**1. Database Connection Errors**

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check connection string
echo $DATABASE_URL

# Reset database
docker-compose down -v
docker-compose up -d postgres
```

**2. Migration Errors**

```bash
# Check current migration
alembic current

# Downgrade one version
alembic downgrade -1

# Upgrade to head
alembic upgrade head
```

**3. Redis Connection Issues**

```bash
# Check Redis is running
docker-compose ps redis

# Test connection
docker-compose exec redis redis-cli ping
```

**4. Frontend Build Errors**

```bash
# Clear node_modules
rm -rf node_modules package-lock.json
npm install

# Clear cache
npm cache clean --force
```

### Debug Mode

Enable debug mode in `.env`:

```bash
DEBUG=true
LOG_LEVEL=DEBUG
ENABLE_SQL_LOGGING=true
```

### Support

- GitHub Issues: [Create an issue](https://github.com/your-repo/issues)
- Documentation: [docs/](docs/)
- Email: support@yoursaas.com

---

**Happy Building! 🚀**
