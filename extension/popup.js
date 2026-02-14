// popup.js - Chrome Extension Frontend

const API_URL = "http://localhost:8000";

// Action type selector
document.getElementById("action-type").addEventListener("change", (e) => {
    const actionType = e.target.value;
    
    // Hide all sections
    document.getElementById("chat-section").style.display = "none";
    document.getElementById("send-email-section").classList.remove("active");
    document.getElementById("fetch-email-section").classList.remove("active");
    
    // Show selected section
    if (actionType === "chat") {
        document.getElementById("chat-section").style.display = "block";
    } else if (actionType === "send-email") {
        document.getElementById("send-email-section").classList.add("active");
    } else if (actionType === "fetch-email") {
        document.getElementById("fetch-email-section").classList.add("active");
    }
    
    // Clear result
    document.getElementById("result").classList.add("hidden");
});

// Check backend connection on load
async function checkConnection() {
    const statusDiv = document.getElementById("status");
    try {
        const response = await fetch(`${API_URL}/health`);
        if (response.ok) {
            statusDiv.textContent = "Connected to Backend";
            statusDiv.className = "status connected";
        } else {
            statusDiv.textContent = "Backend Error";
            statusDiv.className = "status disconnected";
        }
    } catch (error) {
        statusDiv.textContent = "Backend Not Running";
        statusDiv.className = "status disconnected";
    }
}

// Execute button handler
document.getElementById("execute-btn").addEventListener("click", async () => {
    const actionType = document.getElementById("action-type").value;
    const resultDiv = document.getElementById("result");
    const executeBtn = document.getElementById("execute-btn");

    executeBtn.disabled = true;
    executeBtn.textContent = "Processing...";
    resultDiv.innerHTML = "Working...";
    resultDiv.classList.remove("hidden");

    try {
        if (actionType === "chat") {
            await handleChatQuery(resultDiv);
        } else if (actionType === "send-email") {
            await handleSendEmail(resultDiv);
        } else if (actionType === "fetch-email") {
            await handleFetchEmails(resultDiv);
        }
    } catch (error) {
        resultDiv.innerHTML = `<strong>Error:</strong> ${error.message}`;
    } finally {
        executeBtn.disabled = false;
        executeBtn.textContent = "Execute Task";
    }
});

// Handle chat/general query
async function handleChatQuery(resultDiv) {
    const task = document.getElementById("task").value.trim();

    if (!task) {
        resultDiv.innerHTML = "<strong>Error:</strong> Please enter a query";
        return;
    }

    // Show appropriate loading message
    const isComplexQuery = task.toLowerCase().includes('buy') || 
                          task.toLowerCase().includes('compare') || 
                          task.toLowerCase().includes('shop');
    
    const isScrapingQuery = task.toLowerCase().includes('scrape') ||
                           task.toLowerCase().includes('extract');
    
    if (isComplexQuery) {
        resultDiv.innerHTML = "🔄 Running Enhanced MCTS Planning (8 simulations)...\n⏳ Real-time price scraping from 4 platforms...\nThis may take 25-35 seconds for accurate results.";
    } else if (isScrapingQuery) {
        resultDiv.innerHTML = "🔄 Scraping website content...\nThis may take 5-10 seconds.";
    } else {
        resultDiv.innerHTML = "🔄 Processing your query...";
    }

    const response = await fetch(`${API_URL}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: task }),
    });

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    let resultHTML = `<strong>Mode:</strong> ${data.mode}\n`;
    
    if (data.task_type) {
        resultHTML += `<strong>Task Type:</strong> ${data.task_type}\n`;
    }
    
    if (data.plan) {
        resultHTML += `<strong>Plan:</strong>\n`;
        data.plan.forEach((step, i) => {
            resultHTML += `${i + 1}. ${step}\n`;
        });
    }
    
    resultHTML += `\n<strong>Result:</strong>\n${data.answer}`;
    
    resultDiv.innerHTML = resultHTML;
}

// Handle send email
async function handleSendEmail(resultDiv) {
    const recipient = document.getElementById("recipient").value.trim();
    const subject = document.getElementById("subject").value.trim();
    const body = document.getElementById("body").value.trim();

    if (!recipient || !subject || !body) {
        resultDiv.innerHTML = "<strong>Error:</strong> Please fill in all email fields";
        return;
    }

    const response = await fetch(`${API_URL}/send-email`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            recipient: recipient,
            subject: subject,
            body: body
        }),
    });

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    resultDiv.innerHTML = data.message;

    // Clear form on success
    if (data.message.includes("✅")) {
        document.getElementById("recipient").value = "";
        document.getElementById("subject").value = "";
        document.getElementById("body").value = "";
    }
}

// Handle fetch emails
async function handleFetchEmails(resultDiv) {
    const response = await fetch(`${API_URL}/fetch-emails`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
    });

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    resultDiv.innerHTML = data.message;
}

// Initialize
checkConnection();
setInterval(checkConnection, 10000);
