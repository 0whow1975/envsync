# envsync

> Utility to diff and sync `.env` files across environments with secret masking support.

---

## Installation

```bash
pip install envsync
```

Or with `pipx` for isolated installs:

```bash
pipx install envsync
```

---

## Usage

**Diff two `.env` files:**

```bash
envsync diff .env.development .env.production
```

**Sync missing keys from one environment to another:**

```bash
envsync sync .env.development .env.production
```

**Mask secrets when outputting diffs:**

```bash
envsync diff .env.development .env.production --mask-secrets
```

Example output:

```
[+] DB_HOST        only in .env.production
[-] DEBUG          only in .env.development
[~] API_KEY        value differs  (masked)
```

**Options:**

| Flag              | Description                          |
|-------------------|--------------------------------------|
| `--mask-secrets`  | Redact sensitive values in output    |
| `--export`        | Write synced result to a new file    |
| `--dry-run`       | Preview changes without writing      |

---

## License

This project is licensed under the [MIT License](LICENSE).

---

*Contributions welcome. Open an issue or submit a pull request.*