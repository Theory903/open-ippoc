# ☁️ Global Access Guide: IPPOC-OS via Cloudflare Tunnel

This guide explains how to expose your **IPPOC-OS Node** to the public internet securely using [Cloudflare Tunnel](https://www.cloudflare.com/products/tunnel/). This allows you to access your AI from anywhere (e.g., `https://my-ippoc.com`) without opening dangerous ports on your router.

---

## 🏗️ Architecture
Instead of your AI living *on* Cloudflare (which can't run heavy GPUs), your AI lives on your machine (Local or VPS), and **Cloudflare acts as the secure doorway**.

`[You (Anywhere)]  <-->  [Cloudflare Edge]  <==Tunnel==>  [IPPOC Node (Your PC)]`

---

## 🚀 Step 1: Install Cloudflare Tunnel (`cloudflared`)

### On macOS (Your Machine)
```bash
brew install cloudflare/cloudflare/cloudflared
```

### On Linux (Server)
```bash
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb
```

---

## 🔑 Step 2: Authenticate & Create Tunnel

1.  **Login to Cloudflare:**
    ```bash
    cloudflared tunnel login
    ```
    *Select your domain (e.g., `example.com`) in the browser window.*

2.  **Create a Tunnel Identity:**
    ```bash
    cloudflared tunnel create ippoc-tunnel
    ```
    *Copy the `Tunnel-UUID` (e.g., `f2b3c4d5-...`) from the output.*

3.  **Route DNS to Tunnel:**
    *Map `ai.example.com` to your tunnel.*
    ```bash
    cloudflared tunnel route dns ippoc-tunnel ai
    ```

---

## ⚙️ Step 3: Configure the Tunnel

Create a configuration file `deploy/cloudflared_config.yml`:

```yaml
tunnel: <Your-Tunnel-UUID>
credentials-file: /Users/abhishekjha/.cloudflared/<Your-Tunnel-UUID>.json

ingress:
  # 1. IPPOC Node API (HTTP/WebSocket)
  # This makes your API accessible at https://ai.example.com
  - hostname: ai.example.com
    service: http://localhost:8080

  # Default catch-all
  - service: http_status:404
```

---

## 🏃 Step 4: Launch the Tunnel

Run this alongside your IPPOC Node:

```bash
cloudflared tunnel run --config deploy/cloudflared_config.yml ippoc-tunnel
```

---

## 🌐 Result
*   **API Access:** You can now send requests or open the dashboard at `https://ai.example.com`.
*   **Security:** Your home IP is hidden. Cloudflare handles DDoS protection.
*   **Auth:** You can add **Cloudflare Access** (Zero Trust) to put a Google/GitHub login screen in front of your AI for extra safety.
