# ZBook ↔ Mac Studio Setup Instructions

## 1. Test SSH from the Mac Studio

```bash
ssh seanfilipow@192.168.86.33
```

**SSH fingerprint prompt:** Just type `yes` — you're on your own local network, no risk.

## 2. SSH Password Issue

The ZBook uses an Azure AD account (`azuread\seanfilipow`), not a local account, so password-based SSH won't work directly.

**Fix: Set up SSH key-based auth.**

### On the Mac Studio:

Check if you already have a key:
```bash
ls ~/.ssh/*.pub
```

If no key exists, generate one:
```bash
ssh-keygen -t ed25519 -C "studio@defiant"
```
Hit Enter through all prompts (no passphrase needed for local network).

### Copy the public key to the ZBook:

Display the key on the Studio:
```bash
cat ~/.ssh/id_ed25519.pub
```

On the ZBook (admin PowerShell), paste it into the authorized_keys file:
```powershell
# For Azure AD accounts, use the administrators_authorized_keys file:
Add-Content -Path "C:\ProgramData\ssh\administrators_authorized_keys" -Value "PASTE_KEY_HERE"

# Fix permissions:
icacls "C:\ProgramData\ssh\administrators_authorized_keys" /inheritance:r /grant "SYSTEM:(F)" /grant "Administrators:(F)"
```

Then retry from the Studio:
```bash
ssh seanfilipow@192.168.86.33
```

## 3. Test Ollama from the Mac Studio

Once SSH works (or even without it — Ollama uses HTTP, not SSH):

```bash
curl http://192.168.86.33:11434/api/generate \
  -d '{"model": "llama3.1", "prompt": "Hello", "stream": false}'
```

**Note:** Ollama needs to be running on the ZBook and listening on `0.0.0.0` (not just localhost). If the curl fails, check on the ZBook:
- Is Ollama running? (`ollama list` in a terminal)
- Set `OLLAMA_HOST=0.0.0.0` environment variable so it listens on all interfaces, then restart Ollama.
