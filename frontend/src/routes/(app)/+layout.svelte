<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { auth } from '$lib/auth.svelte';
	import { ui, closePreview, requestReload } from '$lib/ui.svelte';
	import { deleteFile, downloadDecrypted } from '$lib/files';
	import TopBar from '$lib/components/TopBar.svelte';
	import PreviewModal from '$lib/components/PreviewModal.svelte';
	import MovePicker from '$lib/components/MovePicker.svelte';

	let { children } = $props();

	onMount(() => {
		if (!auth.user) goto('/login', { replaceState: true });
	});

	async function onPreviewDelete(id: string) {
		if (!confirm('Delete this file? This cannot be undone.')) return;
		await deleteFile(id);
		closePreview();
		requestReload();
	}
</script>

<svelte:window onclick={() => (ui.menuId = null)} />

{#if auth.user}
	<div class="shell">
		<TopBar />
		<div class="below">
			{@render children()}
		</div>
	</div>

	{#if ui.preview}
		<PreviewModal
			item={ui.preview}
			onclose={closePreview}
			ondownload={(f) => downloadDecrypted(f)}
			ondelete={(f) => onPreviewDelete(f.id)}
		/>
	{/if}

	{#if ui.moveTarget}
		<MovePicker item={ui.moveTarget} />
	{/if}
{/if}

<style>
	.shell {
		height: 100vh;
		display: flex;
		flex-direction: column;
		background: var(--wf-paper);
		color: var(--wf-ink);
	}
	.below {
		flex: 1;
		min-height: 0;
		display: flex;
	}
</style>
