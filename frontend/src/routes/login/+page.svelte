<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { auth, login, register } from '$lib/auth.svelte';
	import { ApiError } from '$lib/api';
	import Button from '$lib/components/Button.svelte';

	let tab = $state<'login' | 'signup'>('login');
	let email = $state('');
	let password = $state('');
	let displayName = $state('');
	let busy = $state(false);
	let error = $state('');

	onMount(() => {
		if (auth.user) goto('/files', { replaceState: true });
	});

	async function submit(e: SubmitEvent) {
		e.preventDefault();
		error = '';
		busy = true;
		try {
			if (tab === 'login') await login(email, password);
			else await register(email, password, displayName);
			goto('/files', { replaceState: true });
		} catch (err) {
			if (err instanceof ApiError) {
				const d = err.detail as Record<string, string[]> | string;
				error =
					typeof d === 'string'
						? d
						: Object.values(d).flat().join(' ') || 'Something went wrong.';
			} else {
				error = (err as Error).message;
			}
		} finally {
			busy = false;
		}
	}
</script>

<div class="screen">
	<div class="card">
		<div class="brand">
			<div class="logo">
				<span class="mark"></span>
				<span class="wf-script logoname">Reliquary</span>
			</div>
			<p class="wf-script tagline">All your files,<br />light & in one place.</p>
			<div class="shot">end-to-end encrypted</div>
		</div>

		<form class="form" onsubmit={submit}>
			<div class="tabs">
				<button type="button" class="tab" class:active={tab === 'login'} onclick={() => (tab = 'login')}>
					Log in
				</button>
				<button
					type="button"
					class="tab"
					class:active={tab === 'signup'}
					onclick={() => (tab = 'signup')}
				>
					Sign up
				</button>
			</div>

			{#if tab === 'signup'}
				<label>
					<span>Name</span>
					<input bind:value={displayName} placeholder="Your name" autocomplete="name" />
				</label>
			{/if}
			<label>
				<span>Email</span>
				<input type="email" bind:value={email} required placeholder="you@example.com" autocomplete="email" />
			</label>
			<label>
				<span>Password</span>
				<input
					type="password"
					bind:value={password}
					required
					placeholder="••••••••"
					autocomplete={tab === 'login' ? 'current-password' : 'new-password'}
				/>
			</label>

			{#if error}<p class="error">{error}</p>{/if}

			<Button primary type="submit" disabled={busy}>
				{busy ? 'Please wait…' : tab === 'login' ? 'Log in →' : 'Create account →'}
			</Button>

			<div class="divider"><span>or</span></div>
			<Button disabled>Continue with Google</Button>
		</form>
	</div>
</div>

<style>
	.screen {
		min-height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 24px;
	}
	.card {
		display: flex;
		width: 860px;
		max-width: 100%;
		min-height: 560px;
		background: var(--wf-paper);
		border: 2px solid var(--wf-ink);
		overflow: hidden;
	}
	.brand {
		width: 44%;
		background: var(--wf-fill-soft);
		border-right: 2px solid var(--wf-ink);
		padding: 34px;
		display: flex;
		flex-direction: column;
		gap: 16px;
	}
	.logo {
		display: flex;
		align-items: center;
		gap: 9px;
	}
	.mark {
		width: 22px;
		height: 22px;
		background: var(--wf-accent);
	}
	.logoname {
		font-size: 28px;
		line-height: 1;
	}
	.tagline {
		font-size: 30px;
		line-height: 1.2;
		margin: 18px 0 0;
	}
	.shot {
		margin-top: auto;
		height: 200px;
		border: 2px solid var(--wf-line);
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--wf-faint);
		font-size: 11px;
		background: repeating-linear-gradient(45deg, transparent 0 9px, var(--wf-hatch) 9px 10px);
	}
	.form {
		flex: 1;
		padding: 40px 44px;
		display: flex;
		flex-direction: column;
		justify-content: center;
		gap: 16px;
	}
	.tabs {
		display: flex;
		gap: 18px;
		border-bottom: 1.5px dashed var(--wf-line);
		padding-bottom: 4px;
		margin-bottom: 4px;
	}
	.tab {
		font-size: 16px;
		background: none;
		border: none;
		color: var(--wf-faint);
		padding: 0 0 6px;
		cursor: pointer;
		border-bottom: 3px solid transparent;
	}
	.tab.active {
		color: var(--wf-ink);
		border-bottom-color: var(--wf-accent);
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
	input:focus {
		border-color: var(--wf-accent);
	}
	.error {
		margin: 0;
		font-size: 12px;
		color: var(--wf-danger);
	}
	.divider {
		display: flex;
		align-items: center;
		gap: 10px;
		color: var(--wf-faint);
		font-size: 11px;
	}
	.divider::before,
	.divider::after {
		content: '';
		flex: 1;
		border-top: 1.5px dashed var(--wf-line);
	}
</style>
