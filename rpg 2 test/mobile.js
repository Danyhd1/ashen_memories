const statusText = document.querySelector("#status");
const locationText = document.querySelector("#location");
const partyPanel = document.querySelector("#partyPanel");
const enemyPanel = document.querySelector("#enemyPanel");
const enemyName = document.querySelector("#enemyName");
const enemyHealth = document.querySelector("#enemyHealth");
const attackButton = document.querySelector("#attackButton");

async function api(path, body = null) {
  const response = await fetch(path, {
    method: body ? "POST" : "GET",
    headers: body ? {"Content-Type": "application/json"} : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({error: "Request failed"}));
    throw new Error(error.error || "Request failed");
  }
  return response.json();
}

function render(state) {
  statusText.textContent = state.status;
  locationText.textContent = state.map
    ? `Map: ${state.map} • Position: ${state.x}, ${state.y}`
    : "";
  partyPanel.innerHTML = state.members.map(member =>
    `<article class="member">
      <strong>${member.name}</strong><br>
      ${member.job} • Lv ${member.level}<br>
      HP ${member.hp}/${member.max_hp} • MP ${member.mp}/${member.max_mp}
    </article>`
  ).join("");

  if (state.enemy) {
    enemyPanel.hidden = false;
    enemyName.textContent = state.enemy.name;
    enemyHealth.max = state.enemy.max_hp;
    enemyHealth.value = state.enemy.hp;
    attackButton.disabled = false;
  } else {
    enemyPanel.hidden = true;
    attackButton.disabled = true;
  }
}

async function refresh() {
  try {
    render(await api("/api/state"));
  } catch (error) {
    statusText.textContent = error.message;
  }
}

document.querySelectorAll("[data-direction]").forEach(button => {
  button.addEventListener("click", async () => {
    try {
      render(await api("/api/move", {direction: button.dataset.direction}));
    } catch (error) {
      statusText.textContent = error.message;
    }
  });
});

document.querySelector("#newButton").addEventListener("click", async () => {
  render(await api("/api/new", {}));
});
document.querySelector("#saveButton").addEventListener("click", async () => {
  render(await api("/api/save", {}));
});
document.querySelector("#loadButton").addEventListener("click", async () => {
  render(await api("/api/load", {}));
});
attackButton.addEventListener("click", async () => {
  render(await api("/api/attack", {}));
});

let installPrompt;
window.addEventListener("beforeinstallprompt", event => {
  event.preventDefault();
  installPrompt = event;
  document.querySelector("#installButton").hidden = false;
});
document.querySelector("#installButton").addEventListener("click", async () => {
  if (installPrompt) {
    installPrompt.prompt();
    await installPrompt.userChoice;
  }
});

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => navigator.serviceWorker.register("/sw.js"));
}

refresh();
