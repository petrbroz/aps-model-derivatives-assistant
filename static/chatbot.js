export function initChatbot(authProvider, urn) {
    const $chatbot = document.querySelector("#chatbot");
    $chatbot.innerHTML = `
        <div style="width: 100%; height: 100%;">
            <div id="chatbot-history" style="position: relative; top: 0; left: 0; right: 0; height: 80%; overflow-y: auto; display: flex; flex-flow: column nowrap;">
            </div>
            <div id="chatbot-prompt" style="position: relative; left: 0; right: 0; bottom: 0; height: 20%; overflow-y: hidden; display: flex; flex-flow: column nowrap;">
                <textarea id="chatbot-input" style="margin: 0.5em; margin-bottom: 0; height: 100%;">What are the top 5 elements with the largest area?</textarea>
                <div style="display: flex; flex-flow: row nowrap; align-items: center;">
                    <sl-button id="chatbot-send" variant="primary" style="margin: 0.5em; flex-grow: 1;">Send</sl-button>
                    <sl-icon-button id="chatbot-tips" name="question" label="Tips" style="margin: 0.5em 0.5em 0.5em 0;"></sl-icon-button>
                </div>
            </div>
            <sl-dialog id="chatbot-tips-dialog" label="Tips">
                <sl-button class="example" size="small" style="margin: 0.5em" pill>
                    What are the top 5 elements with the largest area?
                </sl-button>
                <sl-button class="example" size="small" style="margin: 0.5em" pill>
                    Give me the complete list of IDs of wall elements.
                </sl-button>
                <sl-button class="example" size="small" style="margin: 0.5em" pill>
                    What is the average height of doors?
                </sl-button>
                <sl-button class="example" size="small" style="margin: 0.5em" pill>
                    What is the sum of volumes of all floors?
                </sl-button>
                <sl-button slot="footer" variant="primary">Close</sl-button>
            </sl-dialog>
        </div>
    `;
    const $input = document.getElementById("chatbot-input");
    const $button = document.getElementById("chatbot-send");
    $button.addEventListener("click", async function () {
        const prompt = $input.value;
        addChatMessage("User", prompt);
        $input.value = "";
        $input.setAttribute("disabled", "true");
        $button.innerText = "Thinking...";
        $button.setAttribute("disabled", "true");
        try {
            const answer = await submitPrompt(prompt, urn, authProvider);
            addChatMessage("Assistant", answer);
        } catch (err) {
            console.error(err);
            alert("Unable to process the query. See console for more details.");
        } finally {
            $input.removeAttribute("disabled");
            $button.innerText = "Send";
            $button.removeAttribute("disabled");
        }
    });
    const tipsDialog = document.getElementById("chatbot-tips-dialog");
    const tipsOpenButton = document.getElementById("chatbot-tips");
    const tipsCloseButton = tipsDialog.querySelector(`sl-button[slot="footer"]`);
    tipsOpenButton.addEventListener("click", () => tipsDialog.show());
    tipsCloseButton.addEventListener("click", () => tipsDialog.hide());
    for (const example of tipsDialog.querySelectorAll("sl-button.example")) {
        example.addEventListener("click", function () {
            $input.value = example.innerText;
            tipsDialog.hide();
        });
    }
}

async function submitPrompt(prompt, urn, authProvider) {
    const credentials = await authProvider.getCredentials();
    const resp = await fetch(`/chatbot/prompt`, {
        method: "post",
        headers: {
            "Authorization": `Bearer ${credentials.access_token}`,
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ urn, prompt })
    });
    if (resp.ok) {
        const { responses } = await resp.json();
        return responses.join("\n\n");
    } else {
        throw new Error(await resp.text());
    }
}

function addChatMessage(title, message) {
    const card = document.createElement("sl-card");
    card.classList.add("card-header");
    card.style.margin = "0.5em";
    message = DOMPurify.sanitize(marked.parse(message)); // Sanitize and render markdown
    card.innerHTML = `<div slot="header">${title}</div>${message}`;
    const _history = document.getElementById("chatbot-history");
    _history.appendChild(card);
    setTimeout(() => _history.scrollTop = _history.scrollHeight, 1);
}