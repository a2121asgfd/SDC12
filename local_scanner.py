import requests
import socket
import ssl
import time
import concurrent.futures
import urllib.parse
import threading
import sys

# إعدادات النظام
found_count = 0
max_target = 20
stop_event = threading.Event() # أداة لإيقاف جميع الفحوصات فوراً عند الوصول لـ 20
lock = threading.Lock() # أداة لتنظيم الطباعة والكتابة في الملف لكي لا تتداخل
output_file = "NetMod_VIP_Servers.txt"

def print_log(msg):
    """دالة لطباعة النصوص في الشاشة بشكل منظم دون تداخل"""
    with lock:
        print(msg)

def parse_vless(url):
    """تفكيك رابط الـ VLESS لاستخراج الـ IP والبورت والـ SNI المستخدم للتخفي"""
    try:
        main_part = url.split("://")[1]
        auth_host_port, rest = main_part.split("?", 1)
        query_part = rest.split("#")[0] if "#" in rest else rest
        
        _, host_port = auth_host_port.split("@")
        host, port_str = host_port.split(":")
        port = int(port_str)
        
        qs = urllib.parse.parse_qs(query_part)
        sni = qs.get("sni", [host])[0] # استخراج الـ SNI إن وجد، أو استخدام الـ Host
        security = qs.get("security", [""])[0]
        
        return host, port, sni, security
    except Exception:
        return None, None, None, None

def verify_real_tls(host, port, sni, timeout=3.5):
    """محاكاة دقيقة وحقيقية لاتصال NetMod لتخطي الحجب المصري"""
    # 1. فحص الاتصال العادي (هل البورت مفتوح؟)
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
    except socket.timeout:
        return False, "⏳ Error: TCP Timeout (Server is dead or blocked by DPI)"
    except ConnectionRefusedError:
        return False, "🚫 Error: Connection Refused (Port is closed)"
    except Exception as e:
        return False, f"❌ Error: Network failure ({str(e)})"

    # 2. فحص التشفير (هل الجدار الناري المصري سيقطع الاتصال عند بدء التشفير؟)
    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE # نحن فقط نريد التأكد أن التشفير يعمل
        
        wrapped_socket = context.wrap_socket(sock, server_hostname=sni)
        wrapped_socket.do_handshake() # بدء المصافحة المشفرة الحقيقية
        wrapped_socket.close()
        return True, "✅ TLS Handshake Success (DPI BYPASSED)"
    except Exception as e:
        sock.close()
        return False, f"🛡️ Error: SSL Handshake Blocked by DPI ({str(e)})"

def check_server(config):
    global found_count
    
    # إذا وصلنا لـ 20، تجاهل أي سيرفر جديد واخرج فوراً
    if stop_event.is_set():
        return
        
    host, port, sni, security = parse_vless(config)
    
    if not host:
        return
        
    print_log(f"[*] Scanning -> IP: {host} | Port: {port} | SNI: {sni}...")
    
    success, msg = verify_real_tls(host, port, sni)
    
    if success:
        with lock:
            if found_count >= max_target:
                stop_event.set()
                return
            
            found_count += 1
            # طباعة السيرفر الناجح بشكل بارز في الشاشة
            print("\n" + "="*60)
            print(f"🎉 [WORKING SERVER #{found_count}] Passed Egypt DPI Check!")
            print(f"🌐 Host: {host}:{port} | SNI: {sni} | Security: {security}")
            print(f"🔗 Config: {config}")
            print("="*60 + "\n")
            
            # الكتابة الفورية داخل الملف (بوضع a للإضافة أسفل بعض)
            try:
                with open(output_file, "a", encoding="utf-8") as f:
                    f.write(config + "\n")
            except Exception as e:
                print(f"[❌ FATAL ERROR] Could not save to TXT file: {e}")
                
            # إيقاف البرنامج إذا وصلنا للعدد
            if found_count >= max_target:
                print_log(f"\n🏆 TARGET REACHED: 20 Servers Found! Stopping the engine...")
                stop_event.set()
    else:
        # طباعة سبب الفشل لكي تعرف ماذا يحدث خلف الكواليس
        print_log(f"  [FAILED] {host}:{port} -> {msg}")


def main():
    print("="*70)
    print("   🚀 PROFESSIONAL EGYPT DPI SCANNER (NetMod Edition)   ")
    print("="*70)
    
    # تفريغ الملف القديم وبدء ملف جديد نظيف
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("")
        
    url = "https://raw.githubusercontent.com/ebrasha/free-v2ray-public-list/refs/heads/main/vless_configs.txt"
    print("\n📥 Fetching fresh servers from Github...")
    try:
        response = requests.get(url, timeout=10)
        all_configs = response.text.splitlines()
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        input("Press Enter to exit...")
        return

    # استخراج السيرفرات المشفرة فقط
    filtered = []
    for cfg in all_configs:
        cfg_lower = cfg.lower().strip()
        if cfg_lower:
            # شرط أساسي: التشفير مفعل ولا يوجد None
            if ("security=tls" in cfg_lower or "security=reality" in cfg_lower) and "security=none" not in cfg_lower:
                filtered.append(cfg.strip())

    print(f"💎 Valid Encrypted Servers Found: {len(filtered)}")
    print(f"⏳ Starting Deep Scan... Target: {max_target} Working Servers.\n")
    print("-" * 70)

    # تشغيل الفحص
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(check_server, cfg) for cfg in filtered]
        
        # ننتظر حتى ينتهي الفحص أو يتم الوصول للرقم 20 وإعطاء أمر التوقف
        for future in concurrent.futures.as_completed(futures):
            if stop_event.is_set():
                break

    print("\n" + "="*70)
    print(f"✅ PROCESS COMPLETE! Saved {found_count} Working Servers to:")
    print(f"📁 {output_file} (Check the folder where this program is running)")
    print("="*70)
    input("\n🎯 Press Enter to close...")

if __name__ == "__main__":
    main()
