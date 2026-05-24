// Avatar System Frontend JavaScript
const API_BASE = 'http://localhost:8000';

// Tab management
function showTab(tabName) {
    // Hide all tab contents
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => content.classList.remove('active'));
    
    // Remove active class from all tab buttons
    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach(button => button.classList.remove('active'));
    
    // Show selected tab content
    document.getElementById(`${tabName}-tab`).classList.add('active');
    
    // Add active class to selected tab button
    event.target.classList.add('active');
}

// File upload preview
function setupFilePreviews() {
    const fileInputs = [
        { input: 'clone-images', preview: 'images-preview' },
        { input: 'clone-videos', preview: 'videos-preview' },
        { input: 'clone-voice', preview: 'voice-preview' },
        { input: 'clone-docs', preview: 'docs-preview' }
    ];

    fileInputs.forEach(({ input, preview }) => {
        const inputElement = document.getElementById(input);
        const previewElement = document.getElementById(preview);
        
        if (inputElement) {
            inputElement.addEventListener('change', (e) => {
                previewElement.innerHTML = '';
                Array.from(e.target.files).forEach(file => {
                    const div = document.createElement('div');
                    div.className = 'file-preview-item';
                    div.textContent = file.name;
                    previewElement.appendChild(div);
                });
            });
        }
    });
}

// Add social post
function addSocialPost() {
    const container = document.getElementById('social-posts');
    const postDiv = document.createElement('div');
    postDiv.className = 'social-post';
    postDiv.innerHTML = `
        <input type="text" placeholder="Platform (e.g., twitter, instagram)" class="platform-input">
        <textarea placeholder="Post content" rows="2"></textarea>
        <input type="datetime-local">
    `;
    container.appendChild(postDiv);
}

// Add email
function addEmail() {
    const container = document.getElementById('emails');
    const emailDiv = document.createElement('div');
    emailDiv.className = 'email-entry';
    emailDiv.innerHTML = `
        <input type="text" placeholder="Subject">
        <textarea placeholder="Email body" rows="3"></textarea>
        <input type="datetime-local">
    `;
    container.appendChild(emailDiv);
}

// Create avatar
document.getElementById('avatar-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const config = {
        name: document.getElementById('avatar-name').value || undefined,
        gender: document.getElementById('gender').value,
        ethnicity: document.getElementById('ethnicity').value,
        body_type: document.getElementById('body-type').value,
        age: parseInt(document.getElementById('age').value),
        height: parseFloat(document.getElementById('height').value),
        face_shape: document.getElementById('face-shape').value,
        eye_color: document.getElementById('eye-color').value,
        hair_color: document.getElementById('hair-color').value,
        hair_style: document.getElementById('hair-style').value,
        skin_tone: document.getElementById('skin-tone').value,
        outfit: document.getElementById('outfit').value,
        accessories: document.getElementById('accessories').value
            .split(',').map(s => s.trim()).filter(s => s)
    };

    try {
        const response = await axios.post(`${API_BASE}/avatars/create`, config);
        const result = response.data;
        
        document.getElementById('avatar-result').style.display = 'block';
        document.getElementById('avatar-details').innerHTML = `
            <p><strong>Avatar ID:</strong> ${result.avatar_id}</p>
            <p><strong>Status:</strong> ${result.status}</p>
            <p><strong>Created:</strong> ${new Date(result.created_at).toLocaleString()}</p>
        `;
        
        // Update animation avatar dropdown
        loadAvatarOptions();
    } catch (error) {
        console.error('Error creating avatar:', error);
        alert('Error creating avatar: ' + error.response?.data?.detail || error.message);
    }
});

// Create clone
document.getElementById('clone-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const cloneData = {
        name: document.getElementById('clone-name').value,
        email: document.getElementById('clone-email').value || undefined,
        images: [], // Handle file uploads
        videos: [],
        social_media_posts: getSocialPosts(),
        emails: getEmails(),
        voice_notes: [],
        personal_documents: []
    };

    // Handle file uploads (simplified for demo)
    // In real implementation, upload files to server first
    
    try {
        const response = await axios.post(`${API_BASE}/clones/create`, cloneData);
        const result = response.data;
        
        document.getElementById('clone-result').style.display = 'block';
        document.getElementById('clone-details').innerHTML = `
            <p><strong>Clone ID:</strong> ${result.person_id}</p>
            <p><strong>Status:</strong> ${result.status}</p>
            <p><strong>Created:</strong> ${new Date(result.created_at).toLocaleString()}</p>
        `;
    } catch (error) {
        console.error('Error creating clone:', error);
        alert('Error creating clone: ' + error.response?.data?.detail || error.message);
    }
});

// Helper functions to get social posts and emails
function getSocialPosts() {
    const posts = [];
    document.querySelectorAll('.social-post').forEach(post => {
        const inputs = post.querySelectorAll('input, textarea');
        posts.push({
            platform: inputs[0].value,
            content: inputs[1].value,
            timestamp: inputs[2].value
        });
    });
    return posts.filter(post => post.platform && post.content);
}

function getEmails() {
    const emails = [];
    document.querySelectorAll('.email-entry').forEach(email => {
        const inputs = email.querySelectorAll('input, textarea');
        emails.push({
            subject: inputs[0].value,
            body: inputs[1].value,
            timestamp: inputs[2].value
        });
    });
    return emails.filter(email => email.subject && email.body);
}

// Load avatars
async function loadAvatars() {
    try {
        const response = await axios.get(`${API_BASE}/avatars`);
        const avatars = response.data.avatars;
        
        const container = document.getElementById('avatars-list');
        container.innerHTML = '<h3>Avatars</h3>';
        
        for (const avatarId of avatars) {
            const detailsResponse = await axios.get(`${API_BASE}/avatars/${avatarId}`);
            const details = detailsResponse.data;
            
            const card = document.createElement('div');
            card.className = 'item-card';
            card.innerHTML = `
                <h4>${details.config.name || avatarId}</h4>
                <p>Gender: ${details.config.gender}</p>
                <p>Age: ${details.config.age}</p>
                <p>Ethnicity: ${details.config.ethnicity}</p>
                <p>Created: ${new Date(details.created_at).toLocaleDateString()}</p>
            `;
            container.appendChild(card);
        }
    } catch (error) {
        console.error('Error loading avatars:', error);
    }
}

// Load clones
async function loadClones() {
    try {
        const response = await axios.get(`${API_BASE}/clones`);
        const clones = response.data.clones;
        
        const container = document.getElementById('clones-list');
        container.innerHTML = '<h3>Clones</h3>';
        
        for (const cloneId of clones) {
            const detailsResponse = await axios.get(`${API_BASE}/clones/${cloneId}`);
            const details = detailsResponse.data;
            
            const card = document.createElement('div');
            card.className = 'item-card';
            card.innerHTML = `
                <h4>${details.name}</h4>
                <p>ID: ${details.person_id}</p>
                <p>Created: ${new Date(details.created_at).toLocaleDateString()}</p>
                <p>Traits: ${Object.keys(details.personality_traits).length} personality traits</p>
            `;
            container.appendChild(card);
        }
    } catch (error) {
        console.error('Error loading clones:', error);
    }
}

// Load avatar options for animation
async function loadAvatarOptions() {
    try {
        const response = await axios.get(`${API_BASE}/avatars`);
        const avatars = response.data.avatars;
        
        const select = document.getElementById('animate-avatar-id');
        select.innerHTML = '';
        
        avatars.forEach(avatarId => {
            const option = document.createElement('option');
            option.value = avatarId;
            option.textContent = avatarId;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading avatar options:', error);
    }
}

// Animate avatar
async function animateAvatar() {
    const avatarId = document.getElementById('animate-avatar-id').value;
    const animationType = document.getElementById('animation-type').value;
    const expression = document.getElementById('expression').value;
    const intensity = document.getElementById('expression-intensity').value;
    
    try {
        // Animate avatar
        const response = await axios.post(`${API_BASE}/avatars/${avatarId}/animate`, {
            avatar_id: avatarId,
            animation_type: animationType,
            duration: 2.0,
            keyframes: [],
            loop: false
        });
        
        // Animate facial expression
        const expressionResponse = await axios.post(`${API_BASE}/avatars/${avatarId}/expression`, {
            avatar_id: avatarId,
            expression: expression,
            intensity: parseFloat(intensity)
        });
        
        document.getElementById('animation-result').style.display = 'block';
        document.getElementById('animation-details').innerHTML = `
            <p><strong>Avatar:</strong> ${avatarId}</p>
            <p><strong>Animation:</strong> ${animationType}</p>
            <p><strong>Expression:</strong> ${expression} (intensity: ${intensity})</p>
        `;
    } catch (error) {
        console.error('Error animating avatar:', error);
        alert('Error animating avatar: ' + error.response?.data?.detail || error.message);
    }
}

// Intensity slider update
document.getElementById('expression-intensity')?.addEventListener('input', (e) => {
    document.getElementById('intensity-value').textContent = e.target.value;
});

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupFilePreviews();
    loadAvatarOptions();
});