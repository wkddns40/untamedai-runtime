# Upgrade To 1.0

`1.0.0` is the first stable release of the public runtime package. It does not
intentionally break `0.4.0` integrations.

## Upgrade Steps

1. Pin the new package version:

```bash
pip install "untamedai-runtime==1.0.0"
```

2. Install only the extras your application uses:

```bash
pip install "untamedai-runtime[fastapi]==1.0.0"
pip install "untamedai-runtime[openai]==1.0.0"
pip install "untamedai-runtime[supabase]==1.0.0"
pip install "untamedai-runtime[postgres]==1.0.0"
```

3. Keep rendering `end` events as completion markers. Do not display
   `end.content` as a second assistant chat bubble unless showing raw protocol
   events.

4. Keep production authorization in your app. The FastAPI router remains
   unauthenticated by default and expects application-owned `auth_hook` policy.

5. If you implement `CompanionStore`, provider protocols, or `PromptProvider`,
   continue treating state mappings and records as append-only. New optional
   fields may appear in minor releases.

## From 0.4.0

No application code changes are expected for standard `0.4.0` usage.

Notable stable declarations:

- SSE event contract is stable.
- Store/provider/prompt protocols are stable.
- FastAPI route factory API is stable.
- Breaking changes move to future major versions only.

Demo-only change:

- The demo scenario preset list now includes `coffee-ko` alongside
  `coffee-en`.

## From 0.3.x Or Earlier

Review the release notes for intermediate versions:

- [v0.4.0](releases/v0.4.0.md)
- [v0.3.1](releases/v0.3.1.md)
- [v0.2.0](releases/v0.2.0.md)

Important changes before `1.0.0`:

- FastAPI route factory settings were stabilized in `0.2.0`.
- Supabase and Postgres optional persistence helpers were hardened in `0.3.1`.
- Demo and troubleshooting docs were expanded in `0.4.0`.
