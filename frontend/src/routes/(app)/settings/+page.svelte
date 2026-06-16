<script lang="ts">
	import { auth, refreshUser } from '$lib/auth.svelte';
	import { onMount } from 'svelte';
	import Button from '$lib/components/Button.svelte';
	import { apiJson, ApiError } from '$lib/api';

	const nav = ['Account', 'Storage', 'Notifications', 'Security', 'Connected apps'];

	let name = $state(auth.user?.display_name ?? '');
	let email = $state(auth.user?.email ?? '');
	let saving = $state(false);
	let saved = $state(false);
	let serverError = $state('');

	const used = $derived(auth.user?.storage_used ?? 0);
	const total = $derived(auth.user?.storage_quota ?? 15 * 1024 * 1024 * 1024);
	const pct = $derived(Math.min(100, total ? (used / total) * 100 : 0));
	const gb = (b: number) => (b / 1024 / 1024 / 1024).toFixed(1);

	const trimmed = $derived(name.trim());
	const nameError = $derived(
		trimmed === ''
			? 'Name is required.'
			: trimmed.toLowerCase() === 'unnamed'
				? '“Unnamed” isn’t allowed — pick a real name.'
				: trimmed.length < 2
					? 'Name must be at least 2 characters.'
					: ''
	);
	const dirty = $derived(trimmed !== (auth.user?.display_name ?? ''));
	const canSave = $derived(!nameError && dirty && !saving);
	const initial = $derived((trimmed || email || '?').charAt(0).toUpperCase());

	onMount(refreshUser);

	async function save() {
		if (!canSave) return;
		saving = true;
		saved = false;
		serverError = '';
		try {
			const updated = await apiJson<typeof auth.user>('/auth/me/', {
				method: 'PATCH',
				body: JSON.stringify({ display_name: trimmed })
			});
			if (updated) auth.user = updated;
			name = trimmed;
			saved = true;
			setTimeout(() => (saved = false), 2500);
		} catch (e) {
			if (e instanceof ApiError) {
				const d = e.detail as Record<string, string[]> | string;
				serverError =
					typeof d === 'string' ? d : Object.values(d).flat().join(' ') || 'Could not save.';
			} else {
				serverError = (e as Error).message;
			}
		} finally {
			saving = false;
		}
	}
</script>

<div class="settings">
	<div class="nav">
		<a class="back" href="/files">‹ Back to files</a>
		<span class="wf-script title">Settings</span>
		{#each nav as n, i (n)}
			<div class="navitem" class:active={i === 0}>{n}</div>
		{/each}
	</div>

	<div class="panel">
		<div class="profile">
			<span class="avatar">{initial}</span>
			<div class="who">
				<span class="dn">{trimmed || 'Unnamed'}</span>
				<span class="em">{email}</span>
			</div>
			<Button sm disabled>Change photo</Button>
		</div>

		<label class:invalid={nameError}>
			<span class="lbl">Name</span>
			<input
				bind:value={name}
				placeholder="Your name"
				aria-invalid={!!nameError}
				onkeydown={(e) => e.key === 'Enter' && save()}
			/>
			{#if nameError}
				<span class="hint err">{nameError}</span>
			{:else}
				<span class="hint">This is how you’ll appear across Reliquary.</span>
			{/if}
		</label>

		<label>
			<span class="lbl">Email</span>
			<input value={email} disabled />
			<span class="hint">Email can’t be changed.</span>
		</label>

		<div class="storage">
			<div class="srow">
				<span class="slabel">Storage</span>
				<span class="sval">{gb(used)} / {gb(total)} GB</span>
			</div>
			<div class="track"><span style="width:{pct}%"></span></div>
			<span class="sfoot">{pct.toFixed(pct < 10 ? 1 : 0)}% of your space used</span>
		</div>

		<div class="actions">
			<Button primary onclick={save} disabled={!canSave}>
				{saving ? 'Saving…' : 'Save changes'}
			</Button>
			{#if saved}<span class="ok">Saved ✓</span>{/if}
			{#if serverError}<span class="srverr">{serverError}</span>{/if}
			{#if !dirty && !saved}<span class="muted">No changes</span>{/if}
		</div>
	</div>
</div>

<style>
	.settings {
		flex: 1;
		min-height: 0;
		display: flex;
	}
	.nav {
		width: 220px;
		border-right: 2px solid var(--wf-ink);
		padding: 22px 16px;
		display: flex;
		flex-direction: column;
		gap: 6px;
		flex-shrink: 0;
		background: var(--wf-fill-soft);
	}
	.back {
		font-size: 12px;
		color: var(--wf-sub);
		margin-bottom: 6px;
	}
	.back:hover {
		color: var(--wf-accent);
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
		background: var(--wf-paper);
		border-color: var(--wf-line);
		color: var(--wf-ink);
	}
	.panel {
		flex: 1;
		padding: 30px 34px;
		display: flex;
		flex-direction: column;
		gap: 22px;
		max-width: 560px;
		overflow: auto;
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
		color: var(--wf-accent);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 26px;
		flex-shrink: 0;
	}
	.who {
		display: flex;
		flex-direction: column;
		gap: 4px;
		min-width: 0;
	}
	.dn {
		font-size: 16px;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
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
	.lbl {
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
	label.invalid input {
		border-color: var(--wf-danger);
	}
	.hint {
		font-size: 11px;
		color: var(--wf-faint);
	}
	.hint.err {
		color: var(--wf-danger);
	}
	.storage {
		display: flex;
		flex-direction: column;
		gap: 9px;
		margin-top: 4px;
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
		transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
	}
	.sfoot {
		font-size: 10px;
		color: var(--wf-faint);
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
	.srverr {
		font-size: 12px;
		color: var(--wf-danger);
	}
	.muted {
		font-size: 12px;
		color: var(--wf-faint);
	}
</style>
