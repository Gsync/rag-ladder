export type Community = {
	id: string;
	label: string;
	members: string[];
	summary?: string | null;
};

export function indexCommunities(communities: Community[]): Map<string, string> {
	const index = new Map<string, string>();
	for (const community of communities) {
		for (const member of community.members) {
			index.set(member, community.id);
		}
	}
	return index;
}

export function topCommunitiesBySize(communities: Community[], n: number): string[] {
	return [...communities]
		.sort((a, b) => b.members.length - a.members.length)
		.slice(0, n)
		.map((c) => c.id);
}
