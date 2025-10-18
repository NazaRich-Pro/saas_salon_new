# DNS Configuration Guide

## Overview

BeautyHub SaaS requires proper DNS configuration to work correctly. You need to set up DNS records that point to your VPS server where the application is hosted.

## Prerequisites

- A registered domain name (e.g., `saas.akylman.online`)
- Access to your domain's DNS management panel
- Your VPS server's IP address

## Required DNS Records

### 1. Main Domain (A Record)

Point your main domain to your VPS IP:

```
Type: A
Name: @ (or saas.akylman.online)
Value: YOUR_VPS_IP
TTL: 300 (or default)
```

**Example:**
```
A    saas.akylman.online    203.0.113.10    300
```

### 2. Wildcard Subdomain (A Record)

This enables multi-tenancy with subdomains like `salon1.saas.akylman.online`, `salon2.saas.akylman.online`, etc.:

```
Type: A
Name: *
Value: YOUR_VPS_IP
TTL: 300 (or default)
```

**Example:**
```
A    *.saas.akylman.online    203.0.113.10    300
```

### 3. Traefik Dashboard (Optional)

If you want a dedicated subdomain for Traefik dashboard:

```
Type: CNAME
Name: traefik
Value: saas.akylman.online
TTL: 300
```

**Or as A record:**
```
A    traefik.saas.akylman.online    203.0.113.10    300
```

## DNS Provider Examples

### Cloudflare

1. Log in to Cloudflare dashboard
2. Select your domain
3. Go to "DNS" section
4. Click "Add record"

**Main domain:**
- Type: `A`
- Name: `@`
- IPv4 address: `YOUR_VPS_IP`
- Proxy status: DNS only (gray cloud)
- TTL: Auto

**Wildcard:**
- Type: `A`
- Name: `*`
- IPv4 address: `YOUR_VPS_IP`
- Proxy status: DNS only (gray cloud)
- TTL: Auto

⚠️ **Important:** Set proxy status to "DNS only" (not proxied) for SSL certificates to work properly with Let's Encrypt.

### Namecheap

1. Log in to Namecheap
2. Go to Domain List → Manage
3. Go to "Advanced DNS" tab

Add these records:

| Type | Host | Value | TTL |
|------|------|-------|-----|
| A Record | @ | YOUR_VPS_IP | 300 |
| A Record | * | YOUR_VPS_IP | 300 |

### GoDaddy

1. Log in to GoDaddy
2. Go to My Products → DNS
3. Click "Add" under DNS Records

**Main domain:**
- Type: `A`
- Host: `@`
- Points to: `YOUR_VPS_IP`
- TTL: 600 seconds

**Wildcard:**
- Type: `A`
- Host: `*`
- Points to: `YOUR_VPS_IP`
- TTL: 600 seconds

### DigitalOcean

1. Go to Networking → Domains
2. Select your domain

Add these records:

**Main domain:**
```
HOSTNAME: @
WILL DIRECT TO: YOUR_VPS_DROPLET (or IP)
TTL: 30 seconds
```

**Wildcard:**
```
HOSTNAME: *
WILL DIRECT TO: YOUR_VPS_DROPLET (or IP)
TTL: 30 seconds
```

## Verification

### Check DNS Propagation

Use these commands to verify DNS is set up correctly:

```bash
# Check main domain
dig saas.akylman.online +short
nslookup saas.akylman.online

# Check wildcard subdomain
dig demo.saas.akylman.online +short
nslookup demo.saas.akylman.online

# Check from multiple locations
# Visit: https://dnschecker.org/#A/saas.akylman.online
```

Both should return your VPS IP address.

### Online Tools

- **DNS Checker**: https://dnschecker.org/
- **What's My DNS**: https://whatsmydns.net/
- **DNS Propagation Checker**: https://www.whatsmydns.net/

## DNS Propagation Time

- **Typical time**: 5-30 minutes
- **Maximum time**: Up to 48 hours (rare)
- **TTL impact**: Lower TTL = faster propagation

💡 **Tip:** Set TTL to 300 seconds (5 minutes) before making changes for faster propagation.

## Testing After DNS Setup

Once DNS is configured and propagated:

1. **Test main domain:**
   ```bash
   curl -I https://saas.akylman.online
   ```

2. **Test subdomain:**
   ```bash
   curl -I https://demo.saas.akylman.online
   ```

3. **Test in browser:**
   - Visit `https://saas.akylman.online`
   - Visit `https://demo.saas.akylman.online`

## SSL Certificate Setup

Traefik will automatically obtain SSL certificates from Let's Encrypt once DNS is properly configured. This happens automatically when you start the services.

**Check certificate status:**
```bash
cd infra
docker compose logs traefik | grep -i "certificate"
```

**Certificate storage:**
Certificates are stored in `infra/letsencrypt/acme.json`.

## Troubleshooting

### DNS Not Resolving

1. Check if DNS records are correct:
   ```bash
   dig saas.akylman.online
   ```

2. Clear local DNS cache:
   ```bash
   # Linux
   sudo systemd-resolve --flush-caches
   
   # macOS
   sudo dscacheutil -flushcache
   
   # Windows
   ipconfig /flushdns
   ```

3. Wait for propagation (up to 48 hours)

### SSL Certificate Issues

1. Check Traefik logs:
   ```bash
   docker compose logs traefik
   ```

2. Verify DNS points to correct IP:
   ```bash
   dig saas.akylman.online +short
   ```

3. Ensure ports 80 and 443 are open:
   ```bash
   sudo ufw status
   ```

4. Delete old certificates and restart:
   ```bash
   rm infra/letsencrypt/acme.json
   docker compose restart traefik
   ```

### Subdomain Not Working

1. Verify wildcard A record exists:
   ```bash
   dig test.saas.akylman.online +short
   ```

2. Check Traefik routing:
   ```bash
   docker compose logs traefik | grep -i "router"
   ```

## Custom Domain (White-Label)

For custom tenant domains like `mysal on.com`:

1. Customer configures their DNS:
   ```
   Type: A or CNAME
   Name: @ or mysal on
   Value: YOUR_VPS_IP or saas.akylman.online
   ```

2. Add domain in BeautyHub admin panel (will be implemented in Stage 2)

3. Traefik will automatically obtain SSL certificate

## Security Notes

- ✅ Always use HTTPS (handled automatically by Traefik)
- ✅ Enable DNSSEC if your provider supports it
- ✅ Consider using Cloudflare for DDoS protection (optional)
- ⚠️ Don't use Cloudflare proxy mode with Let's Encrypt (use DNS only mode)

## Support

If you encounter DNS issues:

1. Check this guide's troubleshooting section
2. Verify with online DNS tools
3. Contact your DNS provider's support
4. Check Traefik and application logs

## Quick Reference

```bash
# View DNS records
dig saas.akylman.online ANY

# Test HTTPS
curl -I https://saas.akylman.online

# Check SSL certificate
echo | openssl s_client -servername saas.akylman.online -connect YOUR_VPS_IP:443 2>/dev/null | openssl x509 -noout -dates

# Monitor Traefik
docker compose logs -f traefik
```

---

**Need Help?** Refer to the [Deployment Guide](DEPLOYMENT.md) for complete setup instructions.

