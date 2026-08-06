#!/usr/bin/env python3
# write_files.py - writes TSX and CSS files for the IPF IPA React UI

import os

BASE = r"c:\Users\atulk1\.kiro\IPF-Intelligent Process Automation for Agents and Back office\ipf-ipa-react-ui\src\app"

# ============================================================
# globals.css
# ============================================================
globals_css = """\
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --foreground-rgb: 0, 0, 0;
  --background-start-rgb: 248, 250, 252;
}

body {
  color: rgb(var(--foreground-rgb));
  background: rgb(var(--background-start-rgb));
  font-family: Arial, Helvetica, sans-serif;
}

@layer utilities {
  .text-balance {
    text-wrap: balance;
  }
}
"""

with open(os.path.join(BASE, "globals.css"), "w", encoding="utf-8") as f:
    f.write(globals_css)

print("globals.css written")
