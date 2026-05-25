import requests
import re
import socket
import time
import concurrent.futures

def verify_egypt_tls_connection(host, port, timeout=3.0):
    """فحص ذكي يحاكي مصافحة TLS حقيقية ببصمة متصفح لتخطي الـ DPI المصري"""
    try:
        start_time = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        
        # حزمة مصافحة TLS ClientHello لتخطي الحجب
        tls_handshake = (
            b"\x16\x03\x01\x00\xba\x01\x00\x00\xb6\x03\x03"
            b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f"
            b"\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f"
            b"\x00\x00\x1c\x13\x01\x13\x02\x13\x03\xc0\x2b\xc0\x2f\xc0\x2c\xc0\x30"
            b"\xcc\xa9\xcc\xa8\xc0\x09\xc0\x13\xc0\x0a\xc0\x14\x00\x9c\x00\x9d\x00\x2f\x00\x35"
            b"\x01\x00\x00\x51\x00\x00\x00\x00"
        )
        sock.sendall(tls_handshake)
        
        response = sock.recv(1024)
        end_time = time.time()
        sock.close()
        
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
    print("   🚀 NetMod Egypt Live Scanner (Instant Save & CMD Show)   ")
    print("="*60)
    
    output_file = "Egypt_NetMod_Servers.txt"
    
    # تفريغ أو إنشاء الملف من جديد عند بدء تشغيل البرنامج
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("") 

    url = "https://raw.githubusercontent.com/ebrasha/free-v2ray-public-list/refs/heads/main/vless_configs.txt"
    
    print("📥 Downloading server list from source...")
    try:
        response = requests.get(url, timeout=10)
        all_configs = response.text.splitlines()
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        input("\nPress Enter to exit...")
        return

    # الفلترة الصارمة (TLS / Reality) المتوافقة مع مصر
    filtered = []
    for cfg in all_configs:
        cfg_lower = cfg.lower().strip()
        if cfg_lower:
            if ("security=tls" in cfg_lower or "security=reality" in cfg_lower) and "security=none" not in cfg_lower:
                filtered.append(cfg.strip())
                
    total = len(filtered)
    print(f"💎 Found {total} STRICTLY ENCRYPTED servers to test.")
    print(f"⏳ Starting live test... Will stop at 20. Check your folder for '{output_file}' right now!")
    print("-"*60)

    working_count = 0
    max_target = 20

    # بدء الفحص المتوازي
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(check_server, cfg) for cfg in filtered]
        
        # معالجة النتائج فور خروجها حية (الأسرع فالأسرع)
        for future in concurrent.futures.as_completed(futures):
            if working_count >= max_target:
                break
                
            try:
                res = future.result()
                if res:
                    working_count += 1
                    
                    # 1. طباعة تفاصيل السيرفر بالكامل في الـ CMD
                    print(f"\n[🔓 WORKING #{working_count}] Ping: {res['ping']}ms")
                    print(f"🔗 Config: {res['config']}")
                    print("-" * 50)
                    
                    # 2. استخراج وإضافة السيرفر فوراً في ملف الـ txt أسفل السيرفر السابق
                    with open(output_file, "a", encoding="utf-8") as f:
                        f.write(res['config'] + "\n")
                    
                    # التوقف الفوري عند الوصول للهدف
                    if working_count >= max_target:
                        print(f"\n🏆 Done! Successfully exported {max_target} top servers to {output_file}")
                        break
            except Exception:
                pass

    input("\n🎯 Process finished. Press Enter to close...")

if __name__ == "__main__":
    main()
