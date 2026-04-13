name: Market Analysis Bot

on:
  schedule:
    - cron: '10 21 * * *' # 한국시간 06:10
    - cron: '35 1 * * *'  # 한국시간 10:35
  workflow_dispatch:

jobs:
  run-bot:
    runs-on: ubuntu-latest
    env:
      FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true
      
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4
        
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          
      - name: Install Libraries
        run: |
          python -m pip install --upgrade pip
          pip install yfinance requests pandas pytz
        
      - name: Run Script
        env:
          TELEGRAM_TOKEN: ${{ secrets.TELEGRAM_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: python main.py
