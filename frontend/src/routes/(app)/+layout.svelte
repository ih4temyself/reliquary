<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { auth } from '$lib/auth.svelte';

	let { children } = $props();

	onMount(() => {
		if (!auth.user) goto('/login', { replaceState: true });
	});
</script>

{#if auth.user}
	{@render children()}
{/if}
