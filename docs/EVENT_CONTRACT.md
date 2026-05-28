# Event Contract

The SSE event contract is the public compatibility surface. Consumers should
handle unknown event fields conservatively and use `type` as the primary event
switch.

## Frame Format

Each frame is one SSE data frame:

```text
data: {"type": "stream", "content": "Hello"}
```

Payloads are JSON objects. The normalized public shape is:

```python
{
    "type": "stream",
    "content": "Hello",
    "intent": "chat",
    "emotion_color": "#8ecae6",
}
```

Only `type` and `content` are always present after normalization. `intent` and
`emotion_color` are optional.

## Event Types

| Type | Content | Extra Fields | Meaning |
| --- | --- | --- | --- |
| `stream` | Assistant text | none | Text to render in chat. |
| `end` | Final text, if supplied | `intent` | Stream completion marker. |
| `greeting` | Greeting text | none | First greeting response. |
| `name_reveal` | Companion name | none | Companion naming succeeded. |
| `user_name_set` | User display name | none | User intro was accepted. |
| `naming_prompt` | Prompt text | none | Runtime asks user to name the companion. |
| `coffee_request` | Coffee request copy | none | Coffee turn shortcut. |
| `error` | Error text | none | Stream failed. |

## Expected Sequences

### Regular Chat

```json
[
  {"type": "stream", "content": "Luna: I heard you, Min. You said: hello"},
  {
    "type": "end",
    "content": "Luna: I heard you, Min. You said: hello",
    "intent": "chat"
  }
]
```

### Companion Naming

```json
[
  {"type": "name_reveal", "content": "Luna"},
  {"type": "stream", "content": "You can call me Luna."},
  {"type": "end", "content": "You can call me Luna.", "intent": "naming"}
]
```

### User Intro

```json
[
  {"type": "user_name_set", "content": "Min"},
  {"type": "stream", "content": "Luna: I heard you, Min. You said: my name is Min"},
  {
    "type": "end",
    "content": "Luna: I heard you, Min. You said: my name is Min",
    "intent": "chat"
  }
]
```

### Coffee Turn

```json
[
  {"type": "coffee_request", "content": "I could use a warm cup of coffee."}
]
```

## Rendering Guidance

- Render `stream` and `greeting` as assistant-visible text.
- Treat `end` as a completion signal. Do not render its `content` as a second
  assistant message unless your UI intentionally displays raw protocol events.
- Use `name_reveal` and `user_name_set` to update local UI state.
- Display `coffee_request` as a command/event, not as a normal assistant chat
  turn, if your product distinguishes actions from messages.

## Golden Tests

Golden fixtures live in `tests/golden/fixtures`. The test helper merges adjacent
`stream` chunks and normalizes whitespace before diffing. This keeps event
contract failures readable while allowing implementation-level token chunking
to vary.
