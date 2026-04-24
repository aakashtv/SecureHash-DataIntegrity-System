const logContainer = document.getElementById("logs-list");
const riskButtons = document.querySelectorAll(".risk-trigger");

function addLog(title, description) {
    if (!logContainer) {
        return;
    }

    const entry = document.createElement("div");
    entry.className = "log-entry";
    entry.innerHTML = `
        <strong>${title}</strong>
        <span>${description}</span>
    `;

    logContainer.prepend(entry);

    while (logContainer.children.length > 6) {
        logContainer.removeChild(logContainer.lastChild);
    }
}

function getProgressClass(score) {
    if (score <= 25) {
        return "progress-low";
    }
    if (score <= 50) {
        return "progress-medium";
    }
    return "progress-high";
}

function buildExplanation(card, result) {
    const anomalyFlag = Number(card.dataset.anomalyFlag) === 1;
    const usageRate = Number(card.dataset.usageRate || 0);
    const algorithm = card.dataset.algorithm || "Unknown";

    const reasons = [];

    if (anomalyFlag) {
        reasons.push("An anomaly flag is present in the latest telemetry.");
    } else {
        reasons.push("Recent telemetry does not show an active anomaly flag.");
    }

    if (usageRate > 70) {
        reasons.push(`Usage rate is elevated at ${usageRate}, which increases operational exposure.`);
    } else {
        reasons.push(`Usage rate is currently ${usageRate}, which is within a calmer range.`);
    }

    if (algorithm === "RSA-1024") {
        reasons.push("The algorithm is RSA-1024, which is treated as weak by the risk model.");
    } else {
        reasons.push(`${algorithm} is treated as a stronger algorithm in the current model.`);
    }

    reasons.push(`The engine selected ${result.action} because the key is currently rated ${result.risk_level.toLowerCase()} risk.`);
    return reasons.join(" ");
}

async function fetchRisk(keyId, button) {
    const card = button.closest(".key-card");
    const riskScoreEl = card.querySelector(".risk-score-value");
    const riskLevelEl = card.querySelector(".risk-level-value");
    const riskActionEl = card.querySelector(".risk-action-value");
    const progressBar = card.querySelector(".progress-bar");
    const explanationEl = card.querySelector(".explanation-text");
    const statusBadge = card.querySelector(".status-badge");

    button.disabled = true;
    button.textContent = "Loading...";

    try {
        const response = await fetch(`/risk/${keyId}`);
        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || "Unable to calculate risk.");
        }

        const score = Number(result.risk_score || 0);
        const progressClass = getProgressClass(score);

        riskScoreEl.textContent = `${score.toFixed(2)} / 100`;
        riskLevelEl.textContent = `Level: ${result.risk_level}`;
        riskActionEl.textContent = `Action: ${result.action}`;

        progressBar.style.width = `${Math.max(0, Math.min(score, 100))}%`;
        progressBar.className = `progress-bar ${progressClass}`;

        explanationEl.textContent = buildExplanation(card, result);

        if (statusBadge && result.status) {
            statusBadge.textContent = result.status;
            statusBadge.className = `status-badge status-${String(result.status).toLowerCase()}`;
        }

        addLog(
            `Risk evaluated for ${card.dataset.keyName}`,
            `Score ${score.toFixed(2)} (${result.risk_level}) triggered action "${result.action}" and set status to "${result.status}".`
        );
    } catch (error) {
        explanationEl.textContent = error.message;
        addLog("Risk evaluation failed", error.message);
    } finally {
        button.disabled = false;
        button.textContent = "Get Risk";
    }
}

riskButtons.forEach((button) => {
    button.addEventListener("click", () => {
        fetchRisk(button.dataset.keyId, button);
    });
});

document.querySelectorAll(".subtle-btn, .alert-btn").forEach((link) => {
    link.addEventListener("click", () => {
        const card = link.closest(".key-card");
        const label = link.textContent.trim();
        addLog(
            `${label} started`,
            `Telemetry simulation requested for ${card.dataset.keyName}. The page will refresh after the backend update.`
        );
    });
});
