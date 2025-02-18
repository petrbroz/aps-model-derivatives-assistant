import { initAuth, login, logout } from "./auth.js";
import { initBrowser } from "./browser.js";
import { initViewer, loadModel } from "./viewer.js";
import { initChatbot } from "./chatbot.js";

const authProvider = await initAuth();
const $login = document.querySelector("#login");
$login.style.visibility = "visible";
if (authProvider) {
    $login.innerText = "Logout";
    $login.onclick = () => logout();
    const viewer = await initViewer(authProvider);
    await initBrowser(authProvider, (el) => {
        loadModel(viewer, el.urn);
        initChatbot(authProvider, el.urn);
        document.getElementById("chatbot").addEventListener("click", function ({ target }) {
            if (target.dataset.dbids) {
                const dbids = target.dataset.dbids.split(",").map(e => parseInt(e));
                viewer.isolate(dbids);
                viewer.fitToView(dbids);
            }
        });
    });
} else {
    $login.innerText = "Login";
    $login.onclick = () => login();
}