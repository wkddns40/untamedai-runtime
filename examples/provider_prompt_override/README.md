# Provider And Prompt Override

This example shows how a consumer application can provide its own model,
embedding, weather, and prompt policy objects without changing the runtime
package.

Run:

```bash
pip install -e ".[dev]"
python examples/provider_prompt_override/app.py
```

The example uses `GraphRuntime` with:

- an app-owned provider object
- an app-owned `PromptProvider`
- `InMemoryCompanionStore`
- the public chat graph builder
