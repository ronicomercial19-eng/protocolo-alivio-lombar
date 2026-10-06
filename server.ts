import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import bcrypt from 'bcryptjs';
import { GoogleGenAI, Modality } from "@google/genai";
import { WebSocketServer } from "ws";
import { initializeApp } from 'firebase-admin/app';
import { getAuth } from 'firebase-admin/auth';
import { getFirestore } from 'firebase-admin/firestore';

// Initialize Firebase Admin
initializeApp();
const adminAuth = getAuth();
const adminDb = getFirestore();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = 3000;

app.use(express.json());

// Initialize Gemini client
const ai = new GoogleGenAI({
  apiKey: process.env.GEMINI_API_KEY,
  httpOptions: {
    headers: { 'User-Agent': 'aistudio-build' }
  }
});

// API Routes
const users = new Map(); // email -> {name, passwordHash, ...}

app.post('/api/register', async (req, res) => {
    const { name, email, password, consent } = req.body;
    if (!name || !email || !password || !consent) return res.status(400).json({ error: 'Missing fields' });
    if (users.has(email)) return res.status(409).json({ error: 'User already exists' });
    const hashedPassword = await bcrypt.hash(password, 10);
    users.set(email, { name, passwordHash: hashedPassword, role: 'participant', state: 'active' });
    res.json({ ok: true });
});

app.post('/api/login', async (req, res) => {
    const { email, password } = req.body;
    const user = users.get(email);
    if (!user || !(await bcrypt.compare(password, user.passwordHash))) return res.status(401).json({ error: 'Invalid credentials' });
    res.json({ ok: true, name: user.name });
});

app.post('/api/login-google', async (req, res) => {
    const { email, name } = req.body;
    if (!email || !name) return res.status(400).json({ error: 'Missing fields' });
    let user = users.get(email);
    if (!user) {
        user = { name, role: 'participant', state: 'active', passwordHash: 'google' };
        users.set(email, user);
    }
    // Simple session simulation by returning user info
    res.json({ ok: true, name: user.name, role: user.role, state: user.state, email: email });
});

app.get('/api/me', (req, res) => {
    // In this simplified version, me is not really a session-based endpoint.
    // For now, return a placeholder or handle it differently.
    // Actually, app.js calls it to get the user.
    res.json({ name: 'User', role: 'participant', state: 'active' });
});

app.post('/api/chat', async (req, res) => {
    try {
        const { messages, taskComplexity } = req.body;
        // Model selection
        let model = "gemini-3.5-flash";
        if (taskComplexity === 'complex') model = "gemini-3.1-pro-preview";
        else if (taskComplexity === 'fast') model = "gemini-3.1-flash-lite";

        const response = await ai.models.generateContent({
            model: model,
            contents: messages.map((m: any) => ({ role: m.role, parts: [{ text: m.text }] })),
            config: { 
                systemInstruction: "Você é um assistente especializado em protocolo de alívio lombar. Analise o progresso, as variáveis do usuário e dê feedback guiado.",
                tools: [{ googleSearch: {} }]
            }
        });
        res.json({ text: response.text });
    } catch (e: any) {
        res.status(500).json({ error: e.message });
    }
});

app.post('/api/transcribe', async (req, res) => {
    try {
        const { audioData, mimeType } = req.body;
        const response = await ai.models.generateContent({
            model: "gemini-3.5-transcribe",
            contents: { parts: [{ inlineData: { data: audioData, mimeType } }, { text: "Transcreva este áudio." }] }
        });
        res.json({ text: response.text });
    } catch (e: any) {
        res.status(500).json({ error: e.message });
    }
});

// Static files
app.use(express.static(path.join(__dirname, 'web')));

const server = app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server running on http://0.0.0.0:${PORT}`);
});

// Live API WebSocket handler
const wss = new WebSocketServer({ server, path: '/live' });
wss.on("connection", async (clientWs) => {
    const session = await ai.live.connect({
        model: "gemini-3.8-live",
        config: {
            responseModalities: [Modality.AUDIO],
            speechConfig: { voiceConfig: { prebuiltVoiceConfig: { voiceName: "Zephyr" } } },
            systemInstruction: "Você é um assistente de voz para o protocolo de alívio lombar. Guie o usuário durante a execução dos exercícios.",
        },
        callbacks: {
            onmessage: (message: any) => {
                const audio = message.serverContent?.modelTurn?.parts[0]?.inlineData?.data;
                if (audio) clientWs.send(JSON.stringify({ audio }));
            },
        },
    });

    clientWs.on("message", (data) => {
        const { audio } = JSON.parse(data.toString());
        session.sendRealtimeInput({
            audio: { data: audio, mimeType: "audio/pcm;rate=16000" },
        });
    });
});
