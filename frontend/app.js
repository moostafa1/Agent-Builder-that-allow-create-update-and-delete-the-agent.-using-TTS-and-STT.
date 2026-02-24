const API_URL = 'http://localhost:8000/api/v1';
const BASE_URL = 'http://localhost:8000'; 

let currentAgentId = null;
let currentSessionId = null;
let editingAgentId = null; // Tracks if we are editing an agent
let mediaRecorder = null;
let audioChunks = [];

const agentListEl = document.getElementById('agent-list');
const currentAgentNameEl = document.getElementById('current-agent-name');
const sessionSelectEl = document.getElementById('session-select');
const chatWindowEl = document.getElementById('chat-window');
const messageInputEl = document.getElementById('message-input');

const btnCreateAgent = document.getElementById('btn-create-agent');
const btnNewChat = document.getElementById('btn-new-chat');
const btnSendText = document.getElementById('btn-send-text');
const btnRecordVoice = document.getElementById('btn-record-voice');

document.addEventListener('DOMContentLoaded', () => {
    loadAgents();
});

// --- 1. AGENT MANAGEMENT (UPDATED WITH EDIT FEATURE) ---
async function loadAgents() {
    const res = await fetch(`${API_URL}/agents/`);
    const agents = await res.json();
    
    agentListEl.innerHTML = '';
    agents.forEach(agent => {
        const div = document.createElement('div');
        div.className = 'agent-item';
        if (agent.id === currentAgentId) div.classList.add('active');
        
        // Agent Name
        const nameSpan = document.createElement('span');
        nameSpan.className = 'agent-name';
        nameSpan.innerText = agent.name;
        nameSpan.onclick = () => selectAgent(agent.id, agent.name, div);
        
        // Edit Button
        const editBtn = document.createElement('button');
        editBtn.className = 'btn-edit';
        editBtn.innerText = 'Edit';
        editBtn.onclick = (e) => {
            e.stopPropagation(); // Prevents triggering the chat selection
            startEditing(agent);
        };
        
        div.appendChild(nameSpan);
        div.appendChild(editBtn);
        agentListEl.appendChild(div);
    });
}

function startEditing(agent) {
    editingAgentId = agent.id;
    document.getElementById('new-agent-name').value = agent.name;
    document.getElementById('new-agent-prompt').value = agent.prompt;
    btnCreateAgent.innerText = 'Update Agent';
}

btnCreateAgent.onclick = async () => {
    const name = document.getElementById('new-agent-name').value;
    const prompt = document.getElementById('new-agent-prompt').value;
    if (!name || !prompt) return alert("Please enter name and prompt!");

    if (editingAgentId) {
        // UPDATE EXISTING AGENT
        await fetch(`${API_URL}/agents/${editingAgentId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, prompt })
        });
        editingAgentId = null;
        btnCreateAgent.innerText = 'Create Agent';
    } else {
        // CREATE NEW AGENT
        await fetch(`${API_URL}/agents/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, prompt })
        });
    }

    document.getElementById('new-agent-name').value = '';
    document.getElementById('new-agent-prompt').value = '';
    loadAgents();
};

async function selectAgent(agentId, agentName, element) {
    currentAgentId = agentId;
    currentAgentNameEl.innerText = agentName;
    document.querySelectorAll('.agent-item').forEach(el => el.classList.remove('active'));
    element.classList.add('active');
    btnNewChat.disabled = false;
    sessionSelectEl.disabled = false;
    await loadSessions();
}

// --- 2. SESSION MANAGEMENT ---
async function loadSessions() {
    const res = await fetch(`${API_URL}/agents/${currentAgentId}/sessions`);
    const sessions = await res.json();
    
    sessionSelectEl.innerHTML = '<option value="">-- Select a chat --</option>';
    sessions.forEach((s, index) => {
        const opt = document.createElement('option');
        opt.value = s.id;
        opt.innerText = s.name || `Chat ${sessions.length - index}`;
        sessionSelectEl.appendChild(opt);
    });

    if (sessions.length > 0) {
        sessionSelectEl.value = sessions[0].id;
        selectSession(sessions[0].id);
    } else {
        chatWindowEl.innerHTML = '<div class="system-message">No chats yet. Click "New Chat" to begin.</div>';
        disableInput();
    }
}

btnNewChat.onclick = async () => {
    const res = await fetch(`${API_URL}/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_id: currentAgentId, name: `Chat ${new Date().toLocaleTimeString()}` })
    });
    const newSession = await res.json();
    await loadSessions();
    sessionSelectEl.value = newSession.id;
    selectSession(newSession.id);
};

sessionSelectEl.onchange = (e) => selectSession(e.target.value);

async function selectSession(sessionId) {
    if (!sessionId) return disableInput();
    currentSessionId = sessionId;
    enableInput();
    
    const res = await fetch(`${API_URL}/sessions/${sessionId}/messages`);
    const messages = await res.json();
    
    chatWindowEl.innerHTML = '';
    if (messages.length === 0) {
        chatWindowEl.innerHTML = '<div class="system-message">Send a message to start the conversation!</div>';
    } else {
        messages.forEach(msg => appendMessage(msg.role, msg.content, msg.audio_file_path));
    }
}

// --- 3. MESSAGING ---

// Allow sending message with the "Enter" key
messageInputEl.addEventListener('keypress', function (e) {
    if (e.key === 'Enter' && !btnSendText.disabled) {
        btnSendText.click();
    }
});

function appendMessage(role, text, audioPath = null) {
    const sysMsg = chatWindowEl.querySelector('.system-message');
    if (sysMsg) sysMsg.remove();

    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.innerText = text;

    if (audioPath) {
        const audioEl = document.createElement('audio');
        audioEl.controls = true;
        audioEl.src = `${BASE_URL}/${audioPath}`; 
        div.appendChild(document.createElement('br'));
        div.appendChild(audioEl);
    }

    chatWindowEl.appendChild(div);
    chatWindowEl.scrollTop = chatWindowEl.scrollHeight; 
}

btnSendText.onclick = async () => {
    const text = messageInputEl.value.trim();
    if (!text) return;

    appendMessage('user', text);
    messageInputEl.value = '';
    
    const typingId = "typing-" + Date.now();
    appendMessage('assistant', "...", null);
    chatWindowEl.lastChild.id = typingId;

    try {
        const res = await fetch(`${API_URL}/sessions/${currentSessionId}/messages/text`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: text })
        });
        const msg = await res.json();
        document.getElementById(typingId).remove();
        appendMessage(msg.role, msg.content, msg.audio_file_path);
    } catch (err) {
        document.getElementById(typingId).innerText = "Error connecting to AI.";
    }
};

btnRecordVoice.onmousedown = async () => {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
        mediaRecorder.onstop = sendVoiceDataToBackend;
        mediaRecorder.start();
        btnRecordVoice.classList.add('recording');
    } catch (err) {
        alert("Microphone access denied or not available.");
    }
};

btnRecordVoice.onmouseup = () => {
    if (mediaRecorder && mediaRecorder.state === "recording") {
        mediaRecorder.stop();
        btnRecordVoice.classList.remove('recording');
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
    }
};

async function sendVoiceDataToBackend() {
    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
    const formData = new FormData();
    formData.append('file', audioBlob, 'user_voice.webm');

    const processingId = "proc-" + Date.now();
    appendMessage('user', '🎤 [Voice Audio Sent]');
    appendMessage('assistant', "Processing audio...", null);
    chatWindowEl.lastChild.id = processingId;

    try {
        const res = await fetch(`${API_URL}/sessions/${currentSessionId}/messages/voice`, {
            method: 'POST',
            body: formData
        });
        if (!res.ok) throw new Error("Backend error");
        const msg = await res.json();
        document.getElementById(processingId).remove();
        appendMessage(msg.role, msg.content, msg.audio_file_path);
    } catch (err) {
        document.getElementById(processingId).innerText = "Error processing voice (Check backend logs).";
    }
}

function disableInput() {
    messageInputEl.disabled = true;
    btnSendText.disabled = true;
    btnRecordVoice.disabled = true;
}

function enableInput() {
    messageInputEl.disabled = false;
    btnSendText.disabled = false;
    btnRecordVoice.disabled = false;
}