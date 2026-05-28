from untamed_companion.graph import GraphRuntime, build_chat_graph, build_emotion_graph
from untamed_companion.graph.greeting_graph import build_greeting_graph
from untamed_companion.graph.state import ChatState, EmotionState
from untamed_companion.prompts import DefaultPromptProvider, StaticPromptProvider


class PromptEchoChatResponder:
    async def generate_chat_response(self, state: ChatState) -> str:
        return state.get("system_prompt", "")


class PromptEchoGreetingResponder:
    async def generate_greeting(self, state: ChatState) -> str:
        return state.get("system_prompt", "")


class PromptEchoEmotionAnalyzer:
    async def analyze_emotion(self, state: EmotionState) -> dict[str, object]:
        return {
            "primary_emotion": "calm",
            "color_hex": "#8ecae6",
            "summary_text": state.get("system_prompt", ""),
            "key_quote": "",
        }


def test_default_prompt_provider_is_neutral_and_contextual() -> None:
    prompt = DefaultPromptProvider().build_chat_prompt(
        {
            "companion": {"name": "Luna"},
            "user_name": "Min",
            "user_lang": "en",
            "weather_info": "Clear",
            "recent_logs": [{"sender": "USER", "message": "hello"}],
        }
    )

    assert "Luna" in prompt
    assert "Min" in prompt
    assert "Clear" in prompt
    assert "Untamed" not in prompt


async def test_chat_graph_uses_prompt_provider() -> None:
    graph = build_chat_graph(
        runtime=GraphRuntime(
            chat_responder=PromptEchoChatResponder(),
            prompt_provider=StaticPromptProvider(chat_prompt="chat override"),
        )
    )
    result = await graph.ainvoke(
        {
            "companion_id": "demo",
            "last_user_message": "hello",
            "companion": {"name": "Luna"},
        }
    )

    assert result["system_prompt"] == "chat override"
    assert result["emit"][0]["content"] == "chat override"


async def test_greeting_graph_uses_prompt_provider() -> None:
    graph = build_greeting_graph(
        runtime=GraphRuntime(
            greeting_responder=PromptEchoGreetingResponder(),
            prompt_provider=StaticPromptProvider(greeting_prompt="greeting override"),
        )
    )
    result = await graph.ainvoke({"companion": {"name": "Luna"}})

    assert result["system_prompt"] == "greeting override"
    assert result["emit"][0]["content"] == "greeting override"


async def test_emotion_graph_uses_prompt_provider() -> None:
    graph = build_emotion_graph(
        runtime=GraphRuntime(
            emotion_analyzer=PromptEchoEmotionAnalyzer(),
            prompt_provider=StaticPromptProvider(emotion_prompt="emotion override"),
        )
    )
    result = await graph.ainvoke(
        {
            "companion_id": "demo",
            "logs": [{"sender": "USER", "message": "hello"}],
        }
    )

    assert result["system_prompt"] == "emotion override"
    assert result["new_summary"] == "emotion override"
