#!/usr/bin/env python3
"""Hapus blok 'zooshop' lama dari commands/animals.js (backup otomatis ke animals.js.bak).
Pakai:  cd ~/sambo-bot && python3 patch_animals.py"""
import re, shutil, sys
p = 'commands/animals.js'
s = open(p, encoding='utf-8').read()
m = re.search(r"\n  \{\n    name: 'zooshop'.*?\n  \},\n(?=\];)", s, re.S)
if not m:
    print("Blok zooshop tidak ditemukan (mungkin sudah dihapus)."); sys.exit(1)
shutil.copy(p, p + '.bak')
open(p, 'w', encoding='utf-8').write(s[:m.start()] + s[m.end():])
print("OK: blok zooshop lama dihapus. Backup: animals.js.bak")
