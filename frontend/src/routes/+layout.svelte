<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { auth, loadSession } from '$lib/auth.svelte';

	let { children } = $props();

	onMount(loadSession);
</script>

{#if auth.ready}
	{@render children()}
{:else}
	<div class="boot">Loading…</div>
{/if}

<style>
	.boot {
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--wf-faint);
		font-size: 13px;
	}
</style>
