import { WebSocketServer, WebSocket } from 'ws';
import type { IncomingMessage } from 'http';
import type { Duplex } from 'stream';
import { PrismaClient } from '@prisma/client';

const wss = new WebSocketServer({ noServer: true });
const prisma = new PrismaClient();

// async function main() {
// 	const pin = await prisma.pin.create({
// 		data: {
// 			mcc: 310,
// 			mnc: 260,
// 			lac: 12345,
// 			cid: 67890,
// 			lat: 37.22949,
// 			lng: -80.4194,
// 			speed: 0,
// 			timestamp: new Date(),
// 		},
// 	});
// 	console.log(pin);
// }

// main()

type WebSocketSession = {
	socketId: string;
};

const onConnection = async (ws: WebSocket & WebSocketSession, req: IncomingMessage) => {
	ws.socketId = crypto.randomUUID();
	console.log('connected: %s', ws.socketId);
	ws.on('message', (message) => {
		console.log('received: %s', message);
	});
	console.log(await prisma.pin.findMany());
	ws.send(
		JSON.stringify({
			type: "pins",
			data: await prisma.pin.findMany()
		})
	);
	ws.send('something');
	ws.on('close', () => {
		console.log('disconnected: %s', ws.socketId);
	});
};

wss.on('connection', onConnection);

export const onHttpServerUpgrade = (req: IncomingMessage, socket: Duplex, head: Buffer) => {
	const pathname = req.url
		? new URL(`http://${process.env.HOST ?? 'localhost'}${req.url}`).pathname
		: null;
	if (pathname !== '/websocket') return;

	wss.handleUpgrade(req, socket, head, (ws) => {
		wss.emit('connection', ws, req);
	});
};
