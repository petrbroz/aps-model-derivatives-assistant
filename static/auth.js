import { APS_CLIENT_ID, APS_CALLBACK_URL } from "./config.js";

class LocalStorageAuthenticationProvider {
    async getCredentials() {
        let credentials = {
            access_token: localStorage.getItem("access_token"),
            refresh_token: localStorage.getItem("refresh_token"),
            expires_at: parseInt(localStorage.getItem("expires_at"))
        };
        if (credentials.expires_at < Date.now()) {
            credentials = await refreshToken(APS_CLIENT_ID, credentials.refresh_token);
            localStorage.setItem("access_token", credentials.access_token);
            localStorage.setItem("refresh_token", credentials.refresh_token);
            localStorage.setItem("expires_at", credentials.expires_at);
        }
        return credentials;
    }
}

export async function initAuth() {
    const codeVerifier = localStorage.getItem("code_verifier");
    localStorage.removeItem("code_verifier");
    const params = new URLSearchParams(location.search);
    if (params.has("code")) { // User has been redirected back from Autodesk with an authorization code
        const credentials = await exchangeToken(APS_CLIENT_ID, codeVerifier, params.get("code"), APS_CALLBACK_URL);
        localStorage.setItem("access_token", credentials.access_token);
        localStorage.setItem("refresh_token", credentials.refresh_token);
        localStorage.setItem("expires_at", credentials.expires_at);
        location.search = "";
        return credentials;
    } else if (params.has("error")) { // User has been redirected back from Autodesk with an error
        throw new Error(params.get("error") + ": " + params.get("error_description"));
    } else if (localStorage.getItem("access_token")) { // There is an existing access token in local storage
        return new LocalStorageAuthenticationProvider();
    }
    return null;
}

export async function login() {
    const codeVerifier = generateRandomString(100);
    localStorage.setItem("code_verifier", codeVerifier);
    const codeChallenge = await generateCodeChallenge(codeVerifier);
    location.href = generateLoginUrl(APS_CLIENT_ID, APS_CALLBACK_URL, ["data:read"], "123456", codeChallenge);
}

export async function logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("expires_at");
    location.reload();
}

function generateLoginUrl(clientId, callbackUrl, scopes, nonce, challenge) {
    const url = new URL("https://developer.api.autodesk.com/authentication/v2/authorize");
    url.searchParams.append("response_type", "code");
    url.searchParams.append("client_id", clientId);
    url.searchParams.append("redirect_uri", callbackUrl);
    url.searchParams.append("scope", scopes.join(" "));
    url.searchParams.append("nonce", nonce);
    url.searchParams.append("prompt", "login");
    url.searchParams.append("code_challenge", challenge);
    url.searchParams.append("code_challenge_method", "S256");
    return url.toString();
}

function generateRandomString(len, chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789") {
    const arr = new Array(len);
    for (let i = 0; i < len; i++) {
        arr[i] = chars[Math.floor(Math.random() * chars.length)];
    }
    return arr.join("");
}

async function generateCodeChallenge(str) {
    const hash = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(str));
    return window.btoa(String.fromCharCode(...new Uint8Array(hash))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=/g, "");
}

async function exchangeToken(clientId, codeVerifier, code, callbackUrl) {
    const payload = {
        "grant_type": "authorization_code",
        "client_id": clientId,
        "code_verifier": codeVerifier,
        "code": code,
        "redirect_uri": callbackUrl
    };
    const resp = await fetch("https://developer.api.autodesk.com/authentication/v2/token", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: Object.keys(payload).map(key => encodeURIComponent(key) + "=" + encodeURIComponent(payload[key])).join("&")
    });
    if (!resp.ok) {
        throw new Error(await resp.text());
    }
    const credentials = await resp.json();
    credentials.expires_at = Date.now() + credentials.expires_in * 1000;
    delete credentials.expires_in;
    return credentials;
}

async function refreshToken(clientId, refreshToken) {
    const payload = {
        "grant_type": "refresh_token",
        "client_id": clientId,
        "refresh_token": refreshToken,
    };
    const resp = await fetch("https://developer.api.autodesk.com/authentication/v2/token", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: Object.keys(payload).map(key => encodeURIComponent(key) + "=" + encodeURIComponent(payload[key])).join("&")
    });
    if (!resp.ok) {
        throw new Error(await resp.text());
    }
    const credentials = await resp.json();
    credentials.expires_at = Date.now() + credentials.expires_in * 1000;
    delete credentials.expires_in;
    return credentials;
}