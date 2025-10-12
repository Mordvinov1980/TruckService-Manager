# 🚀 Cloud Deployment Setup

This setup allows running the bot on cloud servers (VPS) for 24/7 operation.

## Required Files for Cloud Deployment

### 1. Environment Configuration
Create `.env` file on server:
BOT_TOKEN=your_telegram_bot_token_here
CHAT_ID=-1003145822387
DEBUG_MODE=False

text

### 2. Server Requirements
- Python 3.7+
- Git for cloning repository
- 512MB RAM minimum
- 10GB storage

## Deployment Commands

### Ubuntu/Debian Server:
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and Git
sudo apt install python3 python3-pip git -y

# Clone repository
git clone https://github.com/Mordvinov1980/TruckService-Manager.git
cd TruckService-Manager

# Install dependencies
pip3 install -r requirements.txt

# Create .env file
echo "BOT_TOKEN=your_bot_token" > .env
echo "CHAT_ID=-1003145822387" >> .env
echo "DEBUG_MODE=False" >> .env

# Run bot
python3 bot.py
iPhone Management
Recommended Apps:
Termius (SSH client) - connect to server

Telegram - test bot functionality

Basic iPhone Commands via Termius:
bash
# Connect to server
ssh username@server_ip

# Check if bot is running
ps aux | grep python

# Restart bot
pkill -f "python3 bot.py"
cd TruckService-Manager
python3 bot.py
Recommended Cloud Providers
Beepingeer - от 50 руб/месяц (специально для ботов)

Timeweb - от 150 руб/месяц

FirstVDS - от 190 руб/месяц

Ready for cloud deployment! 🚀
