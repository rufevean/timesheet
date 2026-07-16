# Timesheet Automation

Automates timesheet submission via Appium + Selenium.  
**For educational purposes only. Never use in production. Never make warlords angry (in-game btw). Never disrespect the mighty TCS policies.**

---

## Prerequisites

Before running, install all of the following.

### 1. Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Node.js + Appium

Appium runs as a local server. Install it globally via npm:

```bash
npm install -g appium
appium driver install uiautomator2
```

> Verify: `appium --version`

### 3. ADB (Android Debug Bridge)

```bash
brew install android-platform-tools
```

> Verify: `adb version`

### 4. Microsoft Edge + EdgeDriver

- Install [Microsoft Edge](https://www.microsoft.com/edge) if not already present.
- Selenium 4 manages EdgeDriver automatically — no manual download needed.

### 5. Enable Wireless Debugging on your Android phone

1. Go to **Settings → About Phone** and tap **Build Number** 7 times to enable Developer Options.
2. Go to **Settings → Developer Options → Wireless Debugging** and turn it on.
3. Make sure your phone and Mac are on the **same Wi-Fi network**.

---

## Setup

### 1. Copy the example env file

```bash
cp .env.example .env
```

### 2. Fill in your credentials in `.env`

```env
# Your device's IP address (Settings → Wi-Fi → tap your network)
DEVICE_IP=192.168.x.x

# Your phone model (Settings → About Phone → Model name)
DEVICE_NAME=SM-XXXXXXX

# Your employee ID used to log in to ultimatix.net
EMPLOYEE_ID=your_employee_id

# Your Android screen unlock PIN
DEVICE_UNLOCK_PIN=your_device_pin

# Your TCS TOTP app PIN
TOTP_APP_PIN=your_totp_pin
```

> The rest of the values in `.env` (Appium host/port, URLs, element IDs) are
> pre-filled and don't need to change unless your setup differs.

---

## Run

```bash
python3 phone_connect.py
```

This single command runs the full pipeline:

1. **Discovers** your Android device over mDNS (`dns-sd`)
2. **Connects** ADB over Wi-Fi
3. **Starts** the Appium server and waits until it's ready
4. **Launches** `timesheet.py`, which:
    - Opens ultimatix.net in Edge
    - Uses Appium to read the TOTP auth code from your phone
    - Fills and submits the timesheet

---

## Project Structure

```
timesheet/
├── phone_connect.py   # Master pipeline (run this)
├── authautomate.py    # Appium: reads TOTP code from phone
├── timesheet.py       # Selenium: submits timesheet on ultimatix.net
├── .env               # Your secrets — never commit this
├── .env.example       # Safe template to share
├── requirements.txt   # Python dependencies
└── .gitignore
```
