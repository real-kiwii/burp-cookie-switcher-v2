# burp-cookie-switcher-v2
A lightweight Burp Suite extension for quickly switching authentication tokens while manually testing **BAC**.

## Features

* Cleaner UI
* Admin / User profiles
* Switch **Authorization Bearer**
* Switch **Cookie**
* Switch **CSRF header**
* Switch **Cookie + CSRF together**
* Switch all authentication headers at once
* Right-click **Switch to Admin / User**
* Hotkeys:

  * `Ctrl + Alt + A` → Admin
  * `Ctrl + Alt + U` → User
* Custom CSRF header name
* Settings are saved automatically

## Screenshots

![Cookie Switcher V2](./UI.png)

## How to Use

* Load `cookie_switcher_v2.py` in **Burp → Extensions**
* Open the **Cookie Switcher v2** tab
* Add Admin and User tokens
* Select which headers you want to switch
* In Repeater, right-click the request → **Switch to Admin/User**
* Or use the hotkeys

## Why

Authorization testing can produce false positives and often requires manually replacing tokens.

This extension makes manual **BAC testing faster** by switching authentication contexts in one click.
