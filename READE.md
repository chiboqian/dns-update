# ZoneEdit Dynamic DNS Updater

Update ZoneEdit Dynamic DNS records programmatically with automatic public IP detection.

## Overview

This script updates one or more ZoneEdit Dynamic DNS records to point to your current public IPv4 address. It's useful for maintaining DNS records when your IP address changes (home servers, remote access, etc.).

## Requirements

- Python 3.7+
- `requests` library
- `pyyaml` library
- `python-dotenv` library

### Setup

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Authentication

You need two pieces of information from ZoneEdit:
1. **Username**: Your ZoneEdit account username
2. **Dynamic DNS Token**: A special token for dynamic DNS updates (NOT your account password)

To get your Dynamic DNS token:
1. Log in to ZoneEdit
2. Go to your domain's Dynamic DNS settings
3. Generate or copy your Dynamic DNS token

## Configuration Methods

The script supports four configuration methods (in priority order):

### 1. Command-Line Arguments (Highest Priority)
```bash
python3 util/update_zoneedit_ddns.py \
  --user YOUR_USERNAME \
  --token YOUR_TOKEN \
  --host home.example.com
```

### 2. .env File
Create a `.env` file in the project root (copy from `.env.example`):
```bash
cp .env.example .env
# Edit .env with your credentials
```

`.env` file format:
```
ZONEEDIT_USER=your_username
ZONEEDIT_TOKEN=your_token
ZONEEDIT_HOSTS=home.example.com,nas.example.com
```

Then run the script:
```bash
python3 util/update_zoneedit_ddns.py
```

The `.env` file is automatically loaded and will not be committed to git.

### 3. Environment Variables
```bash
export ZONEEDIT_USER="your_username"
export ZONEEDIT_TOKEN="your_token"
export ZONEEDIT_HOSTS="home.example.com,nas.example.com"

python3 util/update_zoneedit_ddns.py
```

### 4. YAML Configuration File (Lowest Priority)
Create `config/ZoneEdit.yaml`:
```yaml
user: your_username
token: your_token
hosts:
  - home.example.com
  - nas.example.com
```

Then run:
```bash
python3 util/update_zoneedit_ddns.py
```

Or specify a custom config path:
```bash
python3 util/update_zoneedit_ddns.py --config /path/to/config.yaml
```

## Usage Examples

### Basic: Update Single Host (Auto-detect IP)
```bash
python3 util/update_zoneedit_ddns.py \
  --user myuser \
  --token mytoken \
  --host home.example.com
```

### Update Multiple Hosts
```bash
python3 util/update_zoneedit_ddns.py \
  --user myuser \
  --token mytoken \
  --host home.example.com \
  --host nas.example.com \
  --host vpn.example.com
```

### Use Explicit IP Address
```bash
python3 util/update_zoneedit_ddns.py \
  --user myuser \
  --token mytoken \
  --host home.example.com \
  --ip 203.0.113.42
```

### Verbose Output
```bash
python3 util/update_zoneedit_ddns.py \
  --user myuser \
  --token mytoken \
  --host home.example.com \
  --verbose
```

### Quiet Mode (Errors Only)
```bash
python3 util/update_zoneedit_ddns.py \
  --user myuser \
  --token mytoken \
  --host home.example.com \
  --quiet
```

### Disable IP Auto-detection
Useful for testing or when you always want to provide explicit IP:
```bash
python3 util/update_zoneedit_ddns.py \
  --user myuser \
  --token mytoken \
  --host home.example.com \
  --ip 203.0.113.42 \
  --no-detect
```

## IP Auto-detection

When `--ip` is not specified, the script automatically detects your public IPv4 address using these services (in order):
1. https://api.ipify.org
2. https://ipv4.icanhazip.com
3. https://ifconfig.me/ip

If all services fail, the script exits with an error unless `--ip` is provided.

## Exit Codes

- `0`: All updates successful
- `1`: One or more updates failed
- `2`: Configuration error (missing credentials, missing hosts, etc.)

## Output Format

Standard output (unless `--quiet`):
```
[OK] host=home.example.com ip=203.0.113.42 http=200 body=OK
[FAIL] host=nas.example.com ip=203.0.113.42 http=401 body=Unauthorized
```

Verbose mode also prints detected IP:
```
Detected public IP: 203.0.113.42
[OK] host=home.example.com ip=203.0.113.42 http=200 body=OK
```

## Automation / Cron

### Run Every 5 Minutes
Add to crontab (`crontab -e`):
```cron
*/5 * * * * cd /Users/chiboqian/projects/AI_Trading && /usr/local/bin/python3 util/update_zoneedit_ddns.py --quiet >> /var/log/zoneedit_ddns.log 2>&1
```

### systemd Timer (Linux)
Create `/etc/systemd/system/zoneedit-ddns.service`:
```ini
[Unit]
Description=Update ZoneEdit Dynamic DNS

[Service]
Type=oneshot
User=your_user
WorkingDirectory=/Users/chiboqian/projects/AI_Trading
ExecStart=/usr/bin/python3 util/update_zoneedit_ddns.py --quiet
```

Create `/etc/systemd/system/zoneedit-ddns.timer`:
```ini
[Unit]
Description=Update ZoneEdit Dynamic DNS Timer

[Timer]
OnBootSec=2min
OnUnitActiveSec=5min

[Install]
WantedBy=timers.target
```

Enable and start:
```bash
sudo systemctl enable zoneedit-ddns.timer
sudo systemctl start zoneedit-ddns.timer
```

### macOS Launch Agent
Create `~/Library/LaunchAgents/com.zoneedit.ddns.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.zoneedit.ddns</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/Users/chiboqian/projects/AI_Trading/util/update_zoneedit_ddns.py</string>
        <string>--quiet</string>
    </array>
    <key>StartInterval</key>
    <integer>300</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/zoneedit-ddns.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/zoneedit-ddns.err</string>
</dict>
</plist>
```

Load:
```bash
launchctl load ~/Library/LaunchAgents/com.zoneedit.ddns.plist
```

## Troubleshooting

### "Error: ZoneEdit user/token required"
You haven't provided credentials via CLI, environment variables, or config file.

**Solution**: Set credentials using one of the configuration methods above.

### "Error: at least one --host is required"
No hostname was specified.

**Solution**: Add `--host yourhost.example.com` or configure hosts in env/config file.

### "Error: failed to auto-detect public IPv4"
All IP detection services failed (network issue or services down).

**Solution**: 
- Check your internet connection
- Use `--ip YOUR_IP` to specify IP manually
- Check that you can reach https://api.ipify.org in a browser

### "[FAIL] ... http=401 body=Unauthorized"
Invalid username or token.

**Solution**: 
- Verify you're using your Dynamic DNS token (not account password)
- Check for typos in username/token
- Regenerate token in ZoneEdit dashboard

### "[FAIL] ... http=0 body=request_error: ..."
Network connectivity issue or timeout.

**Solution**: 
- Check internet connection
- Increase timeout: `--timeout 30`
- Check firewall settings

### ZoneEdit Returns "nochg" But Shows as OK
This is normal. ZoneEdit returns "nochg" when the IP hasn't changed since last update. The script treats this as success.

## Command-Line Options

```
--user USER              ZoneEdit username
--token TOKEN            ZoneEdit dynamic DNS token
--host HOST              Hostname to update (can be repeated)
--ip IP                  Use this IP instead of auto-detecting
--config CONFIG          Path to YAML config file (default: config/ZoneEdit.yaml)
--timeout TIMEOUT        HTTP timeout in seconds (default: 10.0)
--no-detect              Error if --ip is missing instead of auto-detecting
-v, --verbose            Show detected IP and detailed output
-q, --quiet              Suppress non-error output
-h, --help               Show help message
```

## Security Notes

- **Never commit tokens to version control**. Add your config file to `.gitignore`:
  ```bash
  echo "config/ZoneEdit.yaml" >> .gitignore
  ```
- Use environment variables or a protected config file with restricted permissions:
  ```bash
  chmod 600 config/ZoneEdit.yaml
  ```
- The Dynamic DNS token has limited permissions (only DNS updates), but still treat it as sensitive.

## Related Links

- [ZoneEdit Dynamic DNS Documentation](https://zoneedit.com/doc/dynamic-dns/)
- [ZoneEdit Support](https://zoneedit.com/support/)
