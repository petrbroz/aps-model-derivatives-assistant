class DataManagementClient {
    constructor(authProvider, host = "https://developer.api.autodesk.com") {
        this.authProvider = authProvider;
        this.host = host;
    }

    async #get(endpoint) {
        const credentials = await this.authProvider.getCredentials();
        const headers = { "Authorization": `Bearer ${credentials.access_token}` };
        const response = await fetch(`${this.host}/${endpoint}`, { headers });
        if (!response.ok) {
            throw new Error(`Failed to fetch ${endpoint}: ${response.status} ${response.statusText}`);
        }
        return response.json();
    }

    async getHubs() {
        return this.#get("project/v1/hubs");
    }

    async getProjects(hubId) {
        return this.#get(`project/v1/hubs/${hubId}/projects`);
    }

    async getProjectFolders(hubId, projectId) {
        return this.#get(`project/v1/hubs/${hubId}/projects/${projectId}/topFolders`);
    }

    async getFolderContents(projectId, folderId) {
        return this.#get(`data/v1/projects/${projectId}/folders/${folderId}/contents`);
    }
}

export async function initBrowser(authProvider, onSelectionChanged) {
    const dataManagementClient = new DataManagementClient(authProvider);
    const { data: hubs } = await dataManagementClient.getHubs();
    const $tree = document.querySelector("#browser > sl-tree");
    for (const hub of hubs) {
        $tree.append(createTreeItem(`hub|${hub.id}`, hub.attributes.name, "cloud", true));
    }
    $tree.addEventListener("sl-selection-change", function ({ detail }) {
        if (detail.selection.length === 1 && detail.selection[0].id.startsWith("itm|")) {
            const [, hubId, projectId, itemId, urn] = detail.selection[0].id.split("|");
            const versionId = atob(urn.replace("_", "/"));
            onSelectionChanged({ hubId, projectId, itemId, versionId, urn });
        }
    });

    function createTreeItem(id, text, icon, children = false) {
        const item = document.createElement("sl-tree-item");
        item.id = id;
        item.innerHTML = `<sl-icon name="${icon}"></sl-icon><span style="white-space: nowrap">${text}</span>`;
        if (children) {
            item.lazy = true;
            item.addEventListener("sl-lazy-load", async function (ev) {
                ev.stopPropagation();
                item.lazy = false;
                const tokens = item.id.split("|");
                switch (tokens[0]) {
                    case "hub": {
                        const { data: projects } = await dataManagementClient.getProjects(tokens[1]);
                        item.append(...projects.map(project => createTreeItem(`prj|${tokens[1]}|${project.id}`, project.attributes.name, "building", true)));
                        break;
                    }
                    case "prj": {
                        const { data: folders } = await dataManagementClient.getProjectFolders(tokens[1], tokens[2]);
                        item.append(...folders.map(folder => createTreeItem(`fld|${tokens[1]}|${tokens[2]}|${folder.id}`, folder.attributes.displayName, "folder", true)));
                        break;
                    }
                    case "fld": {
                        const { data: contents, included } = await dataManagementClient.getFolderContents(tokens[2], tokens[3]);
                        const folders = contents.filter(entry => entry.type === "folders");
                        item.append(...folders.map(folder => createTreeItem(`fld|${tokens[1]}|${tokens[2]}|${folder.id}`, folder.attributes.displayName, "folder", true)));
                        const designs = contents.filter(entry => entry.type === "items");
                        for (const [i, design] of designs.entries()) {
                            const urn = included[i].relationships.derivatives.data.id;
                            item.append(createTreeItem(`itm|${tokens[1]}|${tokens[2]}|${design.id}|${urn}`, design.attributes.displayName, "file-earmark-richtext", false));
                        }
                        break;
                    }
                }
            });
        }
        return item;
    }
}