import type {
	ExpressiveCodeConfig,
	LicenseConfig,
	NavBarConfig,
	ProfileConfig,
	SiteConfig,
} from "./types/config";
import { LinkPreset } from "./types/config";

// ========== 网站基础配置 ==========
export const siteConfig: SiteConfig = {
	title: "智澜文档",           // 网站标题
	subtitle: "项目开发文档与更新日志",  // 副标题
	lang: "zh_CN",              // 语言代码：zh_CN 中文, en 英文, ja 日文
	themeColor: {
		hue: 250,               // 主题色相值 0-360：红色 0, 青色 200, 蓝紫 250, 粉色 345
		fixed: false,           // 是否隐藏访客的主题色选择器
	},
	banner: {
		enable: false,          // 是否启用横幅图片
		src: "assets/images/demo-banner.png",  // 图片路径，相对于 /src 目录；以 '/' 开头则相对于 /public 目录
		position: "center",     // 图片位置：top 顶部, center 居中, bottom 底部
		credit: {
			enable: false,      // 是否显示横幅图片的版权信息
			text: "",           // 版权文字
			url: "",            // 原作品或作者主页链接（可选）
		},
	},
	toc: {
		enable: true,           // 是否在文章右侧显示目录
		depth: 2,               // 目录显示的最大标题层级，1-3
	},
	favicon: [
		// 留空则使用默认图标
		// {
		//   src: '/favicon/icon.png',    // 图标路径，相对于 /public 目录
		//   theme: 'light',              // （可选）'light' 或 'dark'，仅在需要区分明暗模式图标时设置
		//   sizes: '32x32',              // （可选）图标尺寸，仅在有多个尺寸时设置
		// }
	],
};

// ========== 导航栏配置 ==========
export const navBarConfig: NavBarConfig = {
	links: [
		LinkPreset.Home,        // 首页
		LinkPreset.Archive,     // 归档
		LinkPreset.About,       // 关于
		{
			name: "简历",
			url: "/resume/",
			external: false,
		},
		{
			name: "Gitee",
			url: "https://gitee.com/zgm2003",  // 内部链接不需要包含 base 路径，会自动添加
			external: true,     // 显示外部链接图标，并在新标签页打开
		},
	],
};

// ========== 个人资料配置 ==========
export const profileConfig: ProfileConfig = {
	avatar: "assets/images/demo-avatar.png",  // 头像路径，相对于 /src 目录；以 '/' 开头则相对于 /public 目录
	name: "智澜管理系统",
	bio: "全栈开发文档中心",
	links: [
		{
			name: "Gitee",
			icon: "fa6-brands:git-alt",  // 图标代码，访问 https://icones.js.org/ 查找
			// 如果图标集未安装，需要运行：pnpm add @iconify-json/<图标集名称>
			url: "https://gitee.com/zgm2003",
		},
		{
			name: "微信",
			icon: "fa6-brands:weixin",
			url: "/wechat-qr.png",
		},
		{
			name: "QQ",
			icon: "fa6-brands:qq",
			url: "https://qm.qq.com/q/90mzzJHcBy",
		},
	],
};

// ========== 文章版权配置 ==========
export const licenseConfig: LicenseConfig = {
	enable: true,               // 是否显示版权信息
	name: "CC BY-NC-SA 4.0",    // 许可证名称
	url: "https://creativecommons.org/licenses/by-nc-sa/4.0/deed.zh-hans",  // 许可证链接（中文版）
};

// ========== 代码块配置 ==========
export const expressiveCodeConfig: ExpressiveCodeConfig = {
	// 注意：部分样式（如背景色）会被覆盖，详见 astro.config.mjs
	// 请选择深色主题，因为本博客目前仅支持深色代码块背景
	theme: "github-dark",
};
