Based on your screenshot, your project is in /home/ubuntu on your AWS EC2 instance. Here is the final, corrected solution for deploying your chess server as a background service that auto-starts on reboot:

1. Check your Python venv and code location
Your code and venv are in /home/ubuntu.
Your main server file is: /home/ubuntu/server/server_main.py
Your venv Python is: /home/ubuntu/venv/bin/python3

2. Create/Edit the systemd service file
Run:

sudo nano /etc/systemd/system/chess-server.service

Paste this (adjust only if your username is not ubuntu):

[Unit]
Description=Multiplayer Chess Server
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu
ExecStart=/home/ubuntu/venv/bin/python3 -m server.server_main
Restart=always
Environment=PYTHONUNBUFFERED=1
Environment=PYTHONPATH=/home/ubuntu

[Install]
WantedBy=multi-user.target


Save and exit (Ctrl+O, Enter, Ctrl+X).

3. Reload systemd and start the service

sudo systemctl daemon-reload
sudo systemctl enable chess-server
sudo systemctl restart chess-server
sudo systemctl status chess-server
You should see active (running).

4. If you get any error
Double-check the paths in ExecStart and WorkingDirectory.
Make sure /home/ubuntu/venv/bin/python3 exists:
Make sure your code is in /home/ubuntu/server/server_main.py.

5. (Optional) View server logs
journalctl -u chess-server -f
Now your server will:

Run in the background
Restart on crash or reboot
Always be ready for new games
Let me know if you see any errors after these steps, or if the status is not "active (running)"!