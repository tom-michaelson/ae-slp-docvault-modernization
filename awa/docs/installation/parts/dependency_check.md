:::info Dependency Check
To verify which dependencies you do not yet have, you can run `make install` directly. If any are not found, it will not proceed with the installation.

Also note that opening the repo root directory in VS Code (or Cursor) will automatically run `make install` for you. Check your terminal for the result.

```bash
============================================================
AWA Dependency Verification
============================================================
Platform: Windows 11
Architecture: AMD64

Checking dependencies...

Checking Python... ✅ Python 3.12.6 (>= 3.12.0)
Checking Node.js... ✅ Node.js 22.16.0 (>= 22.16.0)
Checking uv... ✅ uv 0.7.13 (>= 0.7.13)
Checking pnpm... ✅ pnpm 10.6.2 (>= 10.6.2)
Checking make... ✅ make 4.4 (>= 4.4)
Checking Temporal CLI... ✅ Temporal CLI 1.3.0 (>= 1.3.0)

============================================================
SUMMARY
============================================================
Dependencies checked: 6
Successful: 6
Failed: 0

✅ All dependencies are installed and meet requirements!
```

:::
