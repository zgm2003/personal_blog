import { type CollectionEntry, getCollection } from "astro:content";
import I18nKey from "@i18n/i18nKey";
import { i18n } from "@i18n/translation";
import { getCategoryUrl } from "@utils/url-utils.ts";

// ==================== Posts 相关 ====================

// Retrieve posts and sort them by publication date
async function getRawSortedPosts() {
	const allBlogPosts = await getCollection("posts", ({ data }) => {
		return import.meta.env.PROD ? data.draft !== true : true;
	});

	const sorted = allBlogPosts.sort((a, b) => {
		// 检查是否有置顶标签
		const aIsSticky = a.data.tags?.includes('置顶') ? 1 : 0;
		const bIsSticky = b.data.tags?.includes('置顶') ? 1 : 0;
		
		// 如果有置顶标签，优先级更高
		if (aIsSticky && !bIsSticky) return -1;
		if (!aIsSticky && bIsSticky) return 1;
		
		// 如果都有或都没有置顶标签，则按日期排序
		const dateA = new Date(a.data.published);
		const dateB = new Date(b.data.published);
		return dateA > dateB ? -1 : 1;
	});
	return sorted;
}

export async function getSortedPosts() {
	const sorted = await getRawSortedPosts();

	for (let i = 1; i < sorted.length; i++) {
		sorted[i].data.nextSlug = sorted[i - 1].slug;
		sorted[i].data.nextTitle = sorted[i - 1].data.title;
	}
	for (let i = 0; i < sorted.length - 1; i++) {
		sorted[i].data.prevSlug = sorted[i + 1].slug;
		sorted[i].data.prevTitle = sorted[i + 1].data.title;
	}

	return sorted;
}
export type PostForList = {
	slug: string;
	data: CollectionEntry<"posts">["data"];
};
export async function getSortedPostsList(): Promise<PostForList[]> {
	const sortedFullPosts = await getRawSortedPosts();

	// delete post.body
	const sortedPostsList = sortedFullPosts.map((post) => ({
		slug: post.slug,
		data: post.data,
	}));

	return sortedPostsList;
}
export type Tag = {
	name: string;
	count: number;
};

export async function getTagList(): Promise<Tag[]> {
	const allBlogPosts = await getCollection<"posts">("posts", ({ data }) => {
		return import.meta.env.PROD ? data.draft !== true : true;
	});

	const countMap: { [key: string]: number } = {};
	allBlogPosts.forEach((post: { data: { tags: string[] } }) => {
		post.data.tags.forEach((tag: string) => {
			if (!countMap[tag]) countMap[tag] = 0;
			countMap[tag]++;
		});
	});

	// sort tags
	const keys: string[] = Object.keys(countMap).sort((a, b) => {
		return a.toLowerCase().localeCompare(b.toLowerCase());
	});

	return keys.map((key) => ({ name: key, count: countMap[key] }));
}

export type Category = {
	name: string;
	count: number;
	url: string;
};

export async function getCategoryList(): Promise<Category[]> {
	const allBlogPosts = await getCollection<"posts">("posts", ({ data }) => {
		return import.meta.env.PROD ? data.draft !== true : true;
	});
	const count: { [key: string]: number } = {};
	allBlogPosts.forEach((post: { data: { category: string | null } }) => {
		if (!post.data.category) {
			const ucKey = i18n(I18nKey.uncategorized);
			count[ucKey] = count[ucKey] ? count[ucKey] + 1 : 1;
			return;
		}

		const categoryName =
			typeof post.data.category === "string"
				? post.data.category.trim()
				: String(post.data.category).trim();

		count[categoryName] = count[categoryName] ? count[categoryName] + 1 : 1;
	});

	const lst = Object.keys(count).sort((a, b) => {
		return a.toLowerCase().localeCompare(b.toLowerCase());
	});

	const ret: Category[] = [];
	for (const c of lst) {
		ret.push({
			name: c,
			count: count[c],
			url: getCategoryUrl(c),
		});
	}
	return ret;
}

// ==================== Projects 相关 ====================

export type ProjectDoc = CollectionEntry<"projects">;
export type ProjectDocForList = {
	slug: string;
	data: CollectionEntry<"projects">["data"];
};

// 获取所有项目名称列表
export async function getProjectList(): Promise<string[]> {
	const allDocs = await getCollection("projects", ({ data }) => {
		return import.meta.env.PROD ? data.draft !== true : true;
	});
	const projects = [...new Set(allDocs.map((doc) => doc.data.project))];
	return projects.sort();
}

// 获取指定项目的文档列表（按 order 排序）
export async function getProjectDocs(projectName: string): Promise<ProjectDoc[]> {
	const allDocs = await getCollection("projects", ({ data }) => {
		return import.meta.env.PROD ? data.draft !== true : true;
	});
	
	const filtered = allDocs.filter((doc) => doc.data.project === projectName);
	
	// 按 order 排序，order 相同则按发布时间排序
	const sorted = filtered.sort((a, b) => {
		const orderA = a.data.order ?? 100;
		const orderB = b.data.order ?? 100;
		if (orderA !== orderB) return orderA - orderB;
		return new Date(b.data.published).getTime() - new Date(a.data.published).getTime();
	});

	// 设置上下篇导航
	for (let i = 1; i < sorted.length; i++) {
		sorted[i].data.nextSlug = sorted[i - 1].slug;
		sorted[i].data.nextTitle = sorted[i - 1].data.title;
	}
	for (let i = 0; i < sorted.length - 1; i++) {
		sorted[i].data.prevSlug = sorted[i + 1].slug;
		sorted[i].data.prevTitle = sorted[i + 1].data.title;
	}

	return sorted;
}

// 获取指定项目的文档列表（轻量版，用于列表展示）
export async function getProjectDocsList(projectName: string): Promise<ProjectDocForList[]> {
	const docs = await getProjectDocs(projectName);
	return docs.map((doc) => ({
		slug: doc.slug,
		data: doc.data,
	}));
}

// 获取所有项目及其文档数量
export type ProjectInfo = {
	name: string;
	count: number;
};

export async function getProjectInfoList(): Promise<ProjectInfo[]> {
	const allDocs = await getCollection("projects", ({ data }) => {
		return import.meta.env.PROD ? data.draft !== true : true;
	});
	
	const countMap: { [key: string]: number } = {};
	allDocs.forEach((doc) => {
		const project = doc.data.project;
		countMap[project] = (countMap[project] || 0) + 1;
	});

	return Object.entries(countMap).map(([name, count]) => ({
		name,
		count,
	}));
}
