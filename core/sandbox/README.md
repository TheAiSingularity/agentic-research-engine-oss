# `core/sandbox/` — HermesClaw integration glue

Import this module in a recipe's production tier and you get a working HermesClaw sandbox in one line:

```python
from core.sandbox import run_in_hermesclaw

run_in_hermesclaw(agent, policy="gateway")
```

## Scope

- Policy preset helpers (strict / gateway / permissive — mirroring HermesClaw's three policies)
- Compose-file generation
- Tool → policy mapping (which tools need what permissions)
- Diagnostics (what got blocked, why)

## Status

**Stub — lands in Wave 2.**

## See also

- [HermesClaw](https://github.com/TheAiSingularity/hermesclaw)
- [NVIDIA/OpenShell](https://github.com/NVIDIA/OpenShell)
