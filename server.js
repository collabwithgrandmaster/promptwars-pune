const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = 3000;
const DATA_FILE = path.join(__dirname, 'users.json');

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(__dirname));

// Helper to read data
function readData() {
    if (!fs.existsSync(DATA_FILE)) {
        return {};
    }
    const raw = fs.readFileSync(DATA_FILE, 'utf-8');
    try {
        return JSON.parse(raw);
    } catch (e) {
        return {};
    }
}

// Helper to write data
function writeData(data) {
    fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 2), 'utf-8');
}

// API: Step 1 (Create User Profile)
app.post('/api/onboarding/step1', (req, res) => {
    const { name, age, hobbies, favorites } = req.body;
    
    // Generate a simple unique ID
    const userId = 'user_' + Date.now() + Math.floor(Math.random() * 1000);
    
    const db = readData();
    db[userId] = {
        id: userId,
        name,
        age,
        hobbies,
        favorites,
        createdAt: new Date().toISOString()
    };
    
    writeData(db);
    res.json({ success: true, userId, user: db[userId] });
});

// API: Step 2 (Update User Profile with Skills/Goals)
app.post('/api/onboarding/step2', (req, res) => {
    const { userId, skills, successMetric } = req.body;
    
    if (!userId) return res.status(400).json({ error: 'User ID is required' });
    
    const db = readData();
    if (!db[userId]) {
        return res.status(404).json({ error: 'User not found' });
    }
    
    db[userId].skills = skills;
    db[userId].successMetric = successMetric;
    db[userId].updatedAt = new Date().toISOString();
    
    writeData(db);
    res.json({ success: true, user: db[userId] });
});

// API: Get User Profile
app.get('/api/user/:id', (req, res) => {
    const userId = req.params.id;
    const db = readData();
    
    if (!db[userId]) {
        return res.status(404).json({ error: 'User not found' });
    }
    
    res.json({ success: true, user: db[userId] });
});

app.listen(PORT, () => {
    console.log(`Backend server running at http://localhost:${PORT}`);
    console.log(`Open http://localhost:${PORT}/index.html to start the onboarding flow.`);
});
