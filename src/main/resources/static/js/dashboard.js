"use strict";

const refreshButton = document.getElementById("refresh");
const feedback = document.getElementById("feedback");
const healthBadge = document.getElementById("health");
let refreshing = false;

async function fetchJson(path) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 8000);
    try {
        const response = await fetch(path, { cache: "no-store", signal: controller.signal });
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        return await response.json();
    } finally {
        clearTimeout(timeout);
    }
}

async function refreshDashboard() {
    if (refreshing) return;
    refreshing = true;
    refreshButton.disabled = true;
    feedback.textContent = "Refreshing deployment information…";

    try {
        const [infoResult, healthResult] = await Promise.allSettled([
            fetchJson("/api/info"),
            fetchJson("/actuator/health")
        ]);

        if (infoResult.status === "fulfilled") {
            const info = infoResult.value;
            // textContent keeps environment-provided metadata as plain text.
            document.getElementById("app-name").textContent = info.name;
            document.getElementById("version").textContent = info.version;
            document.getElementById("environment").textContent = info.environment;
            document.getElementById("message").textContent = info.message;
            document.getElementById("commit-sha").textContent = info.commitSha || "Not provided";
            feedback.textContent = "Metadata refreshes every 30 seconds.";
        } else {
            document.getElementById("app-name").textContent = "Deployment information unavailable";
            document.getElementById("version").textContent = "—";
            document.getElementById("environment").textContent = "—";
            document.getElementById("message").textContent = "Could not load the current deployment. Try refreshing.";
            document.getElementById("commit-sha").textContent = "Unavailable";
            feedback.textContent = "Metadata request failed. Retrying automatically in 30 seconds.";
        }

        const isHealthy = healthResult.status === "fulfilled" && healthResult.value.status === "UP";
        healthBadge.className = `health ${isHealthy ? "up" : "down"}`;
        healthBadge.textContent = isHealthy ? "● Healthy" : "● Unavailable / unhealthy";
        document.getElementById("last-checked").textContent = new Date().toLocaleTimeString();
    } finally {
        refreshButton.disabled = false;
        refreshing = false;
    }
}

refreshButton.addEventListener("click", refreshDashboard);
refreshDashboard();
setInterval(refreshDashboard, 30000);
