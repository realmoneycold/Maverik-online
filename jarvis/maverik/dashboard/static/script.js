document.addEventListener('DOMContentLoaded', () => {
    // Navigation Logic
    const navItems = document.querySelectorAll('.nav-item');
    const tabContents = document.querySelectorAll('.tab-content');

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = item.getAttribute('data-tab');
            
            // Update nav styles
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
            
            // Update tab contents
            tabContents.forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(`tab-${targetId}`).classList.add('active');

            // Fetch data if needed
            if(targetId === 'memory') fetchMemory();
            if(targetId === 'skills') fetchSkills();
        });
    });

    // Refresh Buttons
    document.getElementById('refresh-memory').addEventListener('click', fetchMemory);
    document.getElementById('refresh-skills').addEventListener('click', fetchSkills);

    // Initial Data Fetch
    fetchSystemStatus();
    fetchMemory();
    fetchSkills();
});

async function fetchSystemStatus() {
    try {
        const response = await fetch('/api/system');
        const data = await response.json();
        if (data.status === 'success') {
            document.getElementById('brain-status').textContent = `Brain: ${data.data.brain_status}`;
            document.getElementById('model-status').textContent = `Model: ${data.data.model}`;
            document.getElementById('vram-status').textContent = data.data.memory_vram;
        }
    } catch (error) {
        console.error("Error fetching system status:", error);
    }
}

async function fetchMemory() {
    const container = document.getElementById('memory-list');
    container.innerHTML = '<div class="loading-spinner"></div>';
    
    try {
        const response = await fetch('/api/memory');
        const data = await response.json();
        
        if (data.status === 'success') {
            document.getElementById('memory-count').textContent = data.data.length;
            
            if (data.data.length === 0) {
                container.innerHTML = '<div class="empty-state"><p>Core memory is empty.</p></div>';
                return;
            }

            container.innerHTML = data.data.reverse().map(mem => `
                <div class="memory-item">
                    <p>${mem}</p>
                </div>
            `).join('');
        }
    } catch (error) {
        container.innerHTML = `<div class="empty-state" style="color: var(--danger)"><p>Failed to load memory.</p></div>`;
    }
}

async function fetchSkills() {
    const container = document.getElementById('skills-list');
    container.innerHTML = '<div class="loading-spinner"></div>';
    
    try {
        const response = await fetch('/api/skills');
        const data = await response.json();
        
        if (data.status === 'success') {
            document.getElementById('skill-count').textContent = data.data.length;
            
            if (data.data.length === 0) {
                container.innerHTML = '<div class="empty-state"><p>No custom skills found.</p></div>';
                return;
            }

            container.innerHTML = data.data.map(skill => `
                <div class="skill-card">
                    <div class="skill-header">
                        <i class="fa-brands fa-python skill-icon"></i>
                        <h3>${skill.name}</h3>
                    </div>
                    <div class="skill-meta">
                        <span><i class="fa-solid fa-file-code"></i> Python Script</span>
                        <span><i class="fa-solid fa-weight-hanging"></i> ${(skill.size / 1024).toFixed(1)} KB</span>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        container.innerHTML = `<div class="empty-state" style="color: var(--danger)"><p>Failed to load skills.</p></div>`;
    }
}

async function triggerAction(actionType) {
    const inputId = `${actionType}-input`;
    const taskText = document.getElementById(inputId).value.trim();
    if (!taskText) {
        alert("Please enter a prompt or query first.");
        return;
    }

    const outputBox = document.getElementById('action-output');
    outputBox.innerHTML = `> Executing ${actionType.toUpperCase()} module...\n> Task: "${taskText}"\n> Please wait, MAVERIK is thinking...<span class="blinking-cursor">_</span>`;

    try {
        const response = await fetch(`/api/action/${actionType}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ task: taskText })
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            outputBox.innerHTML = outputBox.innerHTML.replace('<span class="blinking-cursor">_</span>', '') + `\n\n[MAVERIK]:\n${data.response}`;
        } else {
            outputBox.innerHTML = outputBox.innerHTML.replace('<span class="blinking-cursor">_</span>', '') + `\n\n[ERROR]: ${data.message || 'Action failed.'}`;
        }
    } catch (error) {
        outputBox.innerHTML = outputBox.innerHTML.replace('<span class="blinking-cursor">_</span>', '') + `\n\n[ERROR]: Could not connect to MAVERIK Brain.\n${error}`;
    }
}
