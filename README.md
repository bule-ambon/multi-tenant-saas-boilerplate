# 🚀 Multi-Tenant SaaS Platform Boilerplate

A production-ready, secure Multi-Tenant SaaS platform boilerplate with complete tenant isolation, billing integration, and RBAC.

## ✨ Features

### 🏢 Multi-Tenancy
- **Dual Tenancy Modes**: Shared database with Row-Level Security (RLS) OR isolated database per tenant
- **Complete Data Isolation**: PostgreSQL RLS policies ensure strict tenant separation
- **Tenant Identification**: Subdomain-based or header-based tenant resolution
- **Custom Branding**: Per-tenant logos, colors, and themes
- **Domain Mapping**: Custom domain support for each tenant

### 🔐 Authentication & Security
- **Multiple Auth Methods**: Email/Password, OAuth (Google, GitHub), Magic Links
- **Multi-Factor Authentication**: TOTP-based 2FA
- **Password Management**: Secure reset flows, password policies
- **Device Tracking**: Monitor and manage user sessions across devices
- **JWT Tokens**: Access & refresh token rotation
- **Rate Limiting**: Per-tenant and per-endpoint rate limits
- **CORS & CSRF Protection**: Configurable security policies
- **Encryption at Rest**: Database-level encryption for sensitive data

### 👥 Role-Based Access Control (RBAC)
- **Tenant-Specific Roles**: Each organization defines custom roles
- **Granular Permissions**: Resource-level permission control
- **User Groups**: Organize users into teams with inherited permissions
- **Built-in Roles**: Admin, Manager, Staff, Member templates
- **Permission Inheritance**: Hierarchical permission structures

### 💳 Subscription & Billing
- **Payment Provider Integration**: Stripe, Paystack, Flutterwave support
- **Flexible Plans**: Free trial, monthly, annual, usage-based billing
- **Proration**: Automatic plan change calculations
- **Coupons & Discounts**: Promotional code system
- **Invoice Management**: PDF generation and email delivery
- **Webhook Handlers**: Real-time payment status updates
- **Usage Tracking**: Metered billing for API calls, storage, etc.

### 📊 Admin Dashboards

#### Tenant Dashboard
- Usage analytics and metrics
- Billing history and invoices
- User management and invitations
- Audit logs and activity tracking
- Team member roles and permissions
- Organization settings

#### Super-Admin Platform
- Multi-tenant overview and management
- System health monitoring
- Global audit logs
- Tenant suspension/activation
- Platform-wide analytics
- Configuration management

### 🛠 DevOps & Deployment
- **Docker**: Complete containerization
- **Docker Compose**: Local development environment
- **Kubernetes**: Production-ready manifests (deployment, services, ingress)
- **Terraform**: IaC examples for AWS, GCP, Azure
- **CI/CD**: GitHub Actions workflows
- **Monitoring**: Prometheus & Grafana integration
- **Logging**: Structured logging with ELK stack support

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Load Balancer                         │
└─────────────────┬───────────────────────────────────────────┘
                  │
        ┌─────────┴─────────┐
        │   Tenant Router   │ (Subdomain/Header Resolution)
        └─────────┬─────────┘
                  │
    ┌─────────────┴─────────────┐
    │                           │
┌───▼────┐                 ┌────▼───┐
│ API    │                 │ React  │
│ Server │◄────────────────┤ SPA    │
│(FastAPI)│                 └────────┘
└───┬────┘
    │
    ├──► PostgreSQL (RLS) ──► Tenant A Data
    ├──► PostgreSQL (RLS) ──► Tenant B Data
    │
    ├──► Redis (Cache & Sessions)
    ├──► Stripe API (Billing)
    └──► S3/Storage (File Uploads)
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+

### Local Development

```bash
# Clone the repository
git clone <repository-url>
cd Secure-Multi-Tenant-SaaS-Platform-Boilerplate-with-Billing-RBAC-and-Tenant-Isolation

# Copy environment variables
cp .env.example .env

# Start services with Docker Compose
docker-compose up -d

# Run database migrations
docker-compose exec backend alembic upgrade head

# Create super admin
docker-compose exec backend python scripts/create_superadmin.py

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Manual Setup

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://user:password@localhost/saas_db"
export SECRET_KEY="your-secret-key"
export STRIPE_SECRET_KEY="your-stripe-key"

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

## 📁 Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI application
│   │   ├── core/
│   │   │   ├── config.py              # Configuration management
│   │   │   ├── security.py            # Security utilities
│   │   │   ├── database.py            # Database connection
│   │   │   └── tenant.py              # Tenant context management
│   │   ├── models/                    # SQLAlchemy models
│   │   │   ├── user.py
│   │   │   ├── tenant.py
│   │   │   ├── role.py
│   │   │   ├── permission.py
│   │   │   └── subscription.py
│   │   ├── schemas/                   # Pydantic schemas
│   │   ├── api/                       # API routes
│   │   │   ├── v1/
│   │   │   │   ├── auth.py
│   │   │   │   ├── tenants.py
│   │   │   │   ├── users.py
│   │   │   │   ├── roles.py
│   │   │   │   ├── billing.py
│   │   │   │   └── admin.py
│   │   ├── services/                  # Business logic
│   │   │   ├── auth_service.py
│   │   │   ├── tenant_service.py
│   │   │   ├── billing_service.py
│   │   │   └── rbac_service.py
│   │   ├── middleware/                # Custom middleware
│   │   │   ├── tenant_middleware.py
│   │   │   ├── rate_limit.py
│   │   │   └── audit_log.py
│   │   └── utils/
│   ├── alembic/                       # Database migrations
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Auth/
│   │   │   ├── Dashboard/
│   │   │   ├── Billing/
│   │   │   └── Admin/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── hooks/
│   │   ├── contexts/
│   │   └── App.tsx
│   ├── package.json
│   └── Dockerfile
├── kubernetes/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   └── configmap.yaml
├── terraform/
│   ├── aws/
│   ├── gcp/
│   └── azure/
├── docker-compose.yml
├── .env.example
└── README.md
```

## 🔧 Configuration

### Environment Variables

```bash
# Application
APP_NAME=Multi-Tenant SaaS Platform
ENVIRONMENT=development
SECRET_KEY=your-secret-key-change-in-production
DEBUG=true
AUTO_INIT_DB=false  # keep false so Alembic handles schema creation

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/saas_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Multi-Tenancy
TENANCY_MODE=shared  # or 'isolated'
TENANT_IDENTIFICATION=subdomain  # or 'header'

# Authentication
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
PASSWORD_MIN_LENGTH=8
REQUIRE_MFA=false

# OAuth Providers
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-secret
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-secret

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PUBLISHABLE_KEY=pk_test_...

# Redis
REDIS_URL=redis://localhost:6379/0

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-password
FROM_EMAIL=noreply@yoursaas.com

# Security
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
RATE_LIMIT_PER_MINUTE=60
ENABLE_CSRF_PROTECTION=true

# Storage
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_S3_BUCKET=your-bucket-name
AWS_REGION=us-east-1
```

The Postgres container no longer mounts `scripts/init-db.sql`; instead the schema is defined by Alembic, so keep `AUTO_INIT_DB=false` (default) and run `docker-compose exec backend alembic upgrade head` before seeding users. Only flip `AUTO_INIT_DB` to `true` for throwaway demos when you want `Base.metadata.create_all` without migrations.

## 🔐 Multi-Tenant Data Isolation

### Row-Level Security (RLS) Mode

The platform uses PostgreSQL RLS to ensure complete data isolation:

```sql
-- Enable RLS on all tenant tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY tenant_isolation_policy ON users
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- Set tenant context
SET app.current_tenant_id = '<tenant-uuid>';
```

### Database-Per-Tenant Mode

Each tenant gets a dedicated database:
- Complete isolation at infrastructure level
- Independent backups and scaling
- Higher resource requirements

## 💳 Billing Integration

### Stripe Setup

1. Create a Stripe account
2. Set up products and prices in Stripe Dashboard
3. Configure webhook endpoint: `https://yourdomain.com/api/v1/webhooks/stripe`
4. Add webhook secret to environment variables

### Supported Events
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.paid`
- `invoice.payment_failed`
- `payment_method.attached`

## 👥 RBAC System

### Default Roles

1. **Super Admin** (Platform-level)
   - Full system access
   - Tenant management
   - System configuration

2. **Tenant Admin** (Tenant-level)
   - Full tenant access
   - User management
   - Billing management

3. **Manager**
   - Team management
   - Content creation
   - Report access

4. **Staff**
   - Limited write access
   - Basic operations

5. **Member**
   - Read-only access

### Custom Roles

```python
# Create custom role via API
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

## 📊 Monitoring & Logging

### Structured Logging

```python
logger.info(
    "User login successful",
    extra={
        "tenant_id": tenant.id,
        "user_id": user.id,
        "ip_address": request.client.host,
        "user_agent": request.headers.get("user-agent")
    }
)
```

### Audit Logs

All critical actions are logged:
- User authentication
- Permission changes
- Billing events
- Data modifications

## 🚢 Deployment

### Docker Production

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes

```bash
kubectl apply -f kubernetes/
```

### Terraform (AWS)

```bash
cd terraform/aws
terraform init
terraform plan
terraform apply
```

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest tests/ -v --cov=app

# Frontend tests
cd frontend
npm test

# E2E tests
npm run test:e2e
```

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

## 🆘 Support

- Documentation: [docs/](docs/)
- Issues: GitHub Issues
- Email: support@yoursaas.com

## 🗺 Roadmap

- [ ] GraphQL API support
- [ ] Multi-language support (i18n)
- [ ] Advanced analytics dashboard
- [ ] Mobile app (React Native)
- [ ] WebSocket real-time features
- [ ] Advanced workflow automation
- [ ] Third-party integrations marketplace

---

**Built with ❤️ for the SaaS community**
