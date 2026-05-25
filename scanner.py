import requests
import re
import socket
import time
import concurrent.futures

def get_tcp_ping(host, port, timeout=2.0):
    try:
        start_time = time.time()
        with socket.create_connection((host, port), timeout=timeout):
            end_time = time.time()
        return int((end_time - start_time) * 1000)
    except Exception:
        return float('inf')

def parse_vless_url(url):
    try:
        main_part = url.split("://")[1].split("?")[0] 
        _, address = main_part.split("@")
        host, port = address.split(":")
        return host, int(port)
    except:
        return None, None

def check_server(config):
    host, port = parse_vless_url(config)
    if host and port:
        ping = get_tcp_ping(host, port)
        if ping != float('inf'):
            return {'config': config, 'ping': ping}
    return None

def main():
    url = "https://raw.githubusercontent.com/ebrasha/free-v2ray-public-list/refs/heads/main/vless_configs.txt"
    country_code = "US" # يمكنك تغييرها لأي دولة
    
    print(f"📥 Fetching servers for country: {country_code}...")
    response = requests.get(url)
    all_configs = response.text.splitlines()
    
    filtered_configs = [
        cfg.strip() for cfg in all_configs 
        if cfg.strip() and (re.search(rf"\b{country_code}\b", cfg, re.IGNORECASE) or country_code.lower() in cfg.lower())
    ]
    
    print(f"🎯 Found {len(filtered_configs)} servers. Starting Ping test...")
    
    working_servers = []
    # استخدام 100 مسار لتسريع الفحص على سيرفرات جيت هاب
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        results = executor.map(check_server, filtered_configs)
        for res in results:
            if res:
                working_servers.append(res)
                
    # الترتيب من الأسرع للأبطأ
    working_servers.sort(key=lambda x: x['ping'])
    
    # حفظ النتيجة في ملف
    output_filename = "Best_Servers.txt"
    with open(output_filename, "w", encoding="utf-8") as f:
        for srv in working_servers:
            f.write(srv['config'] + "\n")
            
    print(f"✅ Finished! Saved {len(working_servers)} working servers to {output_filename}")

if __name__ == "__main__":
    main()
