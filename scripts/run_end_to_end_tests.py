#!/usr/bin/env python

import subprocess
import threading
import time
from playwright.sync_api import sync_playwright
import signal
from uvicorn import Config, Server
import os
import asyncio  # Added asyncio import

def is_port_in_use(port):
  print("Checking if web server is running on port 8000")
  result = subprocess.run(['lsof', '-i', f':{port}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  return result.stdout != b''

if is_port_in_use(8000):
  print("Port 8000 is in use. Is the server already running? If not, then you may need to kill the process that is using the port.")
  exit(1)

def run_app():
  config = Config("src.main:app", host="0.0.0.0", port=8000, reload=True, log_level='critical')
  server = Server(config)
  return server

print('Starting the web server')
app_server = run_app()

def run_server():
  try:
    app_server.run()  # Run the uvicorn server
  except asyncio.CancelledError:
    pass  # Suppress CancelledError during shutdown

server_thread = threading.Thread(target=run_server)  # Changed target to wrapped run
server_thread.start()

# wait a couple seconds for the server to come up
time.sleep(3)

print('Running the end-to-end tests')

# Replace the list command with a single string command
subprocess.run("ENVIRONMENT=test pytest end_to_end_tests/*", shell=True)

# Stop the web server
print('Stopping the web server')
app_server.should_exit = True
server_thread.join()
print('Web server has stopped')