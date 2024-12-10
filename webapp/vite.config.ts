import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import Icons from 'unplugin-icons/vite';

import { onHttpServerUpgrade } from './src/lib/ws/server';

export default defineConfig({
	plugins: [
		sveltekit(),
		{
			name: 'ws',
			configureServer(server) {
				server.httpServer?.on('upgrade', onHttpServerUpgrade);
			},
			configurePreviewServer(server) {
				server.httpServer?.on('upgrade', onHttpServerUpgrade);
			}
		},
		Icons({
			compiler: 'svelte'
		})
	]
	// server: {
	// 	proxy: {
	// 		'/cellmapper': 'https://api.cellmapper.net/v6'
	// 	}
	// }
});
