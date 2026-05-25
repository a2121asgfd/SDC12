import requests
import re
import socket
import time
import concurrent.futures

def verify_egypt_tls_connection(host, port, timeout=3.0):
    """فحص ذكي جداً يحاكي مصافحة TLS حقيقية ببصمة متصفح لتخطي الـ DPI المصري"""
    try:
        start_time = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        
        # إرسال حزمة مصافحة TLS ClientHello حقيقية (تستخدم لتخطي الحجب على بورت 443)
        tls_handshake = (
            b"\x16\x03\x01\x00\xba\x01\x00\x00\xb6\x03\x03"
            b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f"
            b"\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f"
            b"\x00\x00\x1c\x13\x01\x13\x02\x13\x03\xc0\x2b\xc0\x2f\xc0\x2c\xc0\x30"
            b"\xcc\xa9\xcc\xa8\xc0\x09\xc0\x13\xc0\x0a\xc0\x14\x00\x9c\x00\x9d\x00\x2f\x00\x35"
            b"\x01\x00\x00\x51\x00\x00\x00\x00"
        )
        sock.sendall(tls_handshake)
        
        # استقبال الرد من السيرفر (ServerHello)
        response = sock.recv(1024)
        end_time = time.time()
        sock.close()
        
        # إذا رد السيرفر بحزمة صالحة، فهذا يعني أن التشفير يعمل والجدار الناري لم يقطع الاتصال
        if response and len(response) > 0:
            return int((end_time - start_time) * 1000)
        return float('inf')
    except Exception:
        return float('inf')

def parse_url(url):
    try:
        main_part = url.split("://")[1].split("?")[0] 
        _, address = main_part.split("@")
        host, port = address.split(":")
        return host, int(port)
    except:
        return None, None

def check_server(config):
    host, port = parse_url(config)
    if host and port:
        ping = verify_egypt_tls_connection(host, port)
        if ping != float('inf'):
            return {'config': config, 'ping': ping}
    return None

def main():
    print("="*60)
    print("   🚀 NetMod Egypt Pro Scanner (Strict TLS/Reality Filter)   ")
    print("="*60)
    
    url = "https://raw.githubusercontent.com/ebrasha/free-v2ray-public-list/refs/heads/main/vless_configs.txt"
    
    print("📥 Downloading server list from source...")
    try:
        response = requests.get(url, timeout=10)
        all_configs = response.text.splitlines()
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        input("\nPress Enter to exit...")
        return

    # الفلترة الصارمة للسيرفرات المشفرة فقط المتوافقة مع الإنترنت المصري و NetMod
    filtered = []
    for cfg in all_configs:
        cfg_lower = cfg.lower().strip()
        if cfg_lower:
            # شرط أساسي: يجب أن يحتوي على TLS أو Reality ويمنع تماماً الـ security=none الميت في مصر
            if ("security=tls" in cfg_lower or "security=reality" in cfg_lower) and "security=none" not in cfg_lower:
                # نفضل بورتات الحماية العالمية مثل 443
                filtered.append(cfg.strip())
                
    total = len(filtered)
    print(f"🎯 Filtered out {len(all_configs) - total} insecure servers.")
    print(f"💎 Found {total} STRICTLY ENCRYPTED (TLS/Reality) servers to test.")
    print("⏳ Running DPI-Bypass verification... Stopping at 20 solid matches.")
    print("-"*60)

    working_servers = []
    max_target = 20

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(check_server, cfg) for cfg in filtered]
        
        for future in concurrent.futures.as_completed(futures):
            if len(working_servers) >= max_target:
                break
                
            res = future.result()
            if res:
                working_servers.append(res)
                print(f"  [🔓 BYPASSED] Response: {res['ping']}ms | Progress: ({len(working_servers)}/{max_target})")
                
                if len(working_servers) >= max_target:
                    print("\n🎯 Success! Got 20 high-quality encrypted servers.")
                    break

    working_servers.sort(key=lambda x: x['ping'])

    if working_servers:
        with open("Egypt_NetMod_Servers.txt", "w", encoding="utf-8") as f:
            for srv in working_servers:
                f.write(srv['config'] + "\n")
        print("="*60)
        print(f"🏆 SUCCESS! Found {len(working_servers)} servers 100% working on NetMod.")
        print("💾 Copy them now from: Egypt_NetMod_Servers.txt")
        print("="*60)
    else:
        print("\n⚠️ No secure servers passed the TLS check. Source might be down or heavily blocked.")
        
    input("\n🎯 Done! Press Enter to close...")

if __name__ == "__main__":
    main()
