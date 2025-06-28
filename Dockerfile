FROM python:3.12-slim

# Install OS-level dependencies for Playwright and Chromium
RUN apt-get update && apt-get install -y \
    wget gnupg unzip curl fonts-liberation \
    libnss3 libxss1 libasound2 libx11-xcb1 libatk-bridge2.0-0 \
    libgtk-3-0 libxcomposite1 libxdamage1 libxrandr2 \
    libgbm1 libpango-1.0-0 libcairo2 libatspi2.0-0 \
    libx11-dev libxext-dev libxrender-dev libxtst6 \
    && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and browsers
RUN playwright install --with-deps

# Copy bot code
COPY . .

# Set environment variables if needed
ENV PYTHONUNBUFFERED=1

# Run the bot
CMD ["python", "bot.py"]
