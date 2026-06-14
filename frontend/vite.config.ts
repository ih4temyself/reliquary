import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		host: true,
		watch: process.env.VITE_USE_POLLING ? { usePolling: true } : undefined
	}
});
