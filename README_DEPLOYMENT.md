# Running the Application in the Background

There are several ways to keep the Flask application running after you disconnect from the machine:

## Option 1: Using nohup (Simplest)

**Start the server:**
```bash
./start_server.sh
```

**Stop the server:**
```bash
./stop_server.sh
```

**View logs:**
```bash
tail -f server.log
```

## Option 2: Using screen (Good for interactive sessions)

**Start a screen session:**
```bash
screen -S victoria-house
source venv/bin/activate
python app.py
```

**Detach from screen:** Press `Ctrl+A` then `D`

**Reattach to screen:**
```bash
screen -r victoria-house
```

**List all screen sessions:**
```bash
screen -ls
```

## Option 3: Using tmux (Alternative to screen)

**Start a tmux session:**
```bash
tmux new -s victoria-house
source venv/bin/activate
python app.py
```

**Detach from tmux:** Press `Ctrl+B` then `D`

**Reattach to tmux:**
```bash
tmux attach -t victoria-house
```

## Option 4: Using systemd Service (Best for Production)

**1. Edit the service file:**
Replace `%USER%` and `%WORKDIR%` in `victoria-house-photos.service`:
```bash
sed -i "s|%USER%|$(whoami)|g; s|%WORKDIR%|$(pwd)|g" victoria-house-photos.service
```

**2. Copy service file to systemd:**
```bash
sudo cp victoria-house-photos.service /etc/systemd/system/
```

**3. Reload systemd:**
```bash
sudo systemctl daemon-reload
```

**4. Start the service:**
```bash
sudo systemctl start victoria-house-photos
```

**5. Enable auto-start on boot:**
```bash
sudo systemctl enable victoria-house-photos
```

**6. Check status:**
```bash
sudo systemctl status victoria-house-photos
```

**7. View logs:**
```bash
sudo journalctl -u victoria-house-photos -f
```

**8. Stop the service:**
```bash
sudo systemctl stop victoria-house-photos
```

## Option 5: Using Gunicorn (Production-ready)

For production, consider using Gunicorn instead of Flask's development server:

**1. Install Gunicorn:**
```bash
source venv/bin/activate
pip install gunicorn
```

**2. Create a Gunicorn config file (`gunicorn_config.py`):**
```python
bind = "0.0.0.0:5000"
workers = 2
timeout = 120
accesslog = "access.log"
errorlog = "error.log"
```

**3. Run with Gunicorn:**
```bash
source venv/bin/activate
gunicorn -c gunicorn_config.py app:app
```

Then use any of the above methods (nohup, screen, tmux, or systemd) to keep it running.

## Quick Reference

| Method | Best For | Pros | Cons |
|--------|----------|------|------|
| nohup | Quick testing | Simple | No easy reattachment |
| screen/tmux | Development | Easy reattachment | Manual management |
| systemd | Production | Auto-restart, boot startup | Requires sudo |
| Gunicorn + systemd | Production | Better performance | More setup |

## Recommended Approach

- **Development/Testing:** Use `screen` or `tmux` for easy reattachment
- **Production:** Use `systemd` service for automatic restarts and boot startup

