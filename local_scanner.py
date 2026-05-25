import requests
import socket
import ssl
import time
import concurrent.futures
import urllib.parse
import threading
import sys

# الإعدادات
found_count = 0
max_target = 20
stop_event = threading.Event()
lock = threading.Lock()
output_file = "NetMod_Final_VIP_Servers.txt"

def is_valid_config(url):
    """فلترة السيرفرات الوهمية (تمنع السيرفرات التي بها UUID صفري)"""
    try:
        if "00000000-0000-4000-8000-000000000000" in url:
            return False
        return True
    except:
        return False

def parse_vless(url):
    try:
        main_part = url.split("://")[1]
        auth_host_port, rest = main_part.split("?", 1)
        _, host_port = auth_host_port.split("@")
        host, port_str = host_port.split(":")
        port = int(port_str)
        qs = urllib.parse.parse_qs(rest.split("#")[0])
        sni = qs.get("sni", [host])[0]
        return host, port, sni
    except:
        return None, None, None

def verify_connection(host, port, sni):
    """فحص مزدوج: TCP ثم TLS"""
    try:
        # 1. فحص TCP
        sock = socket.create_connection((host, port), timeout=3)
        # 2. فحص TLS
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        wrapped = context.wrap_socket(sock, server_hostname=sni)
        wrapped.do_handshake()
        wrapped.close()
        return True, "Success"
    except Exception as e:
        return False, str(e)

def check_server(config):
    global found_count
    if stop_event.is_set(): return
    
    if not is_valid_config(config): return

    host, port, sni = parse_vless(config)
    if not host: return

    # طباعة لحظية في الـ CMD
    with lock:
        print(f"[*] Testing: {host}:{port}")

    success, msg = verify_connection(host, port, sni)
    
    if success:
        with lock:
            if found_count < max_target:
                found_count += 1
                print(f"\n✅ [FOUND #{found_count}] -> {host}:{port}")
                with open(output_file, "a", encoding="utf-8") as f:
                    f.write(config + "\n")
                if found_count >= max_target:
                    stop_event.set()

def main():
    print("="*60)
    print("   🚀 FINAL NETMOD EGYPT SCANNER (PRO VERSION)   ")
    print("="*60)
    
    # تنظيف الملف القديم
    open(output_file, "w").close()
    
    url = "https://raw.githubusercontent.com/ebrasha/free-v2ray-public-list/refs/heads/main/vless_configs.txt"
    print("📥 Loading List...")
    try:
        configs = requests.get(url, timeout=10).text.splitlines()
    except:
        print("❌ Error loading list.")
        return

    filtered = [c for c in configs if c.strip() and ("security=tls" in c.lower() or "security=reality" in c.lower())]
    print(f"💎 Cleaned List: {len(filtered)} potential servers.\n" + "-"*60)

    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        executor.map(check_server, filtered)
        
    print(f"\n🎉 Done! {found_count} Valid Servers saved to {output_file}")
    input("Press Enter to close...")

if __name__ == "__main__":
    main()
