export function initViewer(authProvider) {
    async function getAccessToken(callback) {
        const credentials = await authProvider.getCredentials();
        callback(credentials.access_token, Math.round((credentials.expires_at - Date.now()) / 1000));
    }
    return new Promise(function (resolve, reject) {
        Autodesk.Viewing.Initializer({ env: "AutodeskProduction2", api: "streamingV2", getAccessToken }, function () {
            const $container = document.querySelector("#preview");
            const options = {
                extensions: ["Autodesk.DocumentBrowser"]
            };
            const viewer = new Autodesk.Viewing.GuiViewer3D($container, options);
            viewer.start();
            viewer.setTheme("light-theme");
            viewer.setEnvMapBackground(false);
            resolve(viewer);
        });
    });
}

export function loadModel(viewer, urn) {
    function onDocumentLoadSuccess(doc) {
        viewer.loadDocumentNode(doc, doc.getRoot().getDefaultGeometry());
    }
    function onDocumentLoadFailure(code, message) {
        alert("Could not load model. See console for more details.");
        console.error(message);
    }
    Autodesk.Viewing.Document.load("urn:" + urn, onDocumentLoadSuccess, onDocumentLoadFailure);
}