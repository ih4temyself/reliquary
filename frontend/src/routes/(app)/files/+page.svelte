<script lang="ts">
	import { onMount, untrack } from 'svelte';
	import { page } from '$app/state';
	import Sidebar from '$lib/components/Sidebar.svelte';
	import Chip from '$lib/components/Chip.svelte';
	import Button from '$lib/components/Button.svelte';
	import Glyph from '$lib/components/Glyph.svelte';
	import UploadModal from '$lib/components/UploadModal.svelte';
	import { auth, refreshUser } from '$lib/auth.svelte';
	import { openPreview, registerReload } from '$lib/ui.svelte';
	import {
		listFiles,
		listFolders,
		createFolder,
		deleteFile,
		downloadDecrypted,
		getDashboard,
		type FileItem,
		type Folder
	} from '$lib/files';

	let folders = $state<Folder[]>([]);
	let files = $state<FileItem[]>([]);
	let usedBytes = $state(0);
	let maxUploadSize = $state(1024 * 1024 * 1024);
	let loading = $state(true);

	const remainingBytes = $derived(
		Math.max((auth.user?.storage_quota ?? 0) - usedBytes, 0)
	);
	let view = $state<'list' | 'grid'>('list');

	const VIEW_LABELS: Record<string, string> = {
		all: 'All files',
		recent: 'Recent',
		photos: 'Photos',
		documents: 'Documents'
	};
	const viewFilter = $derived(page.url.searchParams.get('view') ?? 'all');
	const query = $derived(page.url.searchParams.get('q') ?? '');

	let stack = $state<{ id: string | null; name: string }[]>([{ id: null, name: 'All files' }]);
	let current = $derived(stack[stack.length - 1]);

	let selected = $state<Set<string>>(new Set());
	let menu = $state<{ id: string; x: number; y: number } | null>(null);
	let showUpload = $state(false);

	onMount(() => {
		registerReload(load);
		return () => registerReload(null);
	});

	let filtered = $derived(
		query
			? files.filter((f) => f.name.toLowerCase().includes(query.toLowerCase()))
			: files
	);
	let isEmpty = $derived(!loading && folders.length === 0 && filtered.length === 0);

	const IMG = /\.(png|jpe?g|gif|webp|svg|heic|bmp|avif)$/i;
	const DOC = /\.(pdf|docx?|txt|md|rtf|xlsx?|csv|pptx?|odt|json)$/i;

	function applyView(all: FileItem[], v: string): FileItem[] {
		if (v === 'photos')
			return all.filter((f) => IMG.test(f.name) || f.content_type.startsWith('image/'));
		if (v === 'documents') return all.filter((f) => DOC.test(f.name));
		if (v === 'recent')
			return [...all]
				.sort((a, b) => +new Date(b.updated_at) - +new Date(a.updated_at))
				.slice(0, 30);
		return all;
	}

	async function load() {
		loading = true;
		menu = null;
		selected = new Set();
		try {
			if (query) {
				folders = [];
				files = await listFiles();
			} else if (viewFilter === 'all') {
				const parent = current.id ?? 'root';
				[folders, files] = await Promise.all([listFolders(parent), listFiles(parent)]);
			} else {
				folders = [];
				files = applyView(await listFiles(), viewFilter);
			}
			const dash = await getDashboard();
			usedBytes = dash.total_size;
			maxUploadSize = dash.max_upload_size;
			refreshUser();
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		const v = viewFilter;
		const term = query;
		untrack(() => {
			stack = [{ id: null, name: term ? `Results: "${term}"` : VIEW_LABELS[v] ?? 'All files' }];
			load();
		});
	});

	function openFolder(f: Folder) {
		stack = [...stack, { id: f.id, name: f.name }];
		load();
	}
	function goCrumb(i: number) {
		stack = stack.slice(0, i + 1);
		load();
	}

	function toggleSel(id: string) {
		const next = new Set(selected);
		next.has(id) ? next.delete(id) : next.add(id);
		selected = next;
	}

	async function onNewFolder() {
		const name = prompt('New folder name');
		if (!name) return;
		await createFolder(name, current.id);
		load();
	}

	async function onDelete(id: string) {
		if (!confirm('Delete this file? This cannot be undone.')) return;
		await deleteFile(id);
		load();
	}

	async function onBulkDelete() {
		if (!confirm(`Delete ${selected.size} file(s)?`)) return;
		await Promise.all([...selected].map((id) => deleteFile(id)));
		load();
	}

	async function onBulkDownload() {
		for (const id of selected) {
			const f = files.find((x) => x.id === id);
			if (f) await downloadDecrypted(f);
		}
	}

	function fmtSize(b: number) {
		if (b < 1024) return b + ' B';
		if (b < 1024 * 1024) return (b / 1024).toFixed(0) + ' KB';
		if (b < 1024 * 1024 * 1024) return (b / 1024 / 1024).toFixed(1) + ' MB';
		return (b / 1024 / 1024 / 1024).toFixed(2) + ' GB';
	}
	function fmtDate(s: string) {
		return new Date(s).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
	}
	function iconFor(name: string) {
		return /\.(png|jpe?g|gif|webp|svg|heic)$/i.test(name) ? 'img' : 'file';
	}

	function onRowMenu(e: MouseEvent, id: string) {
		e.preventDefault();
		menu = { id, x: e.clientX, y: e.clientY };
	}
	const menuFile = $derived(menu ? files.find((f) => f.id === menu!.id) ?? null : null);
</script>

<svelte:window onclick={() => (menu = null)} />

<div class="app">
	<Sidebar activeView={viewFilter} {usedBytes} totalBytes={auth.user?.storage_quota ?? undefined} />

	<div class="body">
		<div class="toolbar">
			<div class="crumbrow">
				{#each stack as s, i (i)}
					<button class="crumbbtn" class:cur={i === stack.length - 1} onclick={() => goCrumb(i)}>
						{s.name}
					</button>
					{#if i < stack.length - 1}<span class="csep">›</span>{/if}
				{/each}
			</div>
			<div class="actions">
				<Button sm onclick={onNewFolder}>
					<Glyph type="plus" size={13} color="var(--wf-ink)" /> New folder
				</Button>
				<Button sm primary onclick={() => (showUpload = true)}>Upload</Button>
			</div>
		</div>

		<div class="subbar">
			<div class="sorts">
				<Chip active>Name ↓</Chip>
				<Chip>Type</Chip>
				<Chip>Modified</Chip>
			</div>
			<div class="toggle">
				<Chip active={view === 'list'} onclick={() => (view = 'list')}>List</Chip>
				<Chip active={view === 'grid'} onclick={() => (view = 'grid')}>Grid</Chip>
			</div>
		</div>

			{#if selected.size > 0}
				<div class="bulkbar">
					<span class="check">✓</span>
					<span>{selected.size} selected</span>
					<div class="bulkactions">
						<Button sm onclick={onBulkDownload}>Download</Button>
						<Button sm disabled>Move to…</Button>
						<Button sm onclick={onBulkDelete}>Delete</Button>
					</div>
				</div>
			{/if}

			<div class="sheet">
				{#if loading}
					<div class="state">Loading…</div>
				{:else if isEmpty}
					<div class="empty">
						<Glyph type="folder" size={48} color="var(--wf-line)" />
						<span class="wf-script big">This folder is empty</span>
						<span class="sub">Drag files here, or use the buttons to add something.</span>
						<div class="erow">
							<Button onclick={onNewFolder}>
								<Glyph type="plus" size={14} color="var(--wf-ink)" /> New folder
							</Button>
							<Button primary onclick={() => (showUpload = true)}>Upload files</Button>
						</div>
					</div>
				{:else if view === 'list'}
					<div class="thead">
						<span></span><span></span><span>Name</span><span>Modified</span><span>Size</span><span></span>
					</div>
					<div class="rows">
						{#each folders as f (f.id)}
							<div class="row folder" ondblclick={() => openFolder(f)} role="row" tabindex="0">
								<span></span>
								<Glyph type="folder" size={18} color="var(--wf-accent)" />
								<button class="name" onclick={() => openFolder(f)}>{f.name}</button>
								<span class="meta">{fmtDate(f.created_at)}</span>
								<span class="meta">—</span>
								<Glyph type="dots" size={16} color="var(--wf-faint)" />
							</div>
						{/each}
						{#each filtered as f (f.id)}
							<div
								class="row"
								class:sel={selected.has(f.id)}
								oncontextmenu={(e) => onRowMenu(e, f.id)}
								role="row"
								tabindex="0"
							>
								<button
									class="cb"
									class:on={selected.has(f.id)}
									onclick={() => toggleSel(f.id)}
									aria-label="Select"
								>
									{selected.has(f.id) ? '✓' : ''}
								</button>
								<Glyph type={iconFor(f.name)} size={18} />
								<button class="name" onclick={() => openPreview(f)}>{f.name}</button>
								<span class="meta">{fmtDate(f.updated_at)}</span>
								<span class="meta">{fmtSize(f.encrypted_size)}</span>
								<button class="dots" onclick={(e) => onRowMenu(e, f.id)} aria-label="Menu">
									<Glyph type="dots" size={16} color="var(--wf-faint)" />
								</button>
							</div>
						{/each}
					</div>
				{:else}
					<div class="grid">
						{#each folders as f (f.id)}
							<button class="tile folder" ondblclick={() => openFolder(f)} onclick={() => openFolder(f)}>
								<Glyph type="folder" size={24} color="var(--wf-accent)" />
								<span class="tname">{f.name}</span>
							</button>
						{/each}
						{#each filtered as f (f.id)}
							<button class="tile" onclick={() => openPreview(f)}>
								<div class="thumb">{f.name.split('.').pop()}</div>
								<span class="tname">{f.name}</span>
							</button>
						{/each}
					</div>
				{/if}
			</div>
		</div>
</div>

{#if menu && menuFile}
	<div class="ctx" style="left:{menu.x}px;top:{menu.y}px">
		<button onclick={() => menuFile && openPreview(menuFile)}><Glyph type="file" size={15} color="var(--wf-faint)" />Open</button>
		<button onclick={() => menuFile && downloadDecrypted(menuFile)}><Glyph type="file" size={15} color="var(--wf-faint)" />Download</button>
		<button disabled><Glyph type="square" size={15} color="var(--wf-faint)" />Rename</button>
		<button disabled><Glyph type="folder" size={15} color="var(--wf-faint)" />Move to…</button>
		<div class="sep"></div>
		<button class="danger" onclick={() => menu && onDelete(menu.id)}>
			<Glyph type="square" size={15} color="var(--wf-danger)" />Delete
		</button>
	</div>
{/if}

{#if showUpload}
	<UploadModal
		folder={current.id}
		{maxUploadSize}
		{remainingBytes}
		onclose={() => (showUpload = false)}
		ondone={load}
	/>
{/if}

<style>
	.app {
		display: flex;
		flex: 1;
		min-height: 0;
		background: var(--wf-paper);
		color: var(--wf-ink);
	}
	.body {
		padding: 16px 22px;
		display: flex;
		flex-direction: column;
		gap: 14px;
		flex: 1;
		min-width: 0;
		min-height: 0;
	}
	.toolbar {
		display: flex;
		align-items: center;
		gap: 14px;
	}
	.actions {
		margin-left: auto;
		display: flex;
		gap: 8px;
	}
	.subbar {
		display: flex;
		align-items: center;
		gap: 14px;
	}
	.crumbrow {
		display: flex;
		align-items: center;
		gap: 8px;
		font-size: 13px;
		color: var(--wf-sub);
	}
	.crumbbtn {
		background: none;
		border: none;
		color: var(--wf-sub);
		cursor: pointer;
		font-size: 13px;
		padding: 0;
	}
	.crumbbtn.cur {
		color: var(--wf-ink);
	}
	.csep {
		color: var(--wf-faint);
	}
	.toggle {
		margin-left: auto;
		display: flex;
		gap: 7px;
	}
	.sorts {
		display: flex;
		gap: 7px;
	}
	.bulkbar {
		display: flex;
		align-items: center;
		gap: 14px;
		padding: 9px 16px;
		background: var(--wf-accent-soft);
		border: 2px solid var(--wf-accent);
		font-size: 13px;
	}
	.bulkbar .check {
		width: 16px;
		height: 16px;
		background: var(--wf-accent);
		color: #fff;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 11px;
	}
	.bulkactions {
		margin-left: auto;
		display: flex;
		gap: 8px;
	}
	.sheet {
		flex: 1;
		min-height: 0;
		border: 2px solid var(--wf-ink);
		background: var(--wf-paper);
		padding: 8px 16px;
		display: flex;
		flex-direction: column;
		overflow: auto;
	}
	.thead,
	.row {
		display: grid;
		grid-template-columns: 22px 26px 1fr 130px 80px 24px;
		align-items: center;
		gap: 12px;
	}
	.thead {
		padding: 4px 4px 8px;
		border-bottom: 2px solid var(--wf-line);
		font-size: 11px;
		color: var(--wf-faint);
	}
	.rows {
		display: flex;
		flex-direction: column;
	}
	.row {
		padding: 9px 4px;
		border-bottom: 1.5px dashed var(--wf-line);
		border-radius: 8px;
	}
	.row.sel {
		background: var(--wf-accent-soft);
	}
	.cb {
		width: 16px;
		height: 16px;
		border: 2px solid var(--wf-line);
		background: transparent;
		color: #fff;
		font-size: 11px;
		display: flex;
		align-items: center;
		justify-content: center;
		cursor: pointer;
		padding: 0;
	}
	.cb.on {
		background: var(--wf-accent);
		border-color: var(--wf-accent);
	}
	.name {
		background: none;
		border: none;
		text-align: left;
		color: var(--wf-ink);
		font-size: 13px;
		cursor: pointer;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		padding: 0;
	}
	.name:hover {
		color: var(--wf-accent);
	}
	.meta {
		font-size: 12px;
		color: var(--wf-sub);
	}
	.dots {
		background: none;
		border: none;
		cursor: pointer;
		padding: 0;
	}
	.folder .name {
		font-weight: 500;
	}
	.empty {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 16px;
		text-align: center;
		padding: 30px;
	}
	.empty .big {
		font-size: 26px;
	}
	.empty .sub {
		font-size: 13px;
		color: var(--wf-sub);
		max-width: 320px;
	}
	.erow {
		display: flex;
		gap: 10px;
		margin-top: 4px;
	}
	.state {
		padding: 40px;
		text-align: center;
		color: var(--wf-faint);
	}
	.grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
		gap: 14px;
	}
	.tile {
		border: 2px solid var(--wf-ink);
		background: var(--wf-paper);
		padding: 12px;
		display: flex;
		flex-direction: column;
		gap: 8px;
		cursor: pointer;
		text-align: left;
		color: var(--wf-ink);
	}
	.thumb {
		height: 80px;
		border: 2px solid var(--wf-line);
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--wf-faint);
		font-size: 11px;
		text-transform: uppercase;
		background: repeating-linear-gradient(45deg, transparent 0 9px, var(--wf-hatch) 9px 10px);
	}
	.tname {
		font-size: 12px;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.ctx {
		position: fixed;
		z-index: 60;
		width: 190px;
		background: var(--wf-paper);
		border: 2px solid var(--wf-ink);
		padding: 6px;
		display: flex;
		flex-direction: column;
		gap: 2px;
		box-shadow: 4px 6px 0 rgba(0, 0, 0, 0.25);
	}
	.ctx button {
		display: flex;
		align-items: center;
		gap: 9px;
		padding: 7px 9px;
		background: none;
		border: none;
		text-align: left;
		font-size: 12px;
		color: var(--wf-ink);
		cursor: pointer;
	}
	.ctx button:hover:not(:disabled) {
		background: var(--wf-fill-soft);
	}
	.ctx button:disabled {
		color: var(--wf-faint);
		cursor: default;
	}
	.ctx .danger {
		color: var(--wf-danger);
	}
	.ctx .sep {
		border-top: 1.5px dashed var(--wf-line);
		margin: 3px 4px;
	}
</style>
