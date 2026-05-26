---
title: "React 基础学习手册：从零理解组件到能写项目"
published: 2026-05-26T08:00:00Z
draft: false
tags: [React, 入门, 基础, 前端, TypeScript, Vite, 学习路线]
description: "一篇写给 React 新手的超详细学习文章：从环境、组件、JSX、Props、State、事件、列表、表单、Effect、Hooks、路由、请求、状态管理、性能、测试，到能写一个真实小项目。基于 React 19 与当前官方文档重新整理。"
category: React
---

> **本文价值**：这不是“十分钟精通 React”，也不是把旧教程里的 `class component`、`componentDidMount`、`create-react-app` 原样搬过来。它是一份面向小白的 React 学习手册：先把环境跑通，再理解组件、JSX、Props、State、事件、列表、表单、Effect 和 Hooks，最后知道什么时候需要路由、请求库、状态管理、TypeScript、性能优化和测试。学习 React 不需要玄学，也不需要一上来背框架黑话。你只要先建立正确的心智模型，再用小项目反复练。

# 先说结论：React 新手不要一上来就学 Next.js、Redux 和各种“最佳实践”

很多人学 React 的路线是错的：第一天装一堆脚手架，第二天抄一个后台模板，第三天开始问 Redux 和 Zustand 哪个好，第四天看到 React Server Components、Server Actions、React Compiler、Signals、微前端，最后连 `props` 和 `state` 的区别都说不清。

这不是 React 难，是学习顺序乱。

React 的学习顺序应该很朴素：

1. 先知道 React 是用来描述 UI 的 JavaScript 库，不是“万能前端框架”。
2. 先跑通一个本地项目，知道 `src/main.tsx`、`App.tsx`、`createRoot` 在干什么。
3. 再学组件：组件本质上是返回 UI 的函数。
4. 再学 JSX：它不是 HTML 字符串，而是 JavaScript 里的 UI 描述语法。
5. 再学 Props：父组件把数据传给子组件。
6. 再学 State：组件自己记住会变化的数据。
7. 再学事件：用户点击、输入、提交表单时怎么更新状态。
8. 再学条件渲染、列表渲染和 `key`。
9. 再学表单：什么时候用受控组件，什么时候直接读 `FormData`。
10. 再学 Effect：它是连接外部系统的逃生门，不是“数据变化就同步一遍”的万能工具。
11. 再学 Hooks 规则：为什么 Hook 不能写在 `if`、循环、普通函数里。
12. 再学组件拆分、状态提升、Context、Reducer、自定义 Hook。
13. 最后才学路由、请求库、全局状态、性能优化、测试、框架和工程化。

这条路看起来慢，其实最快。因为 React 真正常见的 bug，不是语法 bug，而是心智模型 bug：把状态复制来复制去、乱用 Effect、直接修改对象数组、列表 key 用错、组件拆分不清、把服务端数据塞进全局状态、把性能优化当作默认写法。

本文基于 2026-05-26 的资料重新整理。写作时我核对了 React 官方文档、React 19.2 发布说明、Vite 官方文档、React Router v7 文档、TanStack Query v5 文档和 Zustand 官方仓库。写作时 npm 上的关键版本是：

| 包 | 写作时 npm latest |
| --- | --- |
| `react` | `19.2.6` |
| `react-dom` | `19.2.6` |
| `vite` | `8.0.14` |
| `@vitejs/plugin-react` | `6.0.2` |
| `react-router` | `7.15.1` |
| `@tanstack/react-query` | `5.100.14` |
| `zustand` | `5.0.13` |

版本会继续变，所以你以后读这篇文章时，可以自己跑：

```bash
npm view react version
npm view react-dom version
npm view vite version
npm view react-router version
```

你不需要记住这些小版本号。你需要记住的是：**现在学 React，不要再从 Create React App 开始，不要把 class 组件当主线，不要把 Redux 当入门必修，不要把 Effect 当生命周期替代品。**

# 0. React 到底是什么

React 是一个用于构建用户界面的 JavaScript 库。更准确一点说，React 让你用“组件”描述页面应该长什么样，然后由 React 根据状态变化去更新真实 DOM。

传统写法里，你可能会这样操作页面：

```js
const button = document.querySelector("button");
const countText = document.querySelector("#count");
let count = 0;

button.addEventListener("click", () => {
  count += 1;
  countText.textContent = String(count);
});
```

这种写法不是错，但随着页面变复杂，你会不断写“找 DOM、改 DOM、同步 DOM”的代码。按钮禁用、列表新增、表单校验、弹窗开关、接口 loading、错误提示、分页切换，全部靠你自己把状态和 DOM 对齐。

React 的思路不一样。你先描述：当 `count` 是多少时，页面应该显示什么。

```tsx
import { useState } from "react";

export default function Counter() {
  const [count, setCount] = useState(0);

  return (
    <button onClick={() => setCount(count + 1)}>
      点击了 {count} 次
    </button>
  );
}
```

你没有手动找 DOM，也没有手动改 `textContent`。你只是更新状态，React 负责重新计算 UI，再把变化同步到页面。

所以 React 的核心不是“语法很高级”，而是一个简单心智模型：

> UI = f(state)

也就是：页面是状态的结果。状态变了，页面自然变。

React 适合做什么？

| 场景 | React 适合的原因 |
| --- | --- |
| 后台管理系统 | 表单、表格、筛选、弹窗、权限状态很多，组件化很有价值 |
| SaaS 控制台 | 页面状态复杂，组件复用多，交互多 |
| 电商前台 | 商品卡片、购物车、筛选、详情页、下单流程都适合组件拆分 |
| AI 应用页面 | 聊天、流式输出、模型配置、文件上传、历史记录都需要状态驱动 UI |
| 小程序/移动端衍生 | React Native、Expo 可以把 React 思路带到原生应用 |

React 不适合什么？

- 不适合拿来炫语法。
- 不适合一个静态介绍页也强行全量 SPA 化。
- 不适合刚入门就把所有状态放进全局 store。
- 不适合把所有逻辑塞进一个 1000 行 `App.tsx`。
- 不适合不懂浏览器、JavaScript、CSS 就直接跳框架。

React 只是工具。工具的价值是让复杂 UI 更可维护，而不是让简单事情变复杂。

# 1. 环境：先把第一个 React 项目跑起来

新手第一步不要背概念，先让项目能在本机跑起来。

现在官方文档对新项目的建议更偏向“使用框架”，比如 Next.js App Router、React Router v7 Framework Mode、Expo 等。原因是生产级应用通常需要路由、数据加载、构建、SSR/SSG、部署策略，这些不是 React 核心库单独负责的。

但如果你是小白，目标是先学 React 基础，我建议先用 Vite 创建一个 React + TypeScript 项目。理由很简单：

- 启动快。
- 配置少。
- 目录清楚。
- 方便看到 React 最基本的入口。
- 不会一开始就被服务端组件、文件路由、缓存策略绕晕。

注意：React 官方文档已经明确不推荐继续用 Create React App。旧教程里看到 `npx create-react-app`，可以直接跳过。

## 1.1 安装 Node.js

React 本身可以通过简单 HTML 在线体验，但真实开发基本离不开 Node.js，因为你需要 npm 包、构建工具、开发服务器和 TypeScript。

先检查：

```bash
node -v
npm -v
```

Vite 当前文档要求 Node.js `20.19+` 或 `22.12+`。如果你的 Node 太老，先升级。不要在一个旧 Node 上硬修一堆奇怪报错。

## 1.2 创建项目

用 npm：

```bash
npm create vite@latest react-beginner -- --template react-ts
cd react-beginner
npm install
npm run dev
```

如果你习惯 pnpm：

```bash
pnpm create vite react-beginner --template react-ts
cd react-beginner
pnpm install
pnpm dev
```

浏览器打开终端提示的地址，一般是：

```text
http://localhost:5173/
```

能看到页面，第一步就成功了。

## 1.3 先看懂项目结构

Vite 创建的 React 项目通常长这样：

```text
react-beginner/
├─ index.html
├─ package.json
├─ src/
│  ├─ main.tsx
│  ├─ App.tsx
│  ├─ App.css
│  └─ index.css
└─ vite.config.ts
```

先别急着改，先知道每个文件大概干什么：

| 文件 | 作用 |
| --- | --- |
| `index.html` | 浏览器最先加载的 HTML，里面通常有 `<div id="root"></div>` |
| `src/main.tsx` | React 应用入口，把组件挂到真实 DOM 上 |
| `src/App.tsx` | 默认的根组件，你写页面通常从这里开始 |
| `package.json` | 项目信息、依赖、脚本命令 |
| `vite.config.ts` | Vite 配置，初学阶段基本不用动 |

`src/main.tsx` 里通常会看到：

```tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.tsx";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
```

这段代码做了三件事：

1. 从 HTML 里找到 `id="root"` 的 DOM 节点。
2. 用 `createRoot` 创建 React 根节点。
3. 把 `<App />` 这个组件渲染进去。

`StrictMode` 是开发阶段的辅助工具，会帮你暴露一些不安全写法。比如某些 Effect 在开发环境看起来执行了两次，这不是 React 坏了，而是它故意帮你发现副作用是否安全。新手不要因为看到执行两次就立刻删掉 `StrictMode`，应该先理解自己的 Effect 是否写错了。

# 2. 组件：React 的最小思考单位

React 里最重要的概念是组件。组件就是一个返回 UI 的函数。

```tsx
function Welcome() {
  return <h1>欢迎学习 React</h1>;
}

export default function App() {
  return <Welcome />;
}
```

组件有几个基本规则：

- 组件名必须以大写字母开头，比如 `Welcome`、`UserCard`。
- 小写标签会被当作 HTML 标签，比如 `<div>`、`<button>`。
- 组件可以组合组件。
- 组件的返回值描述 UI。
- 组件函数不要在渲染过程中做副作用，比如直接请求接口、改全局变量、写 localStorage。

你可以把页面拆成组件：

```tsx
function Header() {
  return <header>我的博客</header>;
}

function Sidebar() {
  return <aside>分类 / 标签 / 搜索</aside>;
}

function ArticleList() {
  return <main>文章列表</main>;
}

export default function App() {
  return (
    <>
      <Header />
      <div className="layout">
        <Sidebar />
        <ArticleList />
      </div>
    </>
  );
}
```

这里的 `<>...</>` 是 Fragment，表示返回多个元素但不额外生成 DOM 包裹层。

新手最容易犯的错误，是把组件当作“页面片段复制工具”，而不是“有清晰职责的 UI 单元”。一个好组件应该能回答三个问题：

1. 它负责显示什么？
2. 它需要哪些输入？
3. 它内部有没有自己的状态？

如果一个组件同时负责请求数据、处理权限、管理表单、控制弹窗、渲染表格、写 localStorage、拼 URL，那它迟早会变成灾难。

# 3. JSX：看起来像 HTML，但它是 JavaScript

React 里常见这种写法：

```tsx
const title = "React 入门";

export default function App() {
  return <h1>{title}</h1>;
}
```

这叫 JSX。它看起来像 HTML，但它最终会被构建工具转换成 JavaScript 调用。你可以把 JSX 理解成：用接近 HTML 的语法，在 JavaScript 里描述 UI。

JSX 有几个重要规则。

## 3.1 必须有一个根节点

错误：

```tsx
function App() {
  return (
    <h1>标题</h1>
    <p>正文</p>
  );
}
```

正确：

```tsx
function App() {
  return (
    <>
      <h1>标题</h1>
      <p>正文</p>
    </>
  );
}
```

或者：

```tsx
function App() {
  return (
    <div>
      <h1>标题</h1>
      <p>正文</p>
    </div>
  );
}
```

如果你只是为了包裹多个元素，优先用 Fragment，避免无意义的 DOM。

## 3.2 属性名更接近 JavaScript

HTML 里写：

```html
<div class="card" tabindex="0"></div>
```

JSX 里写：

```tsx
<div className="card" tabIndex={0}></div>
```

常见差异：

| HTML | JSX |
| --- | --- |
| `class` | `className` |
| `for` | `htmlFor` |
| `tabindex` | `tabIndex` |
| `onclick` | `onClick` |

因为 JSX 更接近 JavaScript，所以很多属性用驼峰命名。

## 3.3 花括号里写 JavaScript 表达式

```tsx
const user = {
  name: "小明",
  age: 18,
};

export default function App() {
  return (
    <section>
      <h1>{user.name}</h1>
      <p>明年 {user.age + 1} 岁</p>
    </section>
  );
}
```

注意：花括号里是表达式，不是随便写语句。下面这样不行：

```tsx
<h1>{if (ok) "成功"}</h1>
```

应该写三元表达式：

```tsx
<h1>{ok ? "成功" : "失败"}</h1>
```

或者提前算好：

```tsx
const text = ok ? "成功" : "失败";
return <h1>{text}</h1>;
```

## 3.4 style 接收对象

```tsx
function App() {
  return (
    <h1 style={{ color: "tomato", fontSize: 32 }}>
      Hello React
    </h1>
  );
}
```

外层 `{}` 表示进入 JavaScript，内层 `{}` 是对象字面量。

不过真实项目里不要到处写内联样式。能用 CSS class 就用 CSS class，组件局部状态驱动 class 会更清晰：

```tsx
<button className={isActive ? "tab active" : "tab"}>文章</button>
```

## 3.5 JSX 不是模板字符串

新手有时会以为 JSX 是一段字符串，然后想拼接：

```tsx
const html = "<h1>Hello</h1>";
return <div>{html}</div>;
```

这样页面会显示文本 `<h1>Hello</h1>`，不会当作 HTML 执行。这是安全设计。不要轻易用 `dangerouslySetInnerHTML`，除非你明确知道 HTML 来源可信且已经做过清洗。

# 4. Props：父组件给子组件传数据

Props 是 React 里最基础的数据传递方式。父组件把数据传给子组件，子组件根据这些数据渲染 UI。

```tsx
type ProfileCardProps = {
  name: string;
  role: string;
  online?: boolean;
};

function ProfileCard({ name, role, online = false }: ProfileCardProps) {
  return (
    <article className="profile-card">
      <h2>{name}</h2>
      <p>{role}</p>
      <span>{online ? "在线" : "离线"}</span>
    </article>
  );
}

export default function App() {
  return (
    <div>
      <ProfileCard name="小明" role="前端学习者" online />
      <ProfileCard name="小红" role="UI 设计师" />
    </div>
  );
}
```

这里有几件事要看懂：

- `ProfileCardProps` 定义组件需要什么数据。
- `name` 和 `role` 是必填。
- `online?` 是可选。
- `online = false` 给默认值。
- `<ProfileCard online />` 等价于 `<ProfileCard online={true} />`。

Props 有一个非常重要的原则：**子组件不要修改 props。**

Props 是父组件传进来的输入，子组件应该把它当只读数据。如果子组件想改变某个状态，应该让父组件传一个回调函数下来。

例如：

```tsx
type LikeButtonProps = {
  liked: boolean;
  onToggle: () => void;
};

function LikeButton({ liked, onToggle }: LikeButtonProps) {
  return (
    <button onClick={onToggle}>
      {liked ? "已点赞" : "点赞"}
    </button>
  );
}
```

子组件不直接改 `liked`，它只是在用户点击时调用 `onToggle`。真正的状态在父组件里。

## 4.1 children：把内容塞进组件

有些组件不是靠固定字段渲染，而是包住一段内容。

```tsx
type CardProps = {
  title: string;
  children: React.ReactNode;
};

function Card({ title, children }: CardProps) {
  return (
    <section className="card">
      <h2>{title}</h2>
      <div>{children}</div>
    </section>
  );
}

export default function App() {
  return (
    <Card title="学习提醒">
      <p>今天先学组件和 props，不要急着学 Redux。</p>
    </Card>
  );
}
```

`children` 适合做布局容器、卡片、弹窗、页面骨架。它让组件更像“壳”，内容由使用者决定。

## 4.2 Props 设计要少而清楚

新手很容易写出这种组件：

```tsx
<UserCard
  userId="1"
  userName="小明"
  userAvatar="/a.png"
  userRole="admin"
  userStatus="active"
  showAvatar
  showRole
  showStatus
  isClickable
  isSelected
  onClick={handleClick}
/>
```

不是说这样一定错，但如果 props 越来越多，说明组件职责可能不清。你要停下来问：

- 这个组件是不是承担了太多场景？
- 能不能拆成 `UserAvatar`、`UserMeta`、`UserStatus`？
- 能不能传一个 `user` 对象，而不是拆十几个字段？
- 哪些字段其实是显示逻辑，不应该交给调用方配置？

组件设计不是 props 越多越强，而是边界越清楚越好。

# 5. State：组件自己记住会变化的数据

Props 是外部传入，State 是组件内部记住的数据。

最常用的 Hook 是 `useState`：

```tsx
import { useState } from "react";

export default function Counter() {
  const [count, setCount] = useState(0);

  return (
    <button onClick={() => setCount(count + 1)}>
      count: {count}
    </button>
  );
}
```

`useState(0)` 表示初始值是 `0`。它返回两个东西：

- `count`：当前状态值。
- `setCount`：更新状态的函数。

不要这样改：

```tsx
count = count + 1;
```

你不能直接改状态变量。你必须调用更新函数：

```tsx
setCount(count + 1);
```

React 看到你调用 `setCount`，才知道需要重新渲染组件。

## 5.1 状态更新不是立刻改当前变量

看这个例子：

```tsx
function Counter() {
  const [count, setCount] = useState(0);

  function handleClick() {
    setCount(count + 1);
    console.log(count);
  }

  return <button onClick={handleClick}>{count}</button>;
}
```

点击时，`console.log(count)` 打印的仍然是这次渲染里的旧值。因为 `count` 是当前这次渲染的快照，调用 `setCount` 是告诉 React：下次渲染时用新值。

如果你需要基于上一次状态连续更新，用函数写法：

```tsx
setCount((prev) => prev + 1);
setCount((prev) => prev + 1);
setCount((prev) => prev + 1);
```

这样点击一次会加 3。函数参数 `prev` 永远是可靠的上一次值。

## 5.2 对象状态：不要直接改

错误：

```tsx
const [user, setUser] = useState({ name: "小明", age: 18 });

function grow() {
  user.age += 1;
  setUser(user);
}
```

正确：

```tsx
function grow() {
  setUser((prev) => ({
    ...prev,
    age: prev.age + 1,
  }));
}
```

React 判断状态是否变化时依赖引用。你直接改原对象，引用没变，容易导致页面不更新或者逻辑混乱。正确做法是创建新对象。

## 5.3 数组状态：也不要直接改

错误：

```tsx
const [todos, setTodos] = useState(["学习 JSX"]);

todos.push("学习 State");
setTodos(todos);
```

正确：

```tsx
setTodos((prev) => [...prev, "学习 State"]);
```

删除：

```tsx
setTodos((prev) => prev.filter((item) => item !== "学习 JSX"));
```

修改：

```tsx
setTodos((prev) =>
  prev.map((item) => (item === "学习 JSX" ? "学习 JSX 和组件" : item)),
);
```

记住一句话：**React 状态里的对象和数组，更新时创建新值，不要原地改。**

## 5.4 哪些东西应该放进 State

不是所有变量都应该放进 state。

应该放进 state 的：

- 用户输入的内容。
- 当前选中的 tab。
- 弹窗是否打开。
- 请求是否 loading。
- 错误信息。
- 列表数据。
- 需要触发重新渲染的 UI 状态。

不应该放进 state 的：

- 可以从 props 或其他 state 算出来的值。
- 不影响页面显示的临时变量。
- 固定配置。
- 每次渲染都能重新计算且成本很低的值。

错误例子：

```tsx
const [firstName, setFirstName] = useState("小");
const [lastName, setLastName] = useState("明");
const [fullName, setFullName] = useState("小明");
```

`fullName` 可以直接算：

```tsx
const fullName = firstName + lastName;
```

能算出来的状态不要复制一份。复制状态会带来同步问题：你必须记得在每次 `firstName` 或 `lastName` 变化时更新 `fullName`，这就是 bug 的来源。

# 6. 事件：用户操作如何改变状态

React 事件写法和 DOM 事件类似，但命名是驼峰：

```tsx
function App() {
  function handleClick() {
    alert("clicked");
  }

  return <button onClick={handleClick}>点击</button>;
}
```

不要写成：

```tsx
<button onClick={handleClick()}>点击</button>
```

这样会在渲染时立刻执行函数，而不是点击时执行。

需要传参数时，用箭头函数：

```tsx
<button onClick={() => deleteTodo(todo.id)}>删除</button>
```

表单提交：

```tsx
import type { FormEvent } from "react";

function SearchBox() {
  const [keyword, setKeyword] = useState("");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    console.log("搜索", keyword.trim());
  }

  return (
    <form onSubmit={handleSubmit}>
      <input
        value={keyword}
        onChange={(event) => setKeyword(event.target.value)}
        placeholder="输入关键词"
      />
      <button type="submit">搜索</button>
    </form>
  );
}
```

`event.preventDefault()` 是为了阻止浏览器默认刷新页面。

# 7. 条件渲染：不同状态显示不同 UI

React 里常见三种条件渲染。

## 7.1 if 提前返回

```tsx
function UserPanel({ user }: { user: { name: string } | null }) {
  if (!user) {
    return <p>请先登录</p>;
  }

  return <p>欢迎你，{user.name}</p>;
}
```

适合分支比较大的情况。

## 7.2 三元表达式

```tsx
function LoginStatus({ isLogin }: { isLogin: boolean }) {
  return <p>{isLogin ? "已登录" : "未登录"}</p>;
}
```

适合短分支。

## 7.3 `&&` 短路渲染

```tsx
function ErrorMessage({ error }: { error?: string }) {
  return <>{error && <p className="error">{error}</p>}</>;
}
```

但要小心数字 `0`：

```tsx
{count && <p>有数据</p>}
```

如果 `count` 是 `0`，页面可能显示 `0`。更稳妥：

```tsx
{count > 0 && <p>有数据</p>}
```

# 8. 列表渲染：map 和 key

列表渲染用 `map`：

```tsx
type Article = {
  id: string;
  title: string;
};

function ArticleList({ articles }: { articles: Article[] }) {
  return (
    <ul>
      {articles.map((article) => (
        <li key={article.id}>{article.title}</li>
      ))}
    </ul>
  );
}
```

`key` 非常重要。它帮助 React 判断列表里每一项是谁。不要随手用数组下标：

```tsx
{articles.map((article, index) => (
  <li key={index}>{article.title}</li>
))}
```

如果列表永远不排序、不删除、不插入，用下标问题不大。但真实项目里列表经常变化，用下标会导致状态错位。例如你在第二个输入框里输入文字，然后删除第一项，输入框里的状态可能跑到别的项上。

优先使用稳定唯一 id：

```tsx
<li key={article.id}>{article.title}</li>
```

如果后端没有 id，前端创建时就生成一个：

```tsx
const todo = {
  id: crypto.randomUUID(),
  text: "学习 React",
};
```

不要在渲染时生成 key：

```tsx
<li key={crypto.randomUUID()}>{article.title}</li>
```

这样每次渲染 key 都变，React 会认为所有项都变成了新项，性能和状态都会出问题。

# 9. 表单：先学受控组件，再理解 React 19 的表单能力

表单是 React 新手最容易卡住的地方，因为表单既有浏览器自己的状态，又有 React 状态。

## 9.1 受控输入

最常见写法：

```tsx
function NameForm() {
  const [name, setName] = useState("");

  return (
    <label>
      姓名
      <input
        value={name}
        onChange={(event) => setName(event.target.value)}
      />
    </label>
  );
}
```

这叫受控组件。输入框的值由 React state 控制。用户输入时触发 `onChange`，你更新 state，页面重新渲染。

受控组件适合：

- 实时校验。
- 输入联动。
- 禁用提交按钮。
- 根据输入动态显示内容。
- 表单内容需要随时参与 UI 计算。

## 9.2 提交时读取 FormData

如果表单不需要每敲一个字都同步到 React state，可以提交时读取：

```tsx
import type { FormEvent } from "react";

function ContactForm() {
  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const email = String(formData.get("email") ?? "").trim();
    console.log(email);
  }

  return (
    <form onSubmit={handleSubmit}>
      <input name="email" type="email" required />
      <button type="submit">提交</button>
    </form>
  );
}
```

这种写法更接近原生表单。简单表单不一定都要把每个字段放进 state。

## 9.3 React 19 的 Form Action、useActionState、useFormStatus

React 19 对表单动作支持更好。你可以把函数传给 `<form action={...}>`，并用 `useActionState` 管理提交后的状态。

```tsx
import { useActionState } from "react";
import { useFormStatus } from "react-dom";

type FormState = {
  message: string;
};

async function saveProfile(
  _prevState: FormState,
  formData: FormData,
): Promise<FormState> {
  const name = String(formData.get("name") ?? "").trim();

  if (!name) {
    return { message: "请输入姓名" };
  }

  await new Promise((resolve) => setTimeout(resolve, 500));
  return { message: `保存成功：${name}` };
}

function SubmitButton() {
  const { pending } = useFormStatus();

  return (
    <button type="submit" disabled={pending}>
      {pending ? "保存中..." : "保存"}
    </button>
  );
}

export default function ProfileForm() {
  const [state, formAction] = useActionState(saveProfile, { message: "" });

  return (
    <form action={formAction}>
      <input name="name" placeholder="请输入姓名" />
      <SubmitButton />
      {state.message && <p>{state.message}</p>}
    </form>
  );
}
```

这不是要求新手立刻把所有表单都改成 Action。你只要知道：React 19 之后，表单不是只能靠 `onSubmit + preventDefault + useState`。但学习顺序仍然是先理解普通表单和受控组件，再学这些新能力。

# 10. Effect：连接外部系统，不是万能同步器

`useEffect` 是 React 新手最容易滥用的 Hook。

先看一个合理例子：

```tsx
import { useEffect, useState } from "react";

function Clock() {
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const timer = window.setInterval(() => {
      setNow(new Date());
    }, 1000);

    return () => {
      window.clearInterval(timer);
    };
  }, []);

  return <time>{now.toLocaleTimeString()}</time>;
}
```

这里 Effect 做的是：连接一个外部系统 `setInterval`，组件卸载时清理它。这是 Effect 的正确用途。

Effect 适合做什么？

- 订阅 WebSocket、事件监听、定时器。
- 请求接口并处理取消或过期结果。
- 和浏览器 API 同步，比如 `document.title`、`localStorage`、地图 SDK。
- 与 React 外部的系统建立连接，并在依赖变化或卸载时清理。

Effect 不适合做什么？

- 把一个 state 同步成另一个 state。
- 处理用户点击后的业务逻辑。
- 计算派生数据。
- 作为“组件加载生命周期”的机械替代。

错误例子：

```tsx
const [firstName, setFirstName] = useState("小");
const [lastName, setLastName] = useState("明");
const [fullName, setFullName] = useState("");

useEffect(() => {
  setFullName(firstName + lastName);
}, [firstName, lastName]);
```

这不需要 Effect：

```tsx
const fullName = firstName + lastName;
```

再看一个常见错误：点击按钮后保存数据，却先设置 state，再用 Effect 监听 state 去请求。

```tsx
const [shouldSave, setShouldSave] = useState(false);

useEffect(() => {
  if (shouldSave) {
    saveData();
  }
}, [shouldSave]);

<button onClick={() => setShouldSave(true)}>保存</button>
```

这也不需要 Effect。用户点击时直接执行：

```tsx
<button onClick={saveData}>保存</button>
```

记住：**如果逻辑是因为用户事件发生的，把它写在事件处理函数里；如果逻辑是因为组件显示到屏幕上需要连接外部系统，才考虑 Effect。**

## 10.1 依赖数组不是随便填的

```tsx
useEffect(() => {
  document.title = `未完成：${remaining}`;
}, [remaining]);
```

Effect 里用到了 `remaining`，依赖数组就应该包含 `remaining`。不要为了“只执行一次”故意漏依赖。漏依赖会产生旧值 bug。

如果加了依赖导致 Effect 不停执行，通常不是依赖数组的问题，而是你的 Effect 里用到了每次渲染都会重新创建的对象或函数，或者你本来就不该用 Effect。

## 10.2 请求接口时处理过期结果

初学可以这样写：

```tsx
function UserList() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let ignore = false;

    async function loadUsers() {
      try {
        setLoading(true);
        setError("");
        const response = await fetch("/api/users");

        if (!response.ok) {
          throw new Error("加载用户失败");
        }

        const data = (await response.json()) as User[];

        if (!ignore) {
          setUsers(data);
        }
      } catch (err) {
        if (!ignore) {
          setError(err instanceof Error ? err.message : "未知错误");
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    }

    loadUsers();

    return () => {
      ignore = true;
    };
  }, []);

  if (loading) return <p>加载中...</p>;
  if (error) return <p>{error}</p>;

  return (
    <ul>
      {users.map((user) => (
        <li key={user.id}>{user.name}</li>
      ))}
    </ul>
  );
}
```

`ignore` 用来避免组件已经卸载或请求已经过期时继续更新状态。真实项目里，服务端数据缓存、重试、失焦刷新、去重、分页等问题会越来越多，这时可以考虑框架的数据加载能力，或者 TanStack Query 这样的客户端请求库。

# 11. Hooks：函数组件里的能力入口

Hooks 是 React 函数组件里使用状态、生命周期相关能力和其他 React 特性的方式。常见 Hook 有：

| Hook | 用途 |
| --- | --- |
| `useState` | 声明组件状态 |
| `useEffect` | 连接外部系统和处理副作用 |
| `useRef` | 保存不触发渲染的可变值，或拿 DOM 节点 |
| `useMemo` | 缓存计算结果 |
| `useCallback` | 缓存函数引用 |
| `useReducer` | 管理复杂状态更新 |
| `useContext` | 读取 Context |
| `useTransition` | 标记非紧急更新，保持交互响应 |
| `useDeferredValue` | 延迟使用某个值，避免输入卡顿 |
| `useActionState` | 管理表单 action 的状态 |
| `useOptimistic` | 乐观更新 UI |

新手不用一口气学完所有 Hook。先学 `useState`、`useEffect`、`useRef`，再学 `useMemo`、`useCallback`、`useReducer`、`useContext`。React 19 的 `useActionState`、`useOptimistic`、`useTransition` 可以放到表单、请求和性能章节里再理解。

## 11.1 Hook 的两条硬规则

第一，Hook 只能在组件或自定义 Hook 的顶层调用。

错误：

```tsx
function App({ ok }: { ok: boolean }) {
  if (ok) {
    const [count, setCount] = useState(0);
  }

  return null;
}
```

正确：

```tsx
function App({ ok }: { ok: boolean }) {
  const [count, setCount] = useState(0);

  if (!ok) {
    return null;
  }

  return <button onClick={() => setCount(count + 1)}>{count}</button>;
}
```

第二，Hook 只能从 React 组件或自定义 Hook 调用，不能从普通函数调用。

错误：

```tsx
function formatName(name: string) {
  const [prefix] = useState("用户");
  return `${prefix}: ${name}`;
}
```

普通函数就是普通函数，不要在里面用 Hook。

为什么有这些规则？因为 React 需要按固定顺序追踪每次渲染中 Hook 对应的状态。如果你把 Hook 放到条件或循环里，顺序可能变化，React 就无法知道哪个状态对应哪个 Hook。

## 11.2 useRef：保存不触发渲染的东西

`useRef` 常见两个用途。

第一个用途：拿 DOM 节点。

```tsx
import { useRef } from "react";

function FocusInput() {
  const inputRef = useRef<HTMLInputElement>(null);

  function focus() {
    inputRef.current?.focus();
  }

  return (
    <>
      <input ref={inputRef} />
      <button onClick={focus}>聚焦输入框</button>
    </>
  );
}
```

第二个用途：保存一个可变值，但它变化时不需要重新渲染。

```tsx
function ClickTracker() {
  const clickCountRef = useRef(0);

  function handleClick() {
    clickCountRef.current += 1;
    console.log("点击次数", clickCountRef.current);
  }

  return <button onClick={handleClick}>点击</button>;
}
```

如果一个值变化后页面需要更新，用 state。如果只是保存临时值、定时器 id、DOM 节点、上一次请求 id，用 ref。

## 11.3 useMemo：缓存昂贵计算，不是默认写法

```tsx
const visibleTodos = useMemo(() => {
  return todos.filter((todo) => todo.text.includes(keyword));
}, [todos, keyword]);
```

`useMemo` 适合缓存相对昂贵的计算结果。不要把每个 `map`、每个字符串拼接都包进 `useMemo`。过度 memo 会让代码更难读，有时还没有性能收益。

一个简单判断：如果计算很便宜，先不要 memo；如果页面真的卡，先用浏览器性能工具或 React DevTools 找瓶颈，再优化。

## 11.4 useCallback：缓存函数引用，也不是默认写法

```tsx
const handleDelete = useCallback((id: string) => {
  setTodos((prev) => prev.filter((todo) => todo.id !== id));
}, []);
```

`useCallback` 常见场景：

- 你把函数传给用 `memo` 包过的子组件。
- 这个函数是某个 Effect 的依赖，并且你确实需要稳定引用。
- 你在自定义 Hook 中暴露回调，希望调用方拿到稳定函数。

不要看到函数就 `useCallback`。新手阶段先写清楚，性能问题出现后再有证据地优化。

## 11.5 useReducer：状态更新复杂时再用

`useState` 适合简单状态。状态变化规则多了，可以用 `useReducer`。

```tsx
type Todo = {
  id: string;
  text: string;
  done: boolean;
};

type Action =
  | { type: "add"; text: string }
  | { type: "toggle"; id: string }
  | { type: "remove"; id: string };

function todoReducer(state: Todo[], action: Action): Todo[] {
  switch (action.type) {
    case "add":
      return [
        { id: crypto.randomUUID(), text: action.text, done: false },
        ...state,
      ];
    case "toggle":
      return state.map((todo) =>
        todo.id === action.id ? { ...todo, done: !todo.done } : todo,
      );
    case "remove":
      return state.filter((todo) => todo.id !== action.id);
    default:
      return state;
  }
}
```

Reducer 的好处是：状态变化集中在一个函数里，可读、可测、可追踪。坏处是代码量多一点。所以它不是入门第一天的必需品，而是状态复杂后自然出现的工具。

## 11.6 useContext：跨层传数据，但别滥用

Context 解决的是“跨很多层传同一份数据”的问题，比如主题、语言、当前登录用户、权限上下文。

```tsx
import { createContext, useContext, useState } from "react";

type Theme = "light" | "dark";

type ThemeContextValue = {
  theme: Theme;
  toggleTheme: () => void;
};

const ThemeContext = createContext<ThemeContextValue | null>(null);

function useTheme() {
  const value = useContext(ThemeContext);

  if (!value) {
    throw new Error("useTheme must be used within ThemeProvider");
  }

  return value;
}

function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>("light");

  function toggleTheme() {
    setTheme((prev) => (prev === "light" ? "dark" : "light"));
  }

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

function ThemeButton() {
  const { theme, toggleTheme } = useTheme();

  return <button onClick={toggleTheme}>当前主题：{theme}</button>;
}
```

Context 不等于全局状态库。不要把所有接口数据、表单字段、页面临时状态都塞进 Context。Context 适合低频变化、跨层共享的上下文；高频变化的大状态放进去，可能导致很多组件一起重渲染。

# 12. 状态设计：React 项目最核心的工程能力

React 写得好不好，很大程度取决于状态设计。

## 12.1 状态放在哪里

一个简单判断：谁需要这个状态，状态就尽量放在离它最近的共同父组件。

```tsx
function Parent() {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  return (
    <>
      <Sidebar selectedId={selectedId} onSelect={setSelectedId} />
      <Detail selectedId={selectedId} />
    </>
  );
}
```

`Sidebar` 和 `Detail` 都需要 `selectedId`，所以它放在它们的共同父组件 `Parent`。

如果只有一个小按钮自己需要 `open`，就放按钮附近，不要放全局。

## 12.2 状态提升

如果两个兄弟组件需要共享状态，就把状态提升到父组件。

```tsx
function SearchPage() {
  const [keyword, setKeyword] = useState("");

  return (
    <>
      <SearchInput value={keyword} onChange={setKeyword} />
      <SearchResult keyword={keyword} />
    </>
  );
}
```

这叫状态提升。它比一开始就用全局 store 更简单、更可控。

## 12.3 避免重复状态

错误：

```tsx
const [items, setItems] = useState<Item[]>([]);
const [selectedItem, setSelectedItem] = useState<Item | null>(null);
```

如果 `selectedItem` 本来就是 `items` 里的某一项，更推荐存 id：

```tsx
const [items, setItems] = useState<Item[]>([]);
const [selectedId, setSelectedId] = useState<string | null>(null);

const selectedItem = items.find((item) => item.id === selectedId) ?? null;
```

这样后端刷新列表后，不容易出现 `selectedItem` 和 `items` 里的数据不一致。

## 12.4 服务端状态和客户端状态要分开

React 新手常把所有东西都叫“状态”，但项目里至少有两类：

| 类型 | 例子 | 特点 |
| --- | --- | --- |
| 客户端状态 | 当前 tab、弹窗开关、输入框内容、拖拽中状态 | 只属于当前浏览器 UI |
| 服务端状态 | 用户列表、订单详情、文章数据、权限数据 | 来源在后端，需要缓存、刷新、错误处理 |

客户端状态用 `useState`、`useReducer`、Context、Zustand 都可以。服务端状态不要随便塞进全局 store 后就不管了，因为它有过期、重试、去重、分页、乐观更新等问题。真实项目里可以用框架的数据加载能力，或者 TanStack Query。

# 13. 请求数据：从 fetch 开始，但不要永远停在 Effect

最小请求可以用 `fetch` 和 `useEffect`。但真实项目一复杂，手写请求会遇到很多重复问题：

- loading 和 error 状态重复写。
- 同一个接口被多个组件重复请求。
- 页面切回来要不要刷新。
- 网络失败要不要重试。
- 数据多久算过期。
- 提交后如何更新缓存。
- 分页和无限加载怎么做。

TanStack Query 解决的就是这些客户端服务端状态管理问题。

```tsx
import {
  QueryClient,
  QueryClientProvider,
  useQuery,
} from "@tanstack/react-query";

type User = {
  id: string;
  name: string;
};

const queryClient = new QueryClient();

async function fetchUsers(): Promise<User[]> {
  const response = await fetch("/api/users");

  if (!response.ok) {
    throw new Error("加载用户失败");
  }

  return (await response.json()) as User[];
}

function UserList() {
  const { data = [], isPending, error } = useQuery({
    queryKey: ["users"],
    queryFn: fetchUsers,
    staleTime: 60_000,
  });

  if (isPending) return <p>加载中...</p>;
  if (error) return <p>{error.message}</p>;

  return (
    <ul>
      {data.map((user) => (
        <li key={user.id}>{user.name}</li>
      ))}
    </ul>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <UserList />
    </QueryClientProvider>
  );
}
```

注意：`QueryClient` 不要写在组件函数内部，否则每次渲染都会创建新客户端，缓存就失去意义。

你不需要入门第一天就学 TanStack Query。但你要尽早建立边界：**后端数据不是普通 UI 状态。** 当项目里请求变多，就不要继续靠散落的 `useEffect + fetch` 硬撑。

# 14. 路由：页面切换不是 React 核心库负责的

React 核心库不自带路由。常见选择是 React Router。

React Router v7 现在有不同模式：Declarative Mode、Data Mode、Framework Mode。小白先从 Declarative Mode 开始就够了。

安装：

```bash
npm install react-router
```

最小示例：

```tsx
import {
  BrowserRouter,
  Link,
  Route,
  Routes,
} from "react-router";

function HomePage() {
  return <h1>首页</h1>;
}

function AboutPage() {
  return <h1>关于我</h1>;
}

function NotFoundPage() {
  return <h1>页面不存在</h1>;
}

export default function App() {
  return (
    <BrowserRouter>
      <nav>
        <Link to="/">首页</Link>
        <Link to="/about">关于</Link>
      </nav>

      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
}
```

几个点要记住：

- `BrowserRouter` 提供路由上下文。
- `Link` 用来页面内跳转，不要用普通 `<a>` 导致整页刷新。
- `Routes` 里放 `Route`。
- `path="*"` 可以兜底 404。

等你理解了基础路由，再学嵌套路由、动态参数、loader、action、Framework Mode。不要第一天就追完整路由框架能力。

# 15. 全局状态：先别急着上 Zustand / Redux

很多小白一学 React 就问：该用 Redux、Zustand 还是 Jotai？我的建议很直接：**先不用。**

React 自带的状态工具足够你完成大量页面：

- 局部状态：`useState`。
- 复杂局部状态：`useReducer`。
- 跨层共享：Context。
- 服务端状态：框架数据加载或 TanStack Query。

什么时候需要 Zustand 这类轻量全局状态库？

- 多个远距离组件频繁读写同一份客户端状态。
- Context 传值导致组件树重渲染范围太大。
- 状态更新逻辑需要集中管理。
- 状态和业务动作希望放到组件外复用。

一个简单 Zustand 例子：

```tsx
import { create } from "zustand";

type CartStore = {
  count: number;
  add: () => void;
  clear: () => void;
};

export const useCartStore = create<CartStore>()((set) => ({
  count: 0,
  add: () => set((state) => ({ count: state.count + 1 })),
  clear: () => set({ count: 0 }),
}));

function CartButton() {
  const count = useCartStore((state) => state.count);
  const add = useCartStore((state) => state.add);

  return <button onClick={add}>购物车：{count}</button>;
}
```

这段代码能用，但你不要得出“所有状态都放 Zustand”的结论。弹窗开关、单个输入框、某个页面的筛选条件，很多时候放本组件或页面组件就够了。

全局状态越多，耦合越强。能局部，就局部；需要共享，再提升；跨层太深，再 Context；仍然复杂，再考虑状态库。

# 16. TypeScript：React 新项目建议直接用 TS

现在新 React 项目，我建议直接用 TypeScript。不是因为 TS 高级，而是它能让很多小错误提前暴露。

组件 props 类型：

```tsx
type ButtonProps = {
  children: React.ReactNode;
  variant?: "primary" | "secondary";
  disabled?: boolean;
  onClick?: () => void;
};

function Button({
  children,
  variant = "primary",
  disabled = false,
  onClick,
}: ButtonProps) {
  return (
    <button
      className={`button button-${variant}`}
      disabled={disabled}
      onClick={onClick}
    >
      {children}
    </button>
  );
}
```

事件类型：

```tsx
import type { ChangeEvent, FormEvent } from "react";

function LoginForm() {
  const [email, setEmail] = useState("");

  function handleEmailChange(event: ChangeEvent<HTMLInputElement>) {
    setEmail(event.target.value);
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    console.log(email);
  }

  return (
    <form onSubmit={handleSubmit}>
      <input value={email} onChange={handleEmailChange} />
      <button type="submit">登录</button>
    </form>
  );
}
```

数组状态：

```tsx
type Todo = {
  id: string;
  text: string;
  done: boolean;
};

const [todos, setTodos] = useState<Todo[]>([]);
```

`useRef`：

```tsx
const inputRef = useRef<HTMLInputElement>(null);
```

新手不需要把 TypeScript 学成类型体操。你只要先掌握：

- props 类型怎么写。
- state 类型怎么写。
- 事件类型怎么写。
- ref 类型怎么写。
- API 返回数据类型怎么写。

能把这些写清楚，React 项目质量已经会明显提升。

# 17. 组件组织：别把所有代码写进 App.tsx

入门时一个 `App.tsx` 没问题。但项目一复杂，就要拆结构。

一个小项目可以这样组织：

```text
src/
├─ main.tsx
├─ App.tsx
├─ components/
│  ├─ Button.tsx
│  ├─ Card.tsx
│  └─ EmptyState.tsx
├─ features/
│  └─ todos/
│     ├─ TodoApp.tsx
│     ├─ TodoForm.tsx
│     ├─ TodoList.tsx
│     ├─ TodoItem.tsx
│     └─ todoTypes.ts
├─ hooks/
│  └─ useLocalStorage.ts
├─ lib/
│  └─ api.ts
└─ styles/
   └─ global.css
```

不要过度设计，也不要完全不设计。一个实用原则：

- 通用 UI 放 `components`。
- 某个业务模块自己的组件放 `features/<feature>`。
- 自定义 Hook 放 `hooks`。
- API 封装、工具函数放 `lib` 或 `utils`。
- 类型可以跟业务放一起，也可以按项目习惯集中管理。

新手常见错误是“按技术类型拆太细”：`components`、`containers`、`services`、`models`、`views`、`stores` 一大堆，但每个功能的文件散落到十个目录。小项目没必要。先按功能聚合，后续再抽公共能力。

# 18. 样式：先掌握 CSS，再谈 UI 库

React 不规定你怎么写 CSS。常见方案有：

| 方案 | 特点 |
| --- | --- |
| 普通 CSS | 最基础，适合入门 |
| CSS Modules | 类名局部化，适合组件样式 |
| Tailwind CSS | 原子类，适合快速搭 UI |
| CSS-in-JS | 样式和组件逻辑更贴近，但要关注运行时和生态 |
| UI 库 | Ant Design、MUI、Chakra UI 等，提高业务开发效率 |

新手阶段不要一上来就被 UI 库带着走。你至少要知道：

- Flex、Grid 怎么布局。
- 盒模型是什么。
- 响应式怎么写。
- hover、focus、disabled 状态怎么处理。
- 表单、按钮、列表的基础样式怎么写。

React 组件只是组织 UI，CSS 才负责视觉表现。不会 CSS，换什么框架都会痛苦。

# 19. 性能：先写对，再优化

React 性能优化有很多关键词：`memo`、`useMemo`、`useCallback`、`useTransition`、`useDeferredValue`、懒加载、代码分割、虚拟列表、React Compiler。小白很容易被这些词吓到。

入门阶段先记住几个优先级。

## 19.1 先减少不必要的状态

派生数据不要放 state。状态越少，同步 bug 越少，重渲染也越少。

```tsx
const completedCount = todos.filter((todo) => todo.done).length;
```

这种计算如果列表不大，直接算就行。

## 19.2 列表 key 要稳定

列表 key 错了，不只是性能问题，还可能是状态错位 bug。

```tsx
<li key={todo.id}>{todo.text}</li>
```

## 19.3 大组件拆小，但不要碎成渣

组件过大，状态变化会牵连很多 UI。适当拆分可以让重渲染范围更清晰。

但也不要把每个 `<span>` 都拆组件。拆组件的理由应该是职责清楚、复用明确、可读性提高。

## 19.4 慢交互用 useTransition / useDeferredValue

当某些更新比较重，但又不应该阻塞输入，可以用 `useTransition`：

```tsx
import { useState, useTransition } from "react";

function SearchPage({ allItems }: { allItems: string[] }) {
  const [keyword, setKeyword] = useState("");
  const [query, setQuery] = useState("");
  const [isPending, startTransition] = useTransition();

  function handleChange(value: string) {
    setKeyword(value);
    startTransition(() => {
      setQuery(value);
    });
  }

  const results = allItems.filter((item) => item.includes(query));

  return (
    <>
      <input value={keyword} onChange={(event) => handleChange(event.target.value)} />
      {isPending && <p>更新结果中...</p>}
      <ul>
        {results.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </>
  );
}
```

或者用 `useDeferredValue` 延迟使用输入值：

```tsx
const deferredKeyword = useDeferredValue(keyword);
const results = allItems.filter((item) => item.includes(deferredKeyword));
```

这些是交互优化工具，不是每个页面都要用。

## 19.5 React Compiler 是未来方向，但不是免死金牌

React Compiler 已经进入稳定主线，它能在符合规则的 React 代码上自动做一些 memo 化优化。但它不是让你随便写副作用、随便改对象、随便破坏 Hooks 规则的借口。

你仍然要写纯组件、正确状态更新、稳定数据流。Compiler 能帮你优化，但不能替你修错误心智模型。

## 19.6 Bundle 优化不要忘

React 页面慢，有时不是渲染慢，而是包太大：

- 不要随便整包引入巨型库。
- 重组件按需懒加载。
- 避免无意义的 barrel import 导致打包进过多代码。
- 第三方统计、客服、地图 SDK 延迟加载。
- 大列表考虑虚拟滚动。

优化顺序永远是：先量化，再定位，再改。不要靠感觉优化。

# 20. 调试：学会看错误，而不是只会刷新

React 新手遇到错误时，最重要的是看控制台。

常见错误：

## 20.1 `Cannot read properties of undefined`

说明你读了空值上的属性。

```tsx
<p>{user.name}</p>
```

但 `user` 可能是 `undefined`。

处理方式：

```tsx
if (!user) {
  return <p>加载中...</p>;
}

return <p>{user.name}</p>;
```

或者：

```tsx
<p>{user?.name ?? "未知用户"}</p>
```

## 20.2 `Each child in a list should have a unique "key" prop`

列表渲染忘了 key，或者 key 不唯一。

```tsx
{items.map((item) => (
  <li key={item.id}>{item.name}</li>
))}
```

## 20.3 `Too many re-renders`

通常是你在渲染过程中直接更新状态。

错误：

```tsx
function App() {
  const [count, setCount] = useState(0);
  setCount(count + 1);
  return <p>{count}</p>;
}
```

每次渲染都更新状态，更新后又渲染，死循环。

应该把更新放到事件、Effect 或明确的逻辑里。

## 20.4 Effect 无限执行

常见原因：依赖里有每次渲染都新建的对象或函数，或者 Effect 里更新的状态又触发了这个 Effect。

不要第一反应删依赖数组。先问：这个 Effect 是否真的需要？能不能把逻辑移到事件处理函数或渲染计算里？

## 20.5 开发环境 Effect 执行两次

React Strict Mode 在开发环境会额外执行某些流程，以帮助你发现副作用问题。不要看到两次就认为 React 有 bug。生产环境行为不同，但你的 Effect 仍然应该写成可清理、可重复连接的安全逻辑。

# 21. 测试：不用一开始追覆盖率，但要会测关键行为

React 测试不要只测“组件能渲染”。更有价值的是测用户行为。

一个简单测试思路：

```tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import Counter from "./Counter";

describe("Counter", () => {
  it("点击按钮后计数加一", async () => {
    const user = userEvent.setup();
    render(<Counter />);

    await user.click(screen.getByRole("button", { name: /count: 0/i }));

    expect(screen.getByRole("button", { name: /count: 1/i })).toBeInTheDocument();
  });
});
```

测试关注的是用户能看到什么、能点什么、点完发生什么，而不是组件内部 state 叫什么名字。

新手阶段可以先学三类测试：

- 工具函数测试：纯函数最好测。
- 组件行为测试：渲染、输入、点击、提交。
- 关键流程测试：登录、下单、创建文章、保存配置。

别把测试当成形式。测试是为了防止你以后改代码把已有行为弄坏。

# 22. 一个完整小项目：Todo 学习清单

下面用一个 Todo 学习清单把前面的知识串起来。这个项目不炫技，但它覆盖 React 入门必须掌握的内容：组件、props、state、事件、列表、key、表单、Effect、localStorage、TypeScript。

目标功能：

- 输入学习任务。
- 添加任务。
- 勾选完成。
- 删除任务。
- 统计未完成数量。
- 保存到 localStorage。

## 22.1 类型定义

```tsx
export type Todo = {
  id: string;
  text: string;
  done: boolean;
};
```

## 22.2 localStorage 工具函数

```tsx
import type { Todo } from "./todoTypes";

const STORAGE_KEY = "react-beginner-todos";

export function loadTodos(): Todo[] {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);

    if (!raw) {
      return [];
    }

    const value = JSON.parse(raw) as Todo[];

    if (!Array.isArray(value)) {
      return [];
    }

    return value.filter(
      (item): item is Todo =>
        typeof item?.id === "string" &&
        typeof item.text === "string" &&
        typeof item.done === "boolean",
    );
  } catch {
    return [];
  }
}

export function saveTodos(todos: Todo[]) {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(todos));
}
```

这里没有直接相信 localStorage 里的内容，因为本地存储可能被用户或旧版本代码写坏。小项目也要有基本的防御性。

## 22.3 TodoForm

```tsx
import { useState } from "react";
import type { FormEvent } from "react";

type TodoFormProps = {
  onAdd: (text: string) => void;
};

export function TodoForm({ onAdd }: TodoFormProps) {
  const [text, setText] = useState("");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const value = text.trim();

    if (!value) {
      return;
    }

    onAdd(value);
    setText("");
  }

  return (
    <form onSubmit={handleSubmit} className="todo-form">
      <input
        value={text}
        onChange={(event) => setText(event.target.value)}
        placeholder="例如：学习 useState"
      />
      <button type="submit">添加</button>
    </form>
  );
}
```

`TodoForm` 只负责输入和提交，不负责保存列表。它通过 `onAdd` 把新增内容交给父组件。

## 22.4 TodoItem

```tsx
import type { Todo } from "./todoTypes";

type TodoItemProps = {
  todo: Todo;
  onToggle: (id: string) => void;
  onRemove: (id: string) => void;
};

export function TodoItem({ todo, onToggle, onRemove }: TodoItemProps) {
  return (
    <li className="todo-item">
      <label>
        <input
          type="checkbox"
          checked={todo.done}
          onChange={() => onToggle(todo.id)}
        />
        <span className={todo.done ? "done" : ""}>{todo.text}</span>
      </label>
      <button type="button" onClick={() => onRemove(todo.id)}>
        删除
      </button>
    </li>
  );
}
```

这里的 `checked` 是受控属性。不要写 `defaultChecked` 后又想让 React 控制它。

## 22.5 TodoList

```tsx
import { TodoItem } from "./TodoItem";
import type { Todo } from "./todoTypes";

type TodoListProps = {
  todos: Todo[];
  onToggle: (id: string) => void;
  onRemove: (id: string) => void;
};

export function TodoList({ todos, onToggle, onRemove }: TodoListProps) {
  if (todos.length === 0) {
    return <p className="empty">还没有学习任务，先添加一个。</p>;
  }

  return (
    <ul className="todo-list">
      {todos.map((todo) => (
        <TodoItem
          key={todo.id}
          todo={todo}
          onToggle={onToggle}
          onRemove={onRemove}
        />
      ))}
    </ul>
  );
}
```

列表的 `key` 用 `todo.id`，不是数组下标。

## 22.6 TodoApp

```tsx
import { useEffect, useMemo, useState } from "react";
import { TodoForm } from "./TodoForm";
import { TodoList } from "./TodoList";
import { loadTodos, saveTodos } from "./todoStorage";
import type { Todo } from "./todoTypes";

export default function TodoApp() {
  const [todos, setTodos] = useState<Todo[]>(() => loadTodos());

  const remainingCount = useMemo(() => {
    return todos.filter((todo) => !todo.done).length;
  }, [todos]);

  useEffect(() => {
    saveTodos(todos);
  }, [todos]);

  function addTodo(text: string) {
    setTodos((prev) => [
      {
        id: crypto.randomUUID(),
        text,
        done: false,
      },
      ...prev,
    ]);
  }

  function toggleTodo(id: string) {
    setTodos((prev) =>
      prev.map((todo) =>
        todo.id === id ? { ...todo, done: !todo.done } : todo,
      ),
    );
  }

  function removeTodo(id: string) {
    setTodos((prev) => prev.filter((todo) => todo.id !== id));
  }

  function clearDone() {
    setTodos((prev) => prev.filter((todo) => !todo.done));
  }

  return (
    <main className="todo-app">
      <h1>React 学习清单</h1>
      <p>未完成：{remainingCount}</p>

      <TodoForm onAdd={addTodo} />
      <TodoList todos={todos} onToggle={toggleTodo} onRemove={removeTodo} />

      <button type="button" onClick={clearDone}>
        清除已完成
      </button>
    </main>
  );
}
```

这个例子里，`useMemo` 不是必须的，因为 `filter` 计算很便宜。这里写出来是为了展示用法。你完全可以直接写：

```tsx
const remainingCount = todos.filter((todo) => !todo.done).length;
```

不要为了“看起来高级”而无脑 memo。

`useEffect(() => saveTodos(todos), [todos])` 是合理的，因为 localStorage 是 React 外部系统，todos 变化时需要同步出去。

## 22.7 样式示例

```css
.todo-app {
  max-width: 720px;
  margin: 40px auto;
  padding: 24px;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  font-family: system-ui, sans-serif;
}

.todo-form {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.todo-form input {
  flex: 1;
  padding: 10px 12px;
}

.todo-list {
  display: grid;
  gap: 10px;
  padding: 0;
  list-style: none;
}

.todo-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
}

.todo-item label {
  display: flex;
  align-items: center;
  gap: 8px;
}

.todo-item .done {
  color: #6b7280;
  text-decoration: line-through;
}

.empty {
  color: #6b7280;
}
```

这个项目虽然小，但已经包含 React 入门最关键的能力。如果你能不看答案自己写出来，并能解释每一行为什么这样写，你就已经超过很多只会复制组件库代码的新手。

# 23. React 19 以后，新手应该知道哪些变化

React 发展到 19 以后，很多旧教程已经不适合作为主线。你不需要一开始深入所有新特性，但至少要知道方向。

## 23.1 Actions 和表单能力更强

React 19 让表单 Action、`useActionState`、`useFormStatus`、`useOptimistic` 这些能力更重要。它们让提交、pending 状态、乐观更新等场景更自然。

但这不等于所有表单都要马上改成 Action。入门顺序仍然是：

1. 先懂原生表单。
2. 再懂受控组件。
3. 再懂 `FormData`。
4. 再懂 React 19 的表单 Action。
5. 最后结合框架的服务端能力。

## 23.2 `ref` 的使用更自然

React 19 之后，`ref` 相关体验更现代。新手不需要死背旧版本的所有 `forwardRef` 写法，但要理解 ref 本质上是拿到 DOM 或组件暴露的命令式能力。能不用 ref，就先不用；需要聚焦输入框、测量 DOM、接第三方库时再用。

## 23.3 React Server Components 不是普通 Vite SPA 的入门内容

React Server Components 很重要，但它通常通过框架使用，比如 Next.js 或 React Router Framework Mode。小白用 Vite 学 React 基础时，不需要先学 RSC。

你可以把学习顺序分清楚：

- React 基础：组件、JSX、props、state、effects、hooks。
- React 应用：路由、请求、表单、状态管理、测试。
- React 框架：SSR、SSG、RSC、服务端数据加载、部署。

不要把第三层内容塞到第一天。

## 23.4 React Compiler 值得关注，但基础仍然第一

React Compiler 能减少手写 memo 的压力，但它建立在你写的是规则正确、纯净、可分析的 React 代码之上。乱改状态、渲染时副作用、Hook 乱用，Compiler 不会把这些变成好代码。

# 24. 一条真正适合小白的 React 学习路线

如果你从零开始，我建议按下面这条路线走。

## 第 1 阶段：JavaScript 和浏览器基础

先别急着 React。你至少要会：

- `let`、`const`、函数、箭头函数。
- 对象、数组、解构、展开运算符。
- `map`、`filter`、`find`、`reduce`。
- Promise、async/await。
- DOM 基础、事件基础。
- CSS 基础布局。

React 不是用来替代 JavaScript 的。JS 不熟，React 会学得很痛苦。

## 第 2 阶段：React 核心

按顺序学：

1. 用 Vite 创建 React + TS 项目。
2. 看懂入口 `main.tsx`。
3. 写函数组件。
4. 学 JSX。
5. 学 props 和 children。
6. 学 `useState`。
7. 学事件处理。
8. 学条件渲染。
9. 学列表渲染和 key。
10. 学受控表单。
11. 学 `useEffect`。
12. 学 Hook 规则。

这一阶段目标：能独立写 Todo、计数器、搜索列表、简单表单。

## 第 3 阶段：组件设计和状态设计

继续学：

- 状态放哪里。
- 状态提升。
- 避免重复状态。
- 组件拆分。
- 自定义 Hook。
- `useReducer`。
- Context。
- 错误边界基础。

这一阶段目标：能写一个稍微完整的页面，而不是所有东西都塞进 `App.tsx`。

## 第 4 阶段：项目能力

开始接触：

- React Router。
- API 请求封装。
- TanStack Query。
- 表单校验。
- 权限控制。
- UI 库。
- TypeScript 类型组织。
- 环境变量。
- 构建和部署。

这一阶段目标：能写一个真实的小后台或个人项目。

## 第 5 阶段：工程质量

最后再补：

- 性能分析。
- 代码分割。
- 懒加载。
- 测试。
- ESLint / Biome / Prettier。
- 目录规范。
- 可访问性。
- 错误监控。
- CI/CD。

这一阶段目标：不是“能跑”，而是“能维护”。

# 25. React 新手最容易走歪的 20 个坑

## 1. 一上来就学 Next.js

Next.js 很强，但它不是 React 基础。你连组件状态都没搞懂时，先学服务端组件、缓存、路由段、服务端动作，只会更乱。

## 2. 还在跟 Create React App 教程

旧教程很多，但现在不建议从 CRA 开始。学习基础用 Vite，生产级应用再看框架。

## 3. 把 class 组件当主线

class 组件仍然能在旧项目里见到，但新项目主线是函数组件和 Hooks。你可以知道 class 组件存在，但不需要把它当入门主线。

## 4. 直接修改 state

```tsx
user.name = "新名字";
setUser(user);
```

这类写法是 React bug 高发区。对象和数组状态更新时创建新值。

## 5. 派生数据也放 state

能算出来就直接算，不要复制一份 state 再用 Effect 同步。

## 6. 列表 key 用 index

会排序、删除、插入的列表，不要用 index 当 key。

## 7. Effect 里乱写业务逻辑

用户点击引发的事情，写事件处理函数；组件显示后需要连接外部系统，才用 Effect。

## 8. 为了消除 lint 报错删依赖

依赖数组不是装饰品。删依赖是在制造旧值 bug。

## 9. 所有状态都放全局 store

全局状态不是高级，很多时候是耦合。先局部，再提升，再 Context，再状态库。

## 10. 过早性能优化

无脑 `memo`、`useMemo`、`useCallback` 会让代码难读。先确认瓶颈，再优化。

## 11. 组件拆分没有边界

为了拆而拆，会得到一堆只包了一行 JSX 的组件。拆分应该服务职责、复用、可读性。

## 12. 完全不处理 loading 和 error

请求接口不可能永远成功。至少要处理加载中、失败、空数据。

## 13. 表单只会受控组件一种写法

受控组件很重要，但简单提交表单也可以用 `FormData`。React 19 还有更现代的 Action 能力。

## 14. 不懂浏览器基础

React 不是浏览器替代品。事件冒泡、表单默认提交、CSS 布局、可访问性，还是要懂。

## 15. 不看控制台错误

控制台已经把很多错误说得很清楚。不要只会刷新、重启开发服务器。

## 16. 盲目复制 UI 库代码

组件库能提效，但不能替你理解状态、事件、表单和数据流。

## 17. 把服务端数据当普通全局状态

接口数据有过期、缓存、重试、刷新问题。项目一复杂，用数据请求库或框架能力更稳。

## 18. 不写类型

TypeScript 不是负担。props、接口返回、事件类型写清楚，会少很多低级错。

## 19. 不会从小项目练起

只看教程不写项目，永远以为自己懂。Todo、搜索、表单、文章列表、购物车，这些小项目必须手写。

## 20. 学习目标不清

React 学习不是背 API，而是建立 UI 状态模型。你要能解释：状态在哪里、为什么放那里、谁更新它、哪些 UI 由它派生。

# 26. 最后给一张学习路线表

| 阶段 | 重点 | 练习项目 | 达标标准 |
| --- | --- | --- | --- |
| 1 | JS、CSS、浏览器基础 | 静态个人页、DOM 计数器 | 能不用框架写简单交互 |
| 2 | 组件、JSX、props | 卡片列表、文章列表 | 能拆组件并传数据 |
| 3 | state、事件、表单 | Todo、搜索框、登录表单 | 能用状态驱动 UI |
| 4 | 列表、key、Effect | 请求用户列表、倒计时 | 能处理加载、错误、清理 |
| 5 | Hooks 和状态设计 | 筛选表格、购物车 | 能说明状态放哪里 |
| 6 | 路由和请求库 | 多页面小后台 | 能处理页面跳转和 API 缓存 |
| 7 | TypeScript 和测试 | 可维护 Todo / 博客后台 | 能写清 props、接口和关键测试 |
| 8 | 性能和工程化 | 中型管理系统 | 能按证据优化，而不是凭感觉 |

# 27. 你学完这篇后应该能回答的问题

如果你真的理解了 React 入门基础，应该能回答这些问题：

1. React 组件为什么要大写开头？
2. JSX 和 HTML 有什么区别？
3. props 和 state 的区别是什么？
4. 为什么不能直接修改 state 里的对象和数组？
5. 为什么 `setState` 后立刻打印还是旧值？
6. 列表为什么需要 key？为什么不建议用 index？
7. 受控组件是什么？什么时候可以用 `FormData`？
8. `useEffect` 到底适合做什么？哪些情况不需要 Effect？
9. Hook 为什么不能写在 if 里？
10. 状态应该放在父组件、子组件、Context 还是全局 store？
11. 服务端状态和客户端状态有什么区别？
12. React Router 解决什么问题？
13. TanStack Query 解决什么问题？
14. TypeScript 在 React 里最先应该学哪些写法？
15. 性能优化应该从哪里开始？

如果这些问题你答不上来，不要急着学更大的框架。回到前面的章节，把小项目重新写一遍。

# 28. 参考资料

本文没有按旧教程照搬，而是以官方和一手资料作为事实来源，再整理成适合小白的学习路线。建议你优先读这些资料：

- [React 官方文档：Learn React](https://react.dev/learn)
- [React 官方文档：Quick Start](https://react.dev/learn)
- [React 官方文档：Installation](https://react.dev/learn/installation)
- [React 官方文档：Describing the UI](https://react.dev/learn/describing-the-ui)
- [React 官方文档：Adding Interactivity](https://react.dev/learn/adding-interactivity)
- [React 官方文档：Managing State](https://react.dev/learn/managing-state)
- [React 官方文档：Escape Hatches](https://react.dev/learn/escape-hatches)
- [React 官方文档：You Might Not Need an Effect](https://react.dev/learn/you-might-not-need-an-effect)
- [React 官方文档：Lifecycle of Reactive Effects](https://react.dev/learn/lifecycle-of-reactive-effects)
- [React 官方文档：Rules of Hooks](https://react.dev/reference/rules/rules-of-hooks)
- [React 官方文档：React 19 release](https://react.dev/blog/2024/12/05/react-19)
- [React 官方文档：React 19.2 release](https://react.dev/blog/2025/10/01/react-19-2)
- [React 官方文档：React Compiler](https://react.dev/learn/react-compiler)
- [Vite 官方文档：Getting Started](https://vite.dev/guide/)
- [React Router 官方文档：Home](https://reactrouter.com/home)
- [React Router 官方文档：Picking a Mode](https://reactrouter.com/start/modes)
- [TanStack Query 官方文档：Overview](https://tanstack.com/query/latest/docs/framework/react/overview)
- [TanStack Query 官方文档：Important Defaults](https://tanstack.com/query/latest/docs/framework/react/guides/important-defaults)
- [Zustand 官方仓库和文档](https://github.com/pmndrs/zustand)
- [Vitest 官方文档](https://vitest.dev/)

最后再强调一遍：React 入门最重要的不是背 API，而是建立稳定的 UI 状态模型。组件是 UI 的拆分方式，props 是父子输入，state 是组件记忆，事件改变 state，state 决定 UI，Effect 连接外部系统。把这条线走顺，你再学路由、请求库、状态库、框架和性能优化，都会自然很多。
