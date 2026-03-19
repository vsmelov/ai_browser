# Bundled extensions (fork)

## What belongs here

| File / dir | Purpose |
|------------|--------|
| **bundled_extensions.json** | Config for browser build: extension ID → `external_crx` filename and version. Committed. |
| **bundled_extensions.json.example** | Template. Committed. |
| **agent-build/** | Unpacked extension (from `build_ponyai_extension.sh`). Generated, gitignored. |
| **agent-pack.crx** | Packed extension used by `bundled_extensions.json`. From `pack_agent_crx.sh`. Gitignored. |
| **agent.pem** | Your signing key (stable extension ID). Gitignored. |

## Remove (not used by fork)

- `bflpfmnmnokmjhmgnolecpppdbdophmk.crx` — old upstream ID
- `hdpfhemclmkffmggeohfogmmcicimkno.crx`, `hppcdefeenkjjbamdggkaaempenbljkn.crx` — other IDs, not in our config
- `agent-pack.pem` — key from “pack without key”; optional, if you only use `agent.pem`

Cleanup:
```bash
cd packages/browseros/resources/extensions
rm -f bflpfmnmnokmjhmgnolecpppdbdophmk.crx hdpfhemclmkffmggeohfogmmcicimkno.crx hppcdefeenkjjbamdggkaaempenbljkn.crx
# optionally: rm -f agent-pack.pem
```
