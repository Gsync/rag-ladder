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

export const queryState = $state({ text: '' });

export const rungState = $state<{ active: RungId | null }>({ active: null });

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
