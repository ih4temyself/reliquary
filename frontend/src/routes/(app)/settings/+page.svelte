<script lang="ts">
	import { auth, refreshUser } from '$lib/auth.svelte';
	import { onMount } from 'svelte';
	import TopBar from '$lib/components/TopBar.svelte';
	import Button from '$lib/components/Button.svelte';
	import { apiJson } from '$lib/api';

	const nav = ['Account', 'Storage', 'Notifications', 'Security', 'Connected apps'];

	let name = $state(auth.user?.display_name ?? '');
	let email = $state(auth.user?.email ?? '');
	let saving = $state(false);
	let saved = $state(false);

	const used = $derived(auth.user?.storage_used ?? 0);
	const total = $derived(auth.user?.storage_quota ?? 15 * 1024 * 1024 * 1024);
	const pct = $derived(Math.min(100, total ? (used / total) * 100 : 0));
	const gb = (b: number) => (b / 1024 / 1024 / 1024).toFixed(1);

	onMount(refreshUser);

	async function save() {
		saving = true;
		saved = false;
		try {
			const updated = await apiJson<typeof auth.user>('/auth/me/', {
				method: 'PATCH',
				body: JSON.stringify({ display_name: name })
			});
			if (updated) auth.user = updated;
			saved = true;
		} finally {
			saving = false;
		}
	}
</script>

<div class="screen">
	<TopBar showSearch={false} />

	<div class="body">
		<div class="nav">
			<a class="back" href="/files">‹ Back to files</a>
			<span class="wf-script title">Settings</span>
			{#each nav as n, i (n)}
				<div class="navitem" class:active={i === 0}>{n}</div>
			{/each}
		</div>

		<div class="panel">
			<div class="profile">
				<span class="avatar"></span>
				<div class="who">
					<span class="dn">{name || 'Unnamed'}</span>
					<span class="em">{email}</span>
				</div>
				<Button sm disabled>Change photo</Button>
			</div>

			<label>
				<span>Name</span>
				<input bind:value={name} placeholder="Your name" />
			</label>
			<label>
				<span>Email</span>
				<input value={email} disabled />
			</label>

			<div class="storage">
				<div class="srow">
					<span class="slabel">Storage</span>
					<span class="sval">{gb(used)} / {gb(total)} GB</span>
				</div>
				<div class="track"><span style="width:{pct}%"></span></div>
			</div>

			<div class="actions">
				<Button primary onclick={save} disabled={saving}>
					{saving ? 'Saving…' : 'Save changes'}
				</Button>
				{#if saved}<span class="ok">Saved ✓</span>{/if}
			</div>
		</div>
	</div>
</div>

<style>
	.screen {
		height: 100vh;
		display: flex;
		flex-direction: column;
		background: var(--wf-paper);
		color: var(--wf-ink);
	}
	.body {
		flex: 1;
		display: flex;
		min-height: 0;
	}
	.nav {
		width: 220px;
		border-right: 2px solid var(--wf-ink);
		padding: 22px 16px;
		display: flex;
		flex-direction: column;
		gap: 6px;
		flex-shrink: 0;
	}
	.back {
		font-size: 12px;
		color: var(--wf-sub);
		margin-bottom: 6px;
	}
	.title {
		font-size: 26px;
		line-height: 1;
		margin-bottom: 10px;
	}
	.navitem {
		padding: 9px 11px;
		border-radius: 8px;
		color: var(--wf-sub);
		font-size: 13px;
		border: 1.5px solid transparent;
	}
	.navitem.active {
		background: var(--wf-fill-soft);
		border-color: var(--wf-line);
		color: var(--wf-ink);
	}
	.panel {
		flex: 1;
		padding: 26px 34px;
		display: flex;
		flex-direction: column;
		gap: 22px;
		max-width: 560px;
	}
	.profile {
		display: flex;
		align-items: center;
		gap: 16px;
	}
	.avatar {
		width: 64px;
		height: 64px;
		border-radius: 50%;
		border: 2px solid var(--wf-ink);
		background: var(--wf-fill);
		flex-shrink: 0;
	}
	.who {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}
	.dn {
		font-size: 15px;
	}
	.em {
		font-size: 12px;
		color: var(--wf-sub);
	}
	.profile :global(.btn) {
		margin-left: auto;
	}
	label {
		display: flex;
		flex-direction: column;
		gap: 6px;
	}
	label span {
		font-size: 12px;
		color: var(--wf-sub);
	}
	input {
		padding: 11px 13px;
		background: var(--wf-fill-soft);
		border: 2px solid var(--wf-ink);
		outline: none;
		font-size: 13px;
	}
	input:disabled {
		color: var(--wf-faint);
	}
	input:focus {
		border-color: var(--wf-accent);
	}
	.storage {
		display: flex;
		flex-direction: column;
		gap: 9px;
	}
	.srow {
		display: flex;
		justify-content: space-between;
	}
	.slabel {
		font-size: 12px;
		color: var(--wf-sub);
	}
	.sval {
		font-size: 11px;
		color: var(--wf-faint);
	}
	.track {
		height: 12px;
		background: var(--wf-fill);
		border: 1.5px solid var(--wf-line);
		overflow: hidden;
	}
	.track span {
		display: block;
		height: 100%;
		background: var(--wf-accent);
	}
	.actions {
		display: flex;
		align-items: center;
		gap: 12px;
	}
	.ok {
		font-size: 12px;
		color: var(--wf-accent);
	}
</style>
