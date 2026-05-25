import requests
import re
import socket
import time
import concurrent.futures

def verify_egypt_connection(host, port, timeout=2.5):
    """فحص ذكي يحاكي إرسال حزمة بيانات حقيقية للتأكد من عدم قطعها من الـ DPI المصري"""
    try:
        start_time = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        
        # إرسال حزمة ترحيبية وهمية لمعرفة هل سيقوم الجدار الناري بقطع الاتصال فوراً أم لا
        sock.sendall(b"\x16\x03\x01\x00\xaa\x01\x00\x00\xa6\x03\x03") 
        sock.recv(1024) 
        
        end_time = time.time()
        sock.close()
        return int((end_time - start_time) * 1000)
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
        ping = verify_egypt_connection(host, port)
        if ping != float('inf'):
            return {'config': config, 'ping': ping}
    return None

def main():
    print("="*50)
    print("   🚀 V2Ray Local Scanner for Egypt (Stop at 20)   ")
    print("="*50)
    
    url = "https://raw.githubusercontent.com/ebrasha/free-v2ray-public-list/refs/heads/main/vless_configs.txt"
    
    print("📥 Loading servers from GitHub, please wait...")
    try:
        response = requests.get(url, timeout=10)
        all_configs = response.text.splitlines()
    except Exception as e:
        print(f"❌ Error downloading source list: {e}")
        input("\nPress Enter to exit...")
        return

    filtered = []
    for cfg in all_configs:
        if cfg.strip():
            if "security=reality" in cfg.lower() or "us" in cfg.lower():
                filtered.append(cfg.strip())
                
    total = len(filtered)
    print(f"🎯 Found {total} potential servers. Target: Find 20 WORKING servers.")
    print("⏳ Testing connectivity... Will stop automatically once 20 servers are found.")

    working_servers = []
    max_target = 20

    # استخدام إدارة مهام مرنة لإيقاف الفحص مبكراً
    with concurrent.futures.ThreadPoolExecutor(max_workers=60) as executor:
        # إرسال جميع المهام للخلفية
        futures = [executor.submit(check_server, cfg) for cfg in filtered]
        
        # معالجة النتائج فور خروجها (الأسرع فالأسرع)
        for future in concurrent.futures.as_completed(futures):
            # شرط أمان إضافي قبل قراءة النتيجة
            if len(working_servers) >= max_target:
                break
                
            res = future.result()
            if res:
                working_servers.append(res)
                print(f"  [WORKING] Ping: {res['ping']}ms | Progress: ({len(working_servers)}/{max_target})")
                
                # إذا وصلنا للعدد المطلوب، قم بإلغاء المهام المتبقية فوراً واكسر الحلقة
                if len(working_servers) >= max_target:
                    print("\n🎯 Target reached! Canceling remaining tasks...")
                    for f in futures:
                        f.cancel()
                    break

    # الترتيب النهائي للـ 20 سيرفر المستخرجين
    working_servers.sort(key=lambda x: x['ping'])

    if working_servers:
        with open("Egypt_Working_Servers.txt", "w", encoding="utf-8") as f:
            for srv in working_servers:
                f.write(srv['config'] + "\n")
        print("="*50)
        print(f"🏆 SUCCESS! Found exactly {len(working_servers)} working servers on your network.")
        print("💾 Saved from fastest to slowest in: Egypt_Working_Servers.txt")
        print("="*50)
    else:
        print("\n⚠️ No servers bypassed the local blocks this time.")
        
    input("\n🎯 Process finished. Press Enter to close...")

if __name__ == "__main__":
    main()
