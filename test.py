import sys
import os
import django

print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Django version: {django.get_version()}")
