import { WebSocketServer, WebSocket } from 'ws';
import type { IncomingMessage } from 'http';
import type { Duplex } from 'stream';

const wss = new WebSocketServer({ noServer: true });

type WebSocketSession = {
	socketId: string;
};

const onConnection = (ws: WebSocket & WebSocketSession, req: IncomingMessage) => {
	ws.socketId = crypto.randomUUID();
	console.log('connected: %s', ws.socketId);
	ws.on('message', (message) => {
		console.log('received: %s', message);
	});

	ws.send('something');
	ws.on('close', () => {
		console.log('disconnected: %s', ws.socketId);
	});
};

wss.on('connection', onConnection);

export const onHttpServerUpgrade = (req: IncomingMessage, socket: Duplex, head: Buffer) => {
	const pathname = req.url ? new URL(`http://${process.env.HOST ?? 'localhost'}${req.url}`).pathname : null;
	if (pathname !== '/websocket') return;

	wss.handleUpgrade(req, socket, head, (ws) => {
		wss.emit('connection', ws, req);
	});
};
