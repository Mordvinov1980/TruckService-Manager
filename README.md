# 🚛 TruckService Manager

A professional Telegram bot for truck service order management with automated document generation.

## 📋 Features

- **Automated Order Creation** - Generate service orders via Telegram
- **Professional Excel Documents** - Auto-generated order forms
- **Work & Materials Management** - Dynamic work lists and materials
- **Photo Integration** - Vehicle photos (front, right, left)
- **Accounting System** - Separate and common order tracking
- **Admin Panel** - Upload new work lists via Excel

## 🏗️ Architecture

- **Factory Pattern** - Document generation (`document_factory.py`)
- **Repository Pattern** - Data access abstraction (`data_repositories.py`)
- **Modular Structure** - Clean separation of concerns
- **Git Version Control** - Full change history and branch management

## 🔧 Technical Stack

- **Python 3.7+**
- **pyTelegramBotAPI**
- **pandas & openpyxl** - Excel processing
- **Repository + Factory Patterns**

## 📁 Project Structure
TruckService_Manager/
├── bot.py # Main bot file
├── modules/ # Architecture modules
│ ├── excel_processor.py # Professional Excel generation
│ ├── data_repositories.py # Repository pattern for data
│ └── document_factory.py # Factory pattern for documents
├── patches/ # Experimental features
│ └── patch_file_upload.py # File upload functionality
├── Шаблоны/ # Excel templates (Templates/)
│ ├── works_list_mercedes.xlsx
│ ├── works_list_techosmotr.xlsx
│ ├── list_materials.xlsx
│ └── template_autoservice.xlsx
└── Documentation/
├── CURRENT_STATUS.md
├── PRINCIPLES.md
└── ЛОГИКА.txt

text

## 🚀 Quick Start

1. **Clone repository**
   ```bash
   git clone https://github.com/Mordvinov1980/TruckService-Manager.git
Install dependencies

bash
pip install -r requirements.txt
Configure environment

bash
# Create .env file with:
BOT_TOKEN=your_telegram_bot_token
Run the bot

bash
python bot.py
📊 Workflow
Start bot → Select section (Mercedes/Technical Service)

Enter data → License plate, date, order number, workers

Select works → From Excel database with norm-hours

Materials → Optional selection from materials list

Photos → 3 vehicle photos (front, right, left)

Documents → Professional Excel + text drafts via Factory

Accounting → Save to separate and common accounting

🔧 Development
DEBUG Mode: Test without saving to accounting

Experimental Features: Use experimental_runner.py

Git Branches: Safe experimentation with branches

📄 License
This project is for internal use of truck service management.

🚀 Developed with modern architecture patterns and version control
