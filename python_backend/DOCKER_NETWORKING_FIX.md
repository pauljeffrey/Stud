# Docker Networking/DNS Fix for Windows

If you're experiencing DNS resolution errors (`[Errno -2] Name or service not known`), follow these steps:

## Quick Fixes (Try in order)

### 1. Restart Docker Desktop
- Close Docker Desktop completely
- Restart it
- Try running `docker-compose up` again

### 2. Check Docker Desktop DNS Settings
1. Open Docker Desktop
2. Go to **Settings** → **Docker Engine**
3. Add or verify DNS configuration:
```json
{
  "dns": ["8.8.8.8", "8.8.4.4", "1.1.1.1"]
}
```
4. Click **Apply & Restart**

### 3. Test Docker Network Connectivity
Run this command to test if Docker can resolve DNS:
```bash
docker run --rm alpine ping -c 3 8.8.8.8
docker run --rm alpine nslookup supabase.co
```

### 4. Check Windows DNS Settings
1. Open **Network Settings** → **Change adapter options**
2. Right-click your network adapter → **Properties**
3. Select **Internet Protocol Version 4 (TCP/IPv4)** → **Properties**
4. Ensure "Obtain DNS server address automatically" is selected, OR
5. Manually set DNS to: `8.8.8.8` and `8.8.4.4`

### 5. Use Host Network Mode (Windows-specific workaround)
If DNS still fails, try using host network mode in `docker-compose.yml`:
```yaml
services:
  backend:
    # ... other config ...
    network_mode: "host"  # Add this line
    # Remove the networks section if using host mode
```

**Note**: Host mode on Windows uses WSL2 networking, which may have different behavior.

### 6. Check Corporate Firewall/Proxy
If you're on a corporate network:
- Check if a proxy is required
- Configure Docker Desktop proxy settings: **Settings** → **Resources** → **Proxies**
- Add proxy configuration if needed

### 7. WSL2 Backend (if using WSL2)
If using WSL2:
```bash
# Check WSL2 DNS
cat /etc/resolv.conf

# Update WSL2 DNS if needed
sudo bash -c 'echo "nameserver 8.8.8.8" > /etc/resolv.conf'
sudo bash -c 'echo "nameserver 8.8.4.4" >> /etc/resolv.conf'
```

### 8. Alternative: Use IP Address (Temporary)
As a last resort, you can temporarily use Supabase's IP address:
1. Find Supabase IP: `nslookup ymwruvfjaooficxjemxt.supabase.co`
2. Update `.env` with IP (not recommended for production)

## Verify Fix
After applying fixes, rebuild and test:
```bash
docker-compose down
docker-compose up --build
```

The connection should now work. If not, check the error messages for more details.
