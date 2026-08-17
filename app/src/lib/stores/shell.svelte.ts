export const DEMO_QUESTIONS = [
	'a good date-handling library?',
	'what breaks if debug disappears?',
	'what are the major sub-ecosystems here?',
	"recommend a Node REST stack, then check each option's dependency count and license."
] as const;

export const RUNGS = [
	{ id: 'vanilla', number: 1, label: 'Vanilla' },
	{ id: 'graph', number: 2, label: 'Graph' },
	{ id: 'agentic', number: 3, label: 'Agentic' }
] as const;

export type RungId = (typeof RUNGS)[number]['id'];

// Sub-steps within the vanilla rung (see specs.md's wireframe: "① VANILLA / embed / chunk / ground").
export const VANILLA_MODULES = [
	{ id: 'embed', label: 'embed' },
	{ id: 'chunk', label: 'chunk' },
	{ id: 'ground', label: 'ground' }
] as const;

export type VanillaModuleId = (typeof VANILLA_MODULES)[number]['id'];

export const queryState = $state({ text: '' });

export const rungState = $state<{ active: RungId | null }>({ active: null });

export const vanillaModuleState = $state<{ active: VanillaModuleId }>({ active: 'embed' });

export type GuidedPanelContent = {
	whatThisShows: string;
	tryThis: string;
	aha: string;
};

const defaultGuidedPanel: GuidedPanelContent = {
	whatThisShows: 'Pick a rung on the left to begin.',
	tryThis: 'Ask a question in the bar above.',
	aha: ''
};

export const guidedPanel = $state<GuidedPanelContent>({ ...defaultGuidedPanel });

export function setGuidedPanel(content: Partial<GuidedPanelContent>) {
	Object.assign(guidedPanel, content);
}

export function resetGuidedPanel() {
	Object.assign(guidedPanel, defaultGuidedPanel);
}
