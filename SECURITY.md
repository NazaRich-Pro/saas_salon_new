# Security Policy & OWASP Compliance

## Overview

BeautyHub SaaS implements security best practices based on OWASP Top 10 2021 and industry standards.

## OWASP Top 10 2021 Compliance

### ✅ A01:2021 – Broken Access Control

**Implementation:**
- ✅ Role-based access control (RBAC) with 5 roles
- ✅ Tenant isolation via middleware
- ✅ Permission checks on all API endpoints
- ✅ JWT authentication with httpOnly cookies
- ✅ Refresh token rotation
- ✅ Device session tracking
- ✅ 2FA (TOTP) for admin roles

**Code:**
```python
# apps/tenants/permissions.py
class IsTenantAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and \
               request.membership.role == 'SALON_ADMIN'
```

### ✅ A02:2021 – Cryptographic Failures

**Implementation:**
- ✅ Passwords hashed with bcrypt (Django default)
- ✅ JWT secrets in environment variables
- ✅ HTTPS enforced (HSTS headers)
- ✅ Database backups encrypted (AES-256-CBC)
- ✅ Sensitive data not logged
- ✅ 2FA secrets encrypted

**Backup Encryption:**
```bash
gzip backup.sql | openssl enc -aes-256-cbc -salt -pbkdf2 \
    -pass pass:"$ENCRYPTION_PASSWORD" > backup.sql.gz.enc
```

### ✅ A03:2021 – Injection

**Implementation:**
- ✅ Django ORM (parameterized queries)
- ✅ Input validation with serializers
- ✅ CSRF protection enabled
- ✅ SQL injection prevention (no raw SQL)
- ✅ XSS protection headers
- ✅ Content Security Policy (CSP)

**Code:**
```python
# All queries use ORM
Appointment.objects.filter(tenant=request.tenant, status='CONFIRMED')

# Serializer validation
class AppointmentSerializer(serializers.ModelSerializer):
    def validate_start_at(self, value):
        if value < timezone.now():
            raise ValidationError("Cannot book in the past")
        return value
```

### ✅ A04:2021 – Insecure Design

**Implementation:**
- ✅ Multi-tenant architecture with isolation
- ✅ Advisory locks for double-booking prevention
- ✅ Rate limiting on auth endpoints
- ✅ Trial lifecycle management
- ✅ Graceful degradation
- ✅ Input validation at multiple layers

### ✅ A05:2021 – Security Misconfiguration

**Implementation:**
- ✅ Security headers middleware
- ✅ DEBUG=False in production
- ✅ Secrets in environment variables
- ✅ ALLOWED_HOSTS configured
- ✅ CORS properly configured
- ✅ Default admin URL changed
- ✅ Error messages sanitized

**Security Headers:**
```python
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000
Content-Security-Policy: default-src 'self'
```

### ✅ A06:2021 – Vulnerable and Outdated Components

**Implementation:**
- ✅ Dependencies pinned in requirements.txt
- ✅ Regular updates via Dependabot
- ✅ No known vulnerable packages
- ✅ Docker base images updated

**Dependency Management:**
```txt
Django==5.0.0
djangorestframework==3.14.0
celery==5.3.4
# All with specific versions
```

### ✅ A07:2021 – Identification and Authentication Failures

**Implementation:**
- ✅ JWT with refresh token rotation
- ✅ 2FA (TOTP) for admins
- ✅ Password strength requirements
- ✅ Account lockout after 5 failed attempts
- ✅ Session management (logout-all)
- ✅ Rate limiting on login (5 per 5 min)
- ✅ No default credentials

**Rate Limiting:**
```python
'/api/auth/login': {'requests': 5, 'window': 300}  # 5 per 5 min
'/api/auth/register': {'requests': 3, 'window': 3600}  # 3 per hour
```

### ✅ A08:2021 – Software and Data Integrity Failures

**Implementation:**
- ✅ Code signing (Git commits)
- ✅ CI/CD pipeline verification
- ✅ Backup integrity checks
- ✅ No unsigned dependencies
- ✅ Audit logging for critical actions

**Backup Verification:**
```bash
openssl enc -d -in backup.sql.gz.enc | gzip -t
# Returns 0 if integrity OK
```

### ✅ A09:2021 – Security Logging and Monitoring Failures

**Implementation:**
- ✅ Audit log for all critical actions
- ✅ Login attempts tracked
- ✅ Failed authentication logged
- ✅ Payment actions logged
- ✅ Export actions logged
- ✅ Celery health checks
- ✅ Error tracking (Sentry integration ready)

**Audit Log:**
```python
AuditLog.objects.create(
    action='PAYMENT',
    entity_type='Payment',
    entity_id=payment.id,
    user=request.user,
    tenant=request.tenant,
    ip_address=get_client_ip(request),
    metadata={'amount': payment.amount_kgs}
)
```

### ✅ A10:2021 – Server-Side Request Forgery (SSRF)

**Implementation:**
- ✅ No user-controlled URLs
- ✅ Webhook URLs validated
- ✅ Internal services not exposed
- ✅ Network segmentation (Docker)

---

## Additional Security Measures

### Rate Limiting

**Endpoints Protected:**
```python
/api/auth/login          → 5 req/5min per IP
/api/auth/register       → 3 req/hour per IP
/api/onboarding/*        → 5 req/hour per IP
/api/public/*            → 100 req/min per IP
```

### Database Security

- ✅ Encrypted backups (AES-256-CBC)
- ✅ 14-day retention
- ✅ Automated daily backups (2 AM)
- ✅ Restore script with verification
- ✅ No SQL injection (ORM only)
- ✅ Connection pooling
- ✅ Prepared statements

### Network Security

- ✅ HTTPS only (HSTS)
- ✅ TLS 1.2+ minimum
- ✅ Docker network isolation
- ✅ Firewall rules (ports 80/443 only)
- ✅ No root containers

### Data Privacy

- ✅ GDPR considerations
- ✅ Data export (user's own data)
- ✅ Data deletion (tenant cancellation)
- ✅ Audit trail (who accessed what)
- ✅ Tenant data isolation

---

## Security Headers

All responses include:

```http
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; ...
Permissions-Policy: geolocation=(), microphone=(), camera=()
```

---

## Backup & Disaster Recovery

### Automated Backups

**Schedule:** Daily at 2 AM UTC

**Process:**
1. `pg_dump` full database
2. Compress with gzip
3. Encrypt with AES-256-CBC
4. Store in `/backups/postgres/`
5. Verify integrity
6. Clean old backups (14-day retention)

**Encryption:**
```bash
# Backup
./infra/scripts/backup.sh

# Restore
./infra/scripts/restore.sh /backups/postgres/backup_20251012_020000.sql.gz.enc

# Test
./infra/scripts/test_backup.sh
```

### Recovery Time Objective (RTO)

- **Database restore:** ~5-10 minutes (depends on size)
- **Application recovery:** ~2 minutes (container restart)
- **Total RTO:** ~15 minutes

### Recovery Point Objective (RPO)

- **Max data loss:** 24 hours (daily backups)
- **For critical systems:** Consider hourly backups

---

## Incident Response

### Security Incident Process

1. **Detection:** Monitoring alerts, audit logs
2. **Containment:** Block attacker, isolate affected systems
3. **Eradication:** Remove threat, patch vulnerabilities
4. **Recovery:** Restore from backups if needed
5. **Lessons Learned:** Update security measures

### Contact

Security issues: security@saas.akylman.online (configure in production)

---

## Security Checklist for Deployment

### Pre-Production

- [ ] Change all default passwords
- [ ] Set strong `JWT_ACCESS_SECRET` and `JWT_REFRESH_SECRET`
- [ ] Set strong `BACKUP_ENCRYPTION_PASSWORD`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set `DEBUG=False`
- [ ] Configure SMTP for email notifications
- [ ] Set up Sentry for error tracking
- [ ] Configure firewall (ports 80/443 only)
- [ ] Enable HTTPS with valid TLS certificate
- [ ] Test backup/restore process
- [ ] Configure log retention
- [ ] Set up monitoring alerts

### Post-Deployment

- [ ] Verify security headers (securityheaders.com)
- [ ] Run security scan (OWASP ZAP)
- [ ] Test rate limiting
- [ ] Verify audit logging
- [ ] Test 2FA functionality
- [ ] Review user permissions
- [ ] Check for exposed secrets
- [ ] Verify CORS configuration
- [ ] Test backup notifications
- [ ] Schedule regular security reviews

---

## Reporting Security Vulnerabilities

If you discover a security vulnerability, please:

1. **Do NOT** create a public GitHub issue
2. Email security@saas.akylman.online with details
3. Include steps to reproduce
4. Allow reasonable time for response
5. We will acknowledge within 48 hours

---

## Security Updates

We regularly update dependencies and apply security patches. Subscribe to:

- GitHub Security Advisories
- Django Security Releases
- OWASP Newsletters

---

## Compliance

### Standards

- ✅ OWASP Top 10 2021
- ✅ PCI DSS Level 4 (payment handling)
- ✅ GDPR considerations
- ✅ SOC 2 Type II ready

### Certifications

- [ ] SOC 2 Type II (planned)
- [ ] ISO 27001 (planned)

---

## Regular Security Tasks

### Daily
- ✅ Automated backups
- ✅ Health checks
- ✅ Log monitoring

### Weekly
- [ ] Review audit logs
- [ ] Check failed login attempts
- [ ] Review rate limit hits

### Monthly
- [ ] Update dependencies
- [ ] Security patch review
- [ ] Backup restore test
- [ ] Access control audit

### Quarterly
- [ ] Penetration testing
- [ ] Security training
- [ ] Incident response drill
- [ ] Third-party security audit

---

Last Updated: 2025-10-12
Version: 1.0

