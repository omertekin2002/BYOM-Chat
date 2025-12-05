<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { createEventDispatcher, onMount, getContext } from 'svelte';
	import { config as backendConfig, user } from '$lib/stores';

	import { getBackendConfig } from '$lib/apis';
	import { getVideoConfig, updateVideoConfig, getVideoModels } from '$lib/apis/videos';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import SensitiveInput from '$lib/components/common/SensitiveInput.svelte';
	import Switch from '$lib/components/common/Switch.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';

	const dispatch = createEventDispatcher();
	const i18n = getContext('i18n');

	let loading = false;
	let models: { id: string; name: string }[] | null = null;
	let config: {
		ENABLE_VIDEO_GENERATION: boolean;
		VIDEO_GENERATION_ENGINE: string;
		VIDEO_GENERATION_MODEL: string;
		VIDEO_DURATION: string;
		VIDEO_SIZE: string;
		VIDEO_QUALITY: string;
		VIDEOS_OPENAI_API_BASE_URL: string;
		VIDEOS_OPENAI_API_KEY: string;
	} | null = null;

	const getModels = async () => {
		models = await getVideoModels(localStorage.token).catch((error) => {
			toast.error(`${error}`);
			return null;
		});
	};

	const updateConfigHandler = async () => {
		if (config?.VIDEO_GENERATION_ENGINE === 'openai' && config?.VIDEOS_OPENAI_API_KEY === '') {
			toast.error($i18n.t('OpenAI API Key is required for video generation.'));
			if (config) config.ENABLE_VIDEO_GENERATION = false;
			return null;
		}

		const res = await updateVideoConfig(localStorage.token, config).catch((error) => {
			toast.error(`${error}`);
			return null;
		});

		if (res) {
			if (res.ENABLE_VIDEO_GENERATION) {
				backendConfig.set(await getBackendConfig());
				getModels();
			}
			return res;
		}

		return null;
	};

	const saveHandler = async () => {
		loading = true;

		const res = await updateConfigHandler();
		if (res) {
			toast.success($i18n.t('Video settings saved successfully'));
			dispatch('save');
		}

		loading = false;
	};

	onMount(async () => {
		if ($user?.role === 'admin') {
			const res = await getVideoConfig(localStorage.token).catch((error) => {
				toast.error(`${error}`);
				return null;
			});

			if (res) {
				config = res;
			}

			if (config?.ENABLE_VIDEO_GENERATION) {
				getModels();
			}
		}
	});
</script>

<form
	class="flex flex-col h-full justify-between space-y-3 text-sm"
	on:submit|preventDefault={saveHandler}
>
	<div class="space-y-3 overflow-y-scroll scrollbar-hidden pr-2">
		{#if config}
			<div>
				<div class="mb-3">
					<div class="mt-0.5 mb-2.5 text-base font-medium">{$i18n.t('General')}</div>
					<hr class="border-gray-100/30 dark:border-gray-850/30 my-2" />

					<div class="mb-2.5">
						<div class="flex w-full justify-between items-center">
							<div class="text-xs pr-2">
								<div class="flex items-center gap-2">
									<span>🎬</span>
									{$i18n.t('Video Generation (Sora)')}
								</div>
							</div>
							<Switch bind:state={config.ENABLE_VIDEO_GENERATION} />
						</div>
					</div>
				</div>

				{#if config.ENABLE_VIDEO_GENERATION}
					<div class="mb-3">
						<div class="mt-0.5 mb-2.5 text-base font-medium">{$i18n.t('Create Video')}</div>
						<hr class="border-gray-100/30 dark:border-gray-850/30 my-2" />

						<div class="mb-2.5">
							<div class="flex w-full justify-between items-center">
								<div class="text-xs pr-2 shrink-0">
									{$i18n.t('Model')}
								</div>

								<Tooltip content={$i18n.t('Select video generation model')} placement="top-start">
									<select
										class="dark:bg-gray-900 w-fit pr-8 cursor-pointer rounded-sm px-2 text-xs bg-transparent outline-hidden text-right"
										bind:value={config.VIDEO_GENERATION_MODEL}
									>
										{#each models ?? [] as model}
											<option value={model.id}>{model.name}</option>
										{/each}
										<option value="sora-2">Sora 2</option>
										<option value="sora-2-pro">Sora 2 Pro</option>
									</select>
								</Tooltip>
							</div>
						</div>

						<div class="mb-2.5">
							<div class="flex w-full justify-between items-center">
								<div class="text-xs pr-2 shrink-0">
									{$i18n.t('Duration (seconds)')}
								</div>

								<Tooltip content={$i18n.t('Video duration in seconds')} placement="top-start">
									<select
										class="dark:bg-gray-900 w-fit pr-8 cursor-pointer rounded-sm px-2 text-xs bg-transparent outline-hidden text-right"
										bind:value={config.VIDEO_DURATION}
									>
										<option value="4">4 seconds</option>
										<option value="8">8 seconds</option>
										<option value="12">12 seconds</option>
									</select>
								</Tooltip>
							</div>
						</div>

						<div class="mb-2.5">
							<div class="flex w-full justify-between items-center">
								<div class="text-xs pr-2 shrink-0">
									{$i18n.t('Video Size')}
								</div>

								<Tooltip content={$i18n.t('Video resolution')} placement="top-start">
									<select
										class="dark:bg-gray-900 w-fit pr-8 cursor-pointer rounded-sm px-2 text-xs bg-transparent outline-hidden text-right"
										bind:value={config.VIDEO_SIZE}
									>
										<option value="1920x1080">1920x1080 (HD)</option>
										<option value="1080x1920">1080x1920 (Vertical HD)</option>
										<option value="1280x720">1280x720 (720p)</option>
										<option value="1024x1792">1024x1792 (Portrait)</option>
										<option value="1792x1024">1792x1024 (Landscape)</option>
									</select>
								</Tooltip>
							</div>
						</div>

						<div class="mb-2.5">
							<div class="flex w-full justify-between items-center">
								<div class="text-xs pr-2 shrink-0">
									{$i18n.t('Quality')}
								</div>

								<Tooltip content={$i18n.t('Video quality setting')} placement="top-start">
									<select
										class="dark:bg-gray-900 w-fit pr-8 cursor-pointer rounded-sm px-2 text-xs bg-transparent outline-hidden text-right"
										bind:value={config.VIDEO_QUALITY}
									>
										<option value="standard">Standard</option>
										<option value="hd">HD</option>
									</select>
								</Tooltip>
							</div>
						</div>
					</div>

					<div class="mb-3">
						<div class="mt-0.5 mb-2.5 text-base font-medium">{$i18n.t('OpenAI API Settings')}</div>
						<hr class="border-gray-100/30 dark:border-gray-850/30 my-2" />

						<div class="mb-2.5">
							<div class="flex w-full justify-between items-center">
								<div class="text-xs pr-2 shrink-0">
									{$i18n.t('API Base URL')}
								</div>

								<div class="flex w-full">
									<div class="flex-1">
										<input
											class="w-full text-sm bg-transparent outline-hidden text-right"
											placeholder="https://api.openai.com/v1"
											bind:value={config.VIDEOS_OPENAI_API_BASE_URL}
										/>
									</div>
								</div>
							</div>
						</div>

						<div class="mb-2.5">
							<div class="flex w-full justify-between items-center">
								<div class="text-xs pr-2 shrink-0">
									{$i18n.t('API Key')}
								</div>

								<div class="flex w-full">
									<div class="flex-1">
										<SensitiveInput
											inputClassName="text-right w-full"
											placeholder={$i18n.t('Enter your OpenAI API Key')}
											bind:value={config.VIDEOS_OPENAI_API_KEY}
											required={true}
										/>
									</div>
								</div>
							</div>
						</div>

						<div class="mt-2 text-xs text-gray-400 dark:text-gray-500">
							{$i18n.t('Video generation uses OpenAI\'s Sora API. Make sure your API key has access to video generation.')}
						</div>
					</div>
				{/if}
			</div>
		{:else}
			<div class="flex justify-center py-8">
				<Spinner />
			</div>
		{/if}
	</div>

	<div class="flex justify-end pt-3 text-sm font-medium">
		<button
			class="px-3.5 py-1.5 text-sm font-medium bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-full flex flex-row space-x-1 items-center {loading
				? 'cursor-not-allowed'
				: ''}"
			type="submit"
			disabled={loading}
		>
			{$i18n.t('Save')}

			{#if loading}
				<div class="ml-2 self-center">
					<Spinner />
				</div>
			{/if}
		</button>
	</div>
</form>

