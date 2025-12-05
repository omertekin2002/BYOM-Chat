<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { getContext, onMount } from 'svelte';
	import { config, user } from '$lib/stores';

	import Modal from '$lib/components/common/Modal.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';

	import {
		getVideoConfig,
		getVideoModels,
		createVideo,
		getVideoStatus,
		getVideoContentUrl,
		listVideos,
		deleteVideo
	} from '$lib/apis/videos';

	const i18n = getContext('i18n');

	export let show = false;

	let loading = false;
	let generating = false;
	let prompt = '';
	let model = 'sora-2';
	let duration = '4';
	let size = '1920x1080';
	let quality = 'standard';

	let models: { id: string; name: string }[] = [];
	let videoConfig: any = null;
	let generatedVideos: any[] = [];
	let currentJob: any = null;
	let pollInterval: any = null;

	const loadConfig = async () => {
		try {
			videoConfig = await getVideoConfig(localStorage.token);
			if (videoConfig) {
				model = videoConfig.VIDEO_GENERATION_MODEL || 'sora-2';
				duration = videoConfig.VIDEO_DURATION || '4';
				size = videoConfig.VIDEO_SIZE || '1920x1080';
				quality = videoConfig.VIDEO_QUALITY || 'standard';
			}
		} catch (error) {
			console.error('Failed to load video config:', error);
		}
	};

	const loadModels = async () => {
		try {
			models = (await getVideoModels(localStorage.token)) || [];
		} catch (error) {
			console.error('Failed to load video models:', error);
			models = [
				{ id: 'sora-2', name: 'Sora 2' },
				{ id: 'sora-2-pro', name: 'Sora 2 Pro' }
			];
		}
	};

	const loadVideos = async () => {
		try {
			const result = await listVideos(localStorage.token);
			if (result?.data) {
				generatedVideos = result.data;
			}
		} catch (error) {
			console.error('Failed to load videos:', error);
		}
	};

	const generateVideo = async () => {
		if (!prompt.trim()) {
			toast.error($i18n.t('Please enter a prompt'));
			return;
		}

		generating = true;
		currentJob = null;

		try {
			const result = await createVideo(localStorage.token, {
				prompt: prompt.trim(),
				model,
				seconds: duration,
				size,
				quality
			});

			if (result?.id) {
				currentJob = result;
				toast.success($i18n.t('Video generation started!'));

				// Start polling for status
				startPolling(result.id);
			} else {
				toast.error($i18n.t('Failed to start video generation'));
				generating = false;
			}
		} catch (error) {
			toast.error(`${error}`);
			generating = false;
		}
	};

	const startPolling = (videoId: string) => {
		if (pollInterval) {
			clearInterval(pollInterval);
		}

		pollInterval = setInterval(async () => {
			try {
				const status = await getVideoStatus(localStorage.token, videoId);

				if (status) {
					currentJob = status;

					if (status.status === 'completed') {
						clearInterval(pollInterval);
						pollInterval = null;
						generating = false;
						toast.success($i18n.t('Video generated successfully!'));
						loadVideos();
					} else if (status.status === 'failed') {
						clearInterval(pollInterval);
						pollInterval = null;
						generating = false;
						toast.error($i18n.t('Video generation failed'));
					}
				}
			} catch (error) {
				console.error('Polling error:', error);
			}
		}, 5000); // Poll every 5 seconds
	};

	const handleDeleteVideo = async (videoId: string) => {
		try {
			await deleteVideo(localStorage.token, videoId);
			toast.success($i18n.t('Video deleted'));
			loadVideos();
		} catch (error) {
			toast.error(`${error}`);
		}
	};

	const downloadVideo = (videoId: string) => {
		const url = getVideoContentUrl(videoId);
		window.open(`${url}?token=${localStorage.token}`, '_blank');
	};

	onMount(() => {
		if (show) {
			loadConfig();
			loadModels();
			loadVideos();
		}
	});

	$: if (show) {
		loadConfig();
		loadModels();
		loadVideos();
	}

	// Cleanup on destroy
	import { onDestroy } from 'svelte';
	onDestroy(() => {
		if (pollInterval) {
			clearInterval(pollInterval);
		}
	});
</script>

<Modal size="lg" bind:show>
	<div>
		<div class="flex justify-between items-center px-5 pt-4 pb-2">
			<div class="flex items-center gap-2">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 24 24"
					fill="currentColor"
					class="w-5 h-5"
				>
					<path
						fill-rule="evenodd"
						d="M4.5 5.653c0-1.426 1.529-2.33 2.779-1.643l11.54 6.348c1.295.712 1.295 2.573 0 3.285L7.28 19.991c-1.25.687-2.779-.217-2.779-1.643V5.653z"
						clip-rule="evenodd"
					/>
				</svg>
				<h3 class="text-lg font-semibold">{$i18n.t('Video Generation (Sora)')}</h3>
			</div>
			<button
				class="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
				on:click={() => (show = false)}
			>
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M6 18L18 6M6 6l12 12"
					/>
				</svg>
			</button>
		</div>

		<div class="px-5 pb-5 space-y-4">
			<!-- Prompt Input -->
			<div>
				<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
					{$i18n.t('Prompt')}
				</label>
				<textarea
					bind:value={prompt}
					placeholder={$i18n.t('Describe the video you want to generate...')}
					class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
					rows="3"
					disabled={generating}
				/>
			</div>

			<!-- Settings Grid -->
			<div class="grid grid-cols-2 gap-4">
				<!-- Model -->
				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
						{$i18n.t('Model')}
					</label>
					<select
						bind:value={model}
						class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
						disabled={generating}
					>
						{#each models as m}
							<option value={m.id}>{m.name}</option>
						{/each}
						{#if models.length === 0}
							<option value="sora-2">Sora 2</option>
							<option value="sora-2-pro">Sora 2 Pro</option>
						{/if}
					</select>
				</div>

				<!-- Duration -->
				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
						{$i18n.t('Duration')}
					</label>
					<select
						bind:value={duration}
						class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
						disabled={generating}
					>
						<option value="4">4 {$i18n.t('seconds')}</option>
						<option value="8">8 {$i18n.t('seconds')}</option>
						<option value="12">12 {$i18n.t('seconds')}</option>
					</select>
				</div>

				<!-- Size -->
				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
						{$i18n.t('Size')}
					</label>
					<select
						bind:value={size}
						class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
						disabled={generating}
					>
						<option value="1920x1080">1920×1080 (HD)</option>
						<option value="1080x1920">1080×1920 (Vertical)</option>
						<option value="1280x720">1280×720 (720p)</option>
						<option value="1024x1792">1024×1792 (Portrait)</option>
						<option value="1792x1024">1792×1024 (Landscape)</option>
					</select>
				</div>

				<!-- Quality -->
				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
						{$i18n.t('Quality')}
					</label>
					<select
						bind:value={quality}
						class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
						disabled={generating}
					>
						<option value="standard">{$i18n.t('Standard')}</option>
						<option value="hd">{$i18n.t('HD')}</option>
					</select>
				</div>
			</div>

			<!-- Generate Button -->
			<button
				on:click={generateVideo}
				disabled={generating || !prompt.trim()}
				class="w-full py-2.5 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
			>
				{#if generating}
					<Spinner className="w-4 h-4" />
					{$i18n.t('Generating...')}
				{:else}
					<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
						/>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
						/>
					</svg>
					{$i18n.t('Generate Video')}
				{/if}
			</button>

			<!-- Current Job Status -->
			{#if currentJob}
				<div class="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
					<div class="flex items-center justify-between mb-2">
						<span class="text-sm font-medium text-gray-700 dark:text-gray-300">
							{$i18n.t('Current Job')}
						</span>
						<span
							class="px-2 py-1 text-xs rounded-full {currentJob.status === 'completed'
								? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
								: currentJob.status === 'failed'
									? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
									: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'}"
						>
							{currentJob.status}
						</span>
					</div>
					{#if currentJob.progress !== undefined}
						<div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 mb-2">
							<div
								class="bg-blue-600 h-2 rounded-full transition-all"
								style="width: {currentJob.progress}%"
							/>
						</div>
					{/if}
					{#if currentJob.status === 'completed'}
						<button
							on:click={() => downloadVideo(currentJob.id)}
							class="text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 flex items-center gap-1"
						>
							<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
								/>
							</svg>
							{$i18n.t('Download Video')}
						</button>
					{/if}
				</div>
			{/if}

			<!-- Recent Videos -->
			{#if generatedVideos.length > 0}
				<div>
					<h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
						{$i18n.t('Recent Videos')}
					</h4>
					<div class="space-y-2 max-h-48 overflow-y-auto">
						{#each generatedVideos.slice(0, 5) as video}
							<div
								class="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800 rounded-lg"
							>
								<div class="flex-1 truncate">
									<span class="text-sm text-gray-600 dark:text-gray-400">{video.id}</span>
									<span
										class="ml-2 px-1.5 py-0.5 text-xs rounded {video.status === 'completed'
											? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
											: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'}"
									>
										{video.status}
									</span>
								</div>
								<div class="flex gap-2">
									{#if video.status === 'completed'}
										<Tooltip content={$i18n.t('Download')}>
											<button
												on:click={() => downloadVideo(video.id)}
												class="p-1 text-blue-600 hover:text-blue-800 dark:text-blue-400"
											>
												<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
													<path
														stroke-linecap="round"
														stroke-linejoin="round"
														stroke-width="2"
														d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
													/>
												</svg>
											</button>
										</Tooltip>
									{/if}
									<Tooltip content={$i18n.t('Delete')}>
										<button
											on:click={() => handleDeleteVideo(video.id)}
											class="p-1 text-red-600 hover:text-red-800 dark:text-red-400"
										>
											<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													stroke-width="2"
													d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
												/>
											</svg>
										</button>
									</Tooltip>
								</div>
							</div>
						{/each}
					</div>
				</div>
			{/if}

			<!-- Info Note -->
			<div class="text-xs text-gray-500 dark:text-gray-400 mt-4">
				<p>
					{$i18n.t('Video generation typically takes 1-5 minutes depending on duration and quality.')}
				</p>
			</div>
		</div>
	</div>
</Modal>

