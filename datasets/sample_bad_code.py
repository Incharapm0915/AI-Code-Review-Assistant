"""
Sample Bad Python Code — Used for testing the AI analysis engine.
Contains intentional vulnerabilities, bad practices, and code smells.
DO NOT use this code in production.
"""
import os
import pickle
import hashlib
import random
import subprocess

# Hardcoded credentials — CWE-798
DB_PASSWORD = "admin123"
SECRET = "mysecret"
API_KEY = "sk-1234567890abcdef"

# Global mutable state — bad practice
user_cache = {}
conn = None


def login(username, password):
    # SQL injection vulnerability — CWE-89
    query = "SELECT * FROM users WHERE username='" + username + "' AND password='" + password + "'"
    result = conn.execute(query)

    # Weak MD5 hashing — CWE-327
    hashed = hashlib.md5(password.encode()).hexdigest()

    # Insecure random for token — CWE-338
    token = random.randint(1000, 9999)

    return result, token


def run_report(report_name):
    # Command injection — CWE-78
    os.system("python reports/" + report_name + ".py")

    # Also bad
    subprocess.call("ls " + report_name, shell=True)


def load_user_prefs(data):
    # Insecure deserialization — CWE-502
    prefs = pickle.loads(data)
    return prefs


def process_uploaded_file(filename):
    # Path traversal — CWE-22
    f = open("/uploads/" + filename, 'r')
    content = f.read()
    # File handle never closed — resource leak
    return content


def calculate_score(values):
    # Magic numbers, no docstring
    x = 0
    for i in range(len(values)):   # Should use enumerate()
        x = x + values[i] * 1.337  # Magic number
    return x / 100 * 999           # More magic numbers


def send_email(user_input):
    # XSS via template injection
    template = "<html><body>Hello " + user_input + "</body></html>"

    # Eval with user input — CWE-95
    result = eval(user_input)
    return template, result


def get_user(id):
    # Not using parameterized query
    q = f"SELECT * FROM users WHERE id = {id}"
    r = conn.execute(q)

    # Bare except — swallows all exceptions
    try:
        data = r.fetchone()
    except:
        pass

    return data


def check_admin(u):
    # Insecure comparison, not constant-time
    if u['password'] == DB_PASSWORD:
        return True
    return False


def temp():
    # Single-char variable names, no docstring, does too many things
    a = []
    b = {}
    c = 0
    for x in range(100):
        for y in range(100):         # Nested loop O(n^2)
            c = c + x + y
            a.append(c)
            b[x] = y
    print(a)                         # Should use logging
    print(b)
    return c


# TODO: fix this later — FIXME: this is broken
def broken_function():
    pass


# Recursive function with no base case — stack overflow risk
def infinite_recurse(n):
    return infinite_recurse(n + 1)


# Unused imports at bottom (bad practice)
import sys
import json
import urllib
