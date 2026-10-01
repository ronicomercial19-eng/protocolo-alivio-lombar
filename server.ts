import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import bcrypt from 'bcryptjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = 3000;

app.use(express.json());

// Serve static files
app.use(express.static(path.join(__dirname, 'web')));

// API Mock routes
const users = new Map(); // email -> {name, passwordHash, ...}

app.post('/api/register', async (req, res) => {
    const { name, email, password, consent } = req.body;
    if (!name || !email || !password || !consent) {
        return res.status(400).json({ error: 'Missing fields' });
    }
    if (users.has(email)) {
        return res.status(409).json({ error: 'User already exists' });
    }
    const hashedPassword = await bcrypt.hash(password, 10);
    users.set(email, { name, passwordHash: hashedPassword, role: 'participant', state: 'active' });
    res.json({ ok: true });
});

app.post('/api/login', async (req, res) => {
    const { email, password } = req.body;
    const user = users.get(email);
    if (!user || !(await bcrypt.compare(password, user.passwordHash))) {
        return res.status(401).json({ error: 'Invalid credentials' });
    }
    res.json({ ok: true, name: user.name });
});

// Serve index.html for SPA
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'web', 'index.html'));
});

app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server running on http://0.0.0.0:${PORT}`);
});
