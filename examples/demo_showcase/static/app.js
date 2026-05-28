const companionId = "demo";

const nodes = {
  companionName: document.querySelector("#companionName"),
  userName: document.querySelector("#userName"),
  streamState: document.querySelector("#streamState"),
  chatLog: document.querySelector("#chatLog"),
  eventLog: document.querySelector("#eventLog"),
  metricsBox: document.querySelector("#metricsBox"),
  messageForm: document.querySelector("#messageForm"),
  messageInput: document.querySelector("#messageInput"),
  clearEvents: document.querySelector("#clearEvents"),
  signalCanvas: document.querySelector("#signalCanvas"),
  langButtons: document.querySelectorAll("[data-lang]"),
};

const eventCounts = new Map();
let currentLang = "en";

const scenarioText = {
  en: {
    hello: "hello",
    nameAi: "your name is Luna",
    userName: "my name is Min",
    coffee: "coffee",
  },
  ko: {
    hello: "안녕",
    nameAi: "네 이름은 루나",
    userName: "내 이름은 민",
    coffee: "커피",
  },
};

function appendMessage(text, kind = "ai") {
  const item = document.createElement("div");
  item.className = `message ${kind}`;
  item.textContent = text || "(empty)";
  nodes.chatLog.append(item);
  nodes.chatLog.scrollTop = nodes.chatLog.scrollHeight;
}

function recordEvent(event) {
  const type = event.type || "unknown";
  eventCounts.set(type, (eventCounts.get(type) || 0) + 1);

  const item = document.createElement("li");
  const badge = document.createElement("span");
  badge.className = "event-type";
  badge.textContent = type;
  item.append(badge, document.createTextNode(event.content || ""));
  nodes.eventLog.prepend(item);

  if (type === "stream" || type === "greeting") {
    appendMessage(event.content, "ai");
  } else if (type === "coffee_request") {
    appendMessage(event.content, "event");
  } else if (type === "name_reveal") {
    nodes.companionName.textContent = event.content || "named";
  } else if (type === "user_name_set") {
    nodes.userName.textContent = event.content || "user set";
  }
  drawSignal();
}

function setBusy(isBusy) {
  nodes.streamState.textContent = isBusy ? "streaming" : "idle";
}

async function refreshState() {
  const response = await fetch(`/api/demo/state/${companionId}`);
  const state = await response.json();
  const companion = state.companion || {};
  nodes.companionName.textContent = companion.name || "???";
  nodes.userName.textContent = companion.user_name || "user unset";
  nodes.metricsBox.textContent = JSON.stringify(state.metrics || [], null, 2);
  return state;
}

function parseFrame(raw) {
  const line = raw
    .split("\n")
    .find((part) => part.startsWith("data:"));
  if (!line) {
    return null;
  }
  return JSON.parse(line.replace(/^data:\s*/, ""));
}

async function readEventStream(response) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true });
    const frames = buffer.split("\n\n");
    buffer = frames.pop() || "";
    for (const frame of frames) {
      if (!frame.trim()) {
        continue;
      }
      const event = parseFrame(frame);
      if (event) {
        recordEvent(event);
      }
    }
  }
}

async function streamRequest(url, options = {}) {
  setBusy(true);
  try {
    const response = await fetch(url, options);
    if (!response.ok || !response.body) {
      appendMessage(`HTTP ${response.status}`, "event");
      return;
    }
    await readEventStream(response);
  } finally {
    setBusy(false);
    await refreshState();
  }
}

async function sendChat(message, type = "chat") {
  appendMessage(message, "user");
  await streamRequest(`/api/chat/${companionId}/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Chat-Canary": "graph",
    },
    body: JSON.stringify({ message, type, lang: currentLang }),
  });
}

async function runEmotion() {
  const response = await fetch(`/api/demo/emotion/${companionId}`, {
    method: "POST",
  });
  const payload = await response.json();
  const result = payload.result || {};
  if (result.skipped) {
    appendMessage("Emotion dry-run skipped.", "event");
  } else {
    const analysis = result.analysis || {};
    appendMessage(analysis.summary_text || "Emotion dry-run complete.", "event");
  }
  await refreshState();
}

async function resetDemo() {
  await fetch(`/api/demo/reset/${companionId}`, { method: "POST" });
  nodes.chatLog.replaceChildren();
  nodes.eventLog.replaceChildren();
  eventCounts.clear();
  drawSignal();
  await refreshState();
}

function drawSignal() {
  const canvas = nodes.signalCanvas;
  const context = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  context.clearRect(0, 0, width, height);
  context.fillStyle = "#111827";
  context.fillRect(0, 0, width, height);

  const tracks = [
    ["greeting", "#7dd3fc"],
    ["name_reveal", "#fbbf24"],
    ["stream", "#86efac"],
    ["end", "#c4b5fd"],
    ["coffee_request", "#fda4af"],
    ["user_name_set", "#93c5fd"],
  ];
  const gap = height / (tracks.length + 1);
  context.lineWidth = 1;
  context.font = "12px sans-serif";

  tracks.forEach(([name, color], index) => {
    const y = Math.round(gap * (index + 1));
    const count = eventCounts.get(name) || 0;
    context.strokeStyle = "rgba(255,255,255,0.18)";
    context.beginPath();
    context.moveTo(92, y);
    context.lineTo(width - 18, y);
    context.stroke();
    context.fillStyle = "#d1d5db";
    context.fillText(name, 12, y + 4);
    for (let dot = 0; dot < Math.min(count, 8); dot += 1) {
      const x = 108 + dot * 24;
      context.fillStyle = color;
      context.beginPath();
      context.arc(x, y, 5, 0, Math.PI * 2);
      context.fill();
    }
  });
}

document.querySelectorAll("[data-action]").forEach((button) => {
  button.addEventListener("click", async () => {
    const action = button.dataset.action;
    if (action === "greeting") {
      await streamRequest(`/api/chat/${companionId}/greeting?lang=${currentLang}`);
    } else if (action === "name-ai") {
      await sendChat(scenarioText[currentLang].nameAi);
    } else if (action === "user-name") {
      await sendChat(scenarioText[currentLang].userName);
    } else if (action === "coffee") {
      await sendChat(scenarioText[currentLang].coffee, "coffee_turn");
    } else if (action === "emotion") {
      await runEmotion();
    } else if (action === "reset") {
      await resetDemo();
    }
  });
});

nodes.langButtons.forEach((button) => {
  button.addEventListener("click", () => {
    currentLang = button.dataset.lang || "en";
    document.documentElement.lang = currentLang;
    nodes.langButtons.forEach((item) => {
      item.classList.toggle("active", item === button);
    });
    if (!nodes.messageInput.value.trim()) {
      nodes.messageInput.value = scenarioText[currentLang].hello;
    }
  });
});

nodes.messageForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = nodes.messageInput.value.trim();
  if (!message) {
    return;
  }
  await sendChat(message);
  nodes.messageInput.value = "";
});

nodes.clearEvents.addEventListener("click", () => {
  nodes.eventLog.replaceChildren();
});

drawSignal();
refreshState();
