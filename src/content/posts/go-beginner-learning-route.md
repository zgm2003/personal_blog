---
title: "Go 语言基本学习路线：从变量到项目入门"
published: 2026-05-04T10:00:00Z
draft: false
tags: [置顶, Go, 入门, 基础, 学习路线, 后端]
description: "一篇强化版 Go 学习路线：从 go run、go mod、package、error、testing、context 到能读懂 admin_back_go 这种 Gin 模块化单体项目框架。"
category: Go
updated: 2026-05-31T14:55:00+08:00
---

> **本文价值**：这不是“Go 高并发神话”，也不是一上来就扔 Gin / GORM / 微服务。它以菜鸟教程的 Go 语言教程全套目录作为基础参考，再加上我自己写项目时更在意的工程判断：先知道 Go 程序怎么跑，再把变量、类型、控制流、函数、数组、切片、Map、结构体、指针、接口、错误处理、包、模块、并发和测试一个个吃掉。学 Go 不需要玄学，先把基础写熟。

# 先说结论：Go 新手不要一上来就学框架

很多人学 Go，第一天就搜 Gin，第二天就搜 GORM，第三天就想写高并发网关。这样学很容易变成“看起来会 Go，实际一写项目全靠复制”。  

Go 的学习顺序应该很实在：

1. 先会安装 Go、运行 `go run`、看懂 `package main` 和 `func main()`。
2. 再学变量、常量、基本类型、类型转换和零值。
3. 再学 `if`、`for`、`switch`、`defer` 这些控制语句。
4. 再学函数、多个返回值、错误返回、闭包。
5. 再学数组、切片、Map、range。
6. 再学结构体、方法、指针。
7. 再学接口和错误处理。
8. 再学包、模块、项目目录。
9. 最后才学 goroutine、channel、context、测试和后端框架。

这条路线看起来慢，其实最快。因为 Go 的语法不复杂，真正容易写烂的是边界、错误处理、并发生命周期和包结构。如果基础不稳，框架只会把问题藏起来。

这篇文章现在明确按一个原则来写：**菜鸟教程负责给新手一条完整、连续、可查的基础目录；我自己的内容负责把这些知识点翻译成更像真实后端项目里的学习顺序和避坑判断。**  

也就是说，它不是复制教程，也不是抛开教程自己另起一套。菜鸟教程里从环境安装、语言结构、基础语法、数据类型、变量、常量、运算符、条件语句、循环语句、函数、作用域、数组、指针、结构体、切片、range、Map、递归、类型转换、接口、泛型、错误处理、并发、文件处理、正则、类型断言到 Go Modules 的路径，是本文的参考骨架。本文会保留这条完整基础线，但不会把每个页面机械摊开，而是按“新手最容易先写错什么、项目里最先用到什么”的顺序重排。

# 0. 环境：先让第一个 Go 程序跑起来

新手第一步不是背概念，是让程序跑起来。

安装 Go 后，在命令行检查版本：

```bash
go version
```

如果能看到类似下面的输出，说明 Go 已经装好了：

```text
go version go1.xx.x windows/amd64
```

新建一个 `hello.go`：

```go
package main

import "fmt"

func main() {
    fmt.Println("Hello, Go")
}
```

运行：

```bash
go run hello.go
```

你现在只需要理解三件事：

- `package main`：表示这是一个可以直接运行的程序入口包。
- `import "fmt"`：引入标准库里的格式化输出包。
- `func main()`：程序从这里开始执行。

不要一上来纠结 GOPATH、工作区、模块代理这些东西。第一步只要确认：你能写一个文件，并且能跑。

# 1. 变量：Go 入门最先要搞明白的东西

菜鸟教程把变量放在基础语法、数据类型之后讲，这个顺序是对的。Go 新手最早卡住的，往往就是变量声明方式。

Go 声明变量有几种常见写法。

## 1.1 用 `var` 声明变量

最完整的写法：

```go
var name string = "zgm"
var age int = 23
var ok bool = true
```

这里的意思很直白：

- `var` 表示我要声明变量。
- `name` 是变量名。
- `string` 是变量类型。
- `"zgm"` 是变量值。

Go 是静态类型语言。变量是什么类型，编译时就要知道。`name` 是 `string`，你就不能后面给它塞一个整数。

## 1.2 类型可以让 Go 自己推断

下面这样也可以：

```go
var name = "zgm"
var age = 23
var ok = true
```

Go 会根据右边的值推断类型：

- `"zgm"` 推断成 `string`
- `23` 推断成 `int`
- `true` 推断成 `bool`

新手可以先这么写，别把每个类型都写出来。Go 不是让你多打字的语言。

## 1.3 函数内部可以用 `:=`

在函数里面，最常用的是短变量声明：

```go
func main() {
    name := "zgm"
    age := 23
    fmt.Println(name, age)
}
```

`:=` 可以理解成“声明变量并赋值”的快捷写法。它只能在函数内部用，不能在函数外面用。

错误写法：

```go
name := "zgm" // 不能直接写在 package 顶层
```

正确写法：

```go
var name = "zgm"

func main() {
    age := 23
    fmt.Println(name, age)
}
```

## 1.4 多个变量可以一起声明

```go
var a, b int = 1, 2
var name, age = "zgm", 23
```

也可以分组：

```go
var (
    name = "zgm"
    age  = 23
    ok   = true
)
```

分组声明适合 package 级别的配置、常量、全局变量。普通函数里不要为了显得“高级”乱分组。

## 1.5 Go 有零值，不初始化也不是垃圾值

Go 的变量如果只声明不赋值，会有默认零值：

```go
var age int
var name string
var ok bool

fmt.Println(age)  // 0
fmt.Println(name) // 空字符串
fmt.Println(ok)   // false
```

常见零值：

| 类型 | 零值 |
| --- | --- |
| `int` / `float64` | `0` |
| `string` | `""` |
| `bool` | `false` |
| 指针 / slice / map / channel / interface / function | `nil` |

零值是 Go 很重要的设计。很多好用的 Go 类型就是因为零值可用，比如 `bytes.Buffer`、`sync.Mutex`。以后你自己设计结构体，也要尽量让零值能安全使用。

## 1.6 新手变量规则

新手先记住这几条：

- 函数里优先用 `:=`，简单。
- 需要指定类型时用 `var name type`。
- package 顶层只能用 `var` 或 `const`，不能用 `:=`。
- 不要声明了不用，Go 编译器会直接报错。
- 不要用 `a`、`b`、`tmp` 乱命名，除非作用域真的很短。

# 2. 常量：不会变的值用 `const`

变量是会变的，常量是不会变的。

```go
const AppName = "admin-api"
const MaxRetry = 3
```

常量常用于：

- 固定配置名
- 状态码
- 枚举值
- 数学常数
- 业务类型

Go 里没有传统意义上的 enum，但可以用 `const + iota`：

```go
const (
    StatusPending = iota + 1
    StatusRunning
    StatusDone
    StatusFailed
)
```

这里的结果是：

```text
StatusPending = 1
StatusRunning = 2
StatusDone    = 3
StatusFailed  = 4
```

新手不要滥用 `iota`。如果业务值必须和数据库、前端、第三方接口对齐，那就显式写清楚：

```go
const (
    PermissionDir    = "DIR"
    PermissionPage   = "PAGE"
    PermissionButton = "BUTTON"
)
```

这种写法更稳。业务代码最怕“看起来聪明，实际没人敢改”。

# 3. 基本类型：先把常用类型吃透

Go 基础类型不用背全表，新手先掌握这些：

```go
bool
string
int
int64
float64
byte
rune
```

## 3.1 `int` 和 `int64`

普通计数可以用 `int`：

```go
count := 10
```

数据库 ID、时间戳、金额分单位这类更明确的数值，很多时候会用 `int64`：

```go
var userID int64 = 10001
```

不要拿 `float64` 存钱。金额最好用整数分、厘，或者用 decimal 类型库。

## 3.2 `string`、`byte`、`rune`

`string` 是字符串：

```go
name := "左光明"
```

`byte` 本质是 `uint8`，常用来处理原始字节。

`rune` 本质是 `int32`，常用来表示一个 Unicode 字符。

新手只要记住：处理中文字符长度时，不要直接用 `len(s)` 当字符数。

```go
s := "Go语言"
fmt.Println(len(s))         // 字节数，不是字符数
fmt.Println(len([]rune(s))) // 字符数
```

## 3.3 类型转换必须显式

Go 不喜欢暗中帮你转换类型：

```go
var a int = 10
var b int64 = 20

// fmt.Println(a + b) // 编译错误
fmt.Println(int64(a) + b)
```

这点刚开始烦，后面会发现它救命。隐式转换太多，接口字段、金额、ID、时间戳迟早出事故。

# 4. 控制流：`if`、`for`、`switch` 就够用了

Go 的控制流很少，学起来不难。

## 4.1 `if`

```go
age := 18

if age >= 18 {
    fmt.Println("成年人")
} else {
    fmt.Println("未成年人")
}
```

Go 的 `if` 条件不用括号，但大括号必须有。

Go 还支持在 `if` 里先声明一个变量：

```go
if score := 90; score >= 60 {
    fmt.Println("通过")
}
```

这个 `score` 只在 `if` 里面可见。作用域小，污染少。

## 4.2 `for`

Go 只有 `for`，没有 `while`。

普通循环：

```go
for i := 0; i < 5; i++ {
    fmt.Println(i)
}
```

类似 while：

```go
count := 0
for count < 5 {
    count++
}
```

死循环：

```go
for {
    // 常驻任务、消费者、服务循环会用到
}
```

遍历切片、Map 用 `range`：

```go
names := []string{"Tom", "Jerry", "Go"}

for index, name := range names {
    fmt.Println(index, name)
}
```

如果不用 index，可以用 `_` 丢掉：

```go
for _, name := range names {
    fmt.Println(name)
}
```

## 4.3 `switch`

```go
role := "admin"

switch role {
case "admin":
    fmt.Println("管理员")
case "user":
    fmt.Println("普通用户")
default:
    fmt.Println("未知角色")
}
```

Go 的 `switch` 默认不会自动往下穿透，不需要每个 case 后面写 `break`。这比很多语言更安全。

## 4.4 `defer`

`defer` 表示函数返回前执行：

```go
file, err := os.Open("data.txt")
if err != nil {
    return err
}
defer file.Close()
```

常见用途：

- 关闭文件
- 关闭响应体
- 解锁 mutex
- 记录函数退出日志
- recover panic

新手要记住：资源打开成功后，立刻想清楚什么时候关闭。Go 没有魔法替你管理资源生命周期。

# 5. 函数：多个返回值和错误处理是重点

Go 函数写法：

```go
func add(a int, b int) int {
    return a + b
}
```

相同类型可以简写：

```go
func add(a, b int) int {
    return a + b
}
```

Go 函数可以返回多个值：

```go
func divide(a, b int) (int, error) {
    if b == 0 {
        return 0, fmt.Errorf("divide by zero")
    }
    return a / b, nil
}
```

调用时：

```go
result, err := divide(10, 2)
if err != nil {
    fmt.Println(err)
    return
}

fmt.Println(result)
```

这就是 Go 的核心味道：错误是返回值，不是隐藏的异常。你必须显式处理。

新手最容易写出这种垃圾代码：

```go
result, _ := divide(10, 0)
fmt.Println(result)
```

`_` 不是垃圾桶。你忽略错误，错误就会换一种更难查的方式回来。

# 6. 数组、切片、Map：真正项目里最常用的是 slice 和 map

## 6.1 数组

数组长度固定：

```go
var nums [3]int
nums[0] = 1
nums[1] = 2
nums[2] = 3
```

也可以直接初始化：

```go
nums := [3]int{1, 2, 3}
```

数组在 Go 里不是最常用。更多时候你会用切片。

## 6.2 切片 slice

切片长度可变：

```go
nums := []int{1, 2, 3}
nums = append(nums, 4)
fmt.Println(nums)
```

切片可以截取：

```go
nums := []int{1, 2, 3, 4, 5}
part := nums[1:3] // [2 3]
```

新手要知道：切片不是数组本身，它更像是“指向底层数组的一段视图”。这会带来共享底层数组的问题。刚开始不用深挖，但要知道切片赋值、截取、append 不是简单复制。

需要预估容量时，用 `make`：

```go
users := make([]string, 0, 100)
users = append(users, "Tom")
```

这表示：长度 0，容量 100。适合你知道大概会塞多少数据的时候。

## 6.3 Map

Map 是键值对：

```go
scores := map[string]int{
    "Tom":   90,
    "Jerry": 88,
}

scores["Go"] = 100
```

读取 Map：

```go
score, ok := scores["Tom"]
if !ok {
    fmt.Println("not found")
    return
}
fmt.Println(score)
```

为什么要 `ok`？因为如果 key 不存在，Map 会返回 value 类型的零值。你不能只看 `score == 0`，因为真实分数也可能是 0。

删除：

```go
delete(scores, "Tom")
```

新手注意：Map 默认不是并发安全的。多个 goroutine 同时读写 Map 会出问题。先别急着写并发 Map，后面学 `sync.Map` 或加锁。

# 7. 结构体、方法、指针：Go 的“对象”不是 class

Go 没有 class，但有 struct。

```go
type User struct {
    ID   int64
    Name string
    Age  int
}
```

创建：

```go
u := User{
    ID:   1,
    Name: "zgm",
    Age:  23,
}
```

访问字段：

```go
fmt.Println(u.Name)
```

## 7.1 方法

给结构体加方法：

```go
func (u User) DisplayName() string {
    return fmt.Sprintf("%d-%s", u.ID, u.Name)
}
```

调用：

```go
fmt.Println(u.DisplayName())
```

这不是 class，只是给某个类型绑定函数。

## 7.2 指针

指针保存的是地址：

```go
x := 10
p := &x
*p = 20

fmt.Println(x) // 20
```

在方法里，如果你要修改原始结构体，用指针接收者：

```go
func (u *User) Rename(name string) {
    u.Name = name
}
```

如果只是读取，不修改，用值接收者也可以：

```go
func (u User) DisplayName() string {
    return u.Name
}
```

新手判断方法：

- 要修改原对象：用 `*User`
- 结构体很大，不想复制：用 `*User`
- 只是小结构体读字段：`User` 也行
- 一个类型的方法接收者最好统一，别一半值、一半指针乱写

# 8. 接口：先理解“小接口”，不要写 Java 味

Go 的接口是行为集合。

```go
type Writer interface {
    Write(p []byte) (n int, err error)
}
```

只要某个类型实现了 `Write` 方法，它就满足这个接口，不需要显式 `implements`。

自己写一个简单例子：

```go
type Greeter interface {
    Greet() string
}

type User struct {
    Name string
}

func (u User) Greet() string {
    return "hello " + u.Name
}

func Say(g Greeter) {
    fmt.Println(g.Greet())
}
```

调用：

```go
u := User{Name: "zgm"}
Say(u)
```

新手最容易犯的错误，是每个 struct 都配一个 interface：

```go
type UserService interface {
    Create()
    Update()
    Delete()
    List()
}

type UserServiceImpl struct {}
```

这不是 Go 味，这是把 Java 的坏习惯搬过来。Go 的接口应该小，应该由调用方按需要定义。真的有多个实现、需要隔离外部依赖、需要测试替身时再定义 interface。

一句话：**先写 struct，后抽 interface；先让业务跑清楚，再抽象。**

# 9. 错误处理：Go 新手必须接受“每一层都要看 error”

Go 没有传统 try/catch。错误通常作为最后一个返回值：

```go
func findUser(id int64) (*User, error) {
    if id <= 0 {
        return nil, fmt.Errorf("invalid user id: %d", id)
    }
    return &User{ID: id, Name: "zgm"}, nil
}
```

调用：

```go
user, err := findUser(1)
if err != nil {
    return err
}

fmt.Println(user.Name)
```

错误要带上下文：

```go
user, err := repo.FindUser(ctx, id)
if err != nil {
    return nil, fmt.Errorf("find user %d: %w", id, err)
}
```

`%w` 表示包装错误，后面可以用 `errors.Is`、`errors.As` 判断。

```go
if errors.Is(err, sql.ErrNoRows) {
    // 没找到
}
```

新手规则：

- 不要忽略错误。
- 不要只返回 `err`，最好加上当前业务语义。
- 不要在 repository 里返回 HTTP 状态码。
- 不要在 service 里直接写 `c.JSON`。
- 每一层只处理自己该处理的错误。

# 10. 包和模块：项目不是一堆 `.go` 文件乱扔

Go 项目通常用 module 管理。

初始化：

```bash
go mod init example.com/admin-api
```

这会生成 `go.mod`。

添加依赖后：

```bash
go mod tidy
```

它会整理依赖。

一个最小项目可以这样放：

```text
admin-api/
  go.mod
  cmd/
    admin-api/
      main.go
  internal/
    user/
      handler.go
      service.go
      repository.go
      model.go
```

新手先理解：

- `cmd/xxx/main.go` 放程序入口。
- `internal/` 放项目内部包，外部不能随便 import。
- 一个包尽量做一件事。
- 包名要短，不要叫 `common`、`utils` 装所有东西。

`utils` 是很多项目腐烂的开始。你今天放字符串工具，明天放上传，后天放支付，最后没人知道它是什么。Go 项目要靠包边界说话，不靠万能工具箱续命。

# 11. 并发：goroutine 很便宜，但不是不要钱

Go 的并发很强，但新手不要把每个函数都 `go func()`。

最简单 goroutine：

```go
go func() {
    fmt.Println("run in goroutine")
}()
```

如果主函数直接退出，goroutine 可能还没执行完。所以你需要等待：

```go
var wg sync.WaitGroup

wg.Add(1)
go func() {
    defer wg.Done()
    fmt.Println("task done")
}()

wg.Wait()
```

channel 用来传值：

```go
ch := make(chan string)

go func() {
    ch <- "hello"
}()

msg := <-ch
fmt.Println(msg)
```

多个 channel 可以用 `select`：

```go
select {
case msg := <-ch:
    fmt.Println(msg)
case <-time.After(time.Second):
    fmt.Println("timeout")
}
```

真实后端里，更重要的是 `context`：

```go
ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
defer cancel()

req, err := http.NewRequestWithContext(ctx, http.MethodGet, "https://example.com", nil)
if err != nil {
    return err
}

_, err = http.DefaultClient.Do(req)
return err
```

新手并发路线：

1. 先会 goroutine。
2. 再会 channel。
3. 再会 WaitGroup。
4. 再会 context timeout / cancel。
5. 最后再学 worker pool、限流、锁、atomic、race detector。

并发代码最怕没有退出路径。没有 cancel、没有 close、没有 WaitGroup、没有超时控制的 goroutine，不是高并发，是泄漏。

# 12. 测试：Go 项目想写稳，必须会 `go test`

Go 内置测试工具，不需要一上来装复杂框架。

文件名：

```text
user_test.go
```

测试函数：

```go
func TestAdd(t *testing.T) {
    got := add(1, 2)
    if got != 3 {
        t.Fatalf("got %d, want %d", got, 3)
    }
}
```

运行：

```bash
go test ./...
```

Go 很适合 table-driven tests：

```go
func TestDivide(t *testing.T) {
    tests := []struct {
        name    string
        a       int
        b       int
        want    int
        wantErr bool
    }{
        {name: "normal", a: 10, b: 2, want: 5},
        {name: "zero divisor", a: 10, b: 0, wantErr: true},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got, err := divide(tt.a, tt.b)
            if tt.wantErr {
                if err == nil {
                    t.Fatalf("expected error")
                }
                return
            }
            if err != nil {
                t.Fatalf("unexpected error: %v", err)
            }
            if got != tt.want {
                t.Fatalf("got %d, want %d", got, tt.want)
            }
        })
    }
}
```

刚开始你会觉得测试很啰嗦。但一旦你写权限、金额、订单状态、Token 校验、缓存失效，测试就是救命的。没有测试的重构就是赌博。

# 13. 一条真正适合新手的 Go 学习路线

下面这条路线可以直接照着走。

## 第 1 阶段：跑起来

目标：能写 `hello.go`，能用 `go run`，能看懂 `package main`。

练习：

- 打印姓名、年龄、城市。
- 写一个 `main.go`，输出三行信息。
- 改错：故意删掉 `import "fmt"`，看看编译器报什么。

不要跳过报错。新手真正的成长来自看懂错误。

## 第 2 阶段：变量、常量、类型

目标：熟悉 `var`、`:=`、`const`、零值、类型转换。

练习：

- 写一个学生成绩程序：姓名、语文、数学、英语、总分、平均分。
- 写一个金额分转元的程序：`amountFen := 12345`，输出 `123.45`。
- 写一个权限类型常量：`DIR`、`PAGE`、`BUTTON`。

这个阶段不要碰框架，只写小文件。

## 第 3 阶段：控制流和函数

目标：会写 `if`、`for`、`switch`、函数返回值和错误。

练习：

- 写一个判断成绩等级的函数。
- 写一个计算阶乘的函数。
- 写一个除法函数，除数为 0 返回 error。
- 用 `switch` 判断用户角色。

你要开始习惯：函数不要太长，一件事一个函数。

## 第 4 阶段：slice、map、struct

目标：能表达一组数据、一张映射表、一个业务对象。

练习：

- 用 slice 保存多个用户名。
- 用 map 保存用户分数。
- 定义 `User` 结构体，包含 ID、Name、Role。
- 写一个函数，根据用户角色判断是否有权限。

这一步开始接近业务代码了。后台系统本质上就是一堆结构体、状态、规则和数据流。

## 第 5 阶段：指针、方法、接口

目标：理解值传递和指针修改，理解方法绑定，理解接口是行为。

练习：

- 给 `User` 写 `Rename` 方法。
- 写一个 `Greeter` 接口。
- 写一个 `Repository` 接口，只定义 `FindByID` 一个方法。
- 不要写 `ServiceImpl`，不要每个 struct 都配 interface。

这一步要建立 Go 味。Go 不是没有架构，但 Go 的架构应该简单、明确、少抽象。

## 第 6 阶段：包、模块、目录

目标：能把代码拆成多个包，不再所有东西都塞 `main.go`。

练习：

```text
go-basic-demo/
  go.mod
  cmd/
    demo/
      main.go
  internal/
    user/
      user.go
      service.go
```

要求：

- `main.go` 只负责启动。
- `user.go` 放结构体。
- `service.go` 放业务函数。
- 不要建 `utils` 大杂烩。

## 第 7 阶段：测试

目标：会写基础单元测试，会跑 `go test ./...`。

练习：

- 给成绩等级函数写测试。
- 给除法函数写成功和失败测试。
- 给权限判断函数写 table-driven tests。

测试不是给面试官看的，是给你以后敢改代码用的。

## 第 8 阶段：并发

目标：理解 goroutine、channel、WaitGroup、context。

练习：

- 启动 3 个 goroutine 打印任务。
- 用 channel 收集结果。
- 用 WaitGroup 等待全部完成。
- 用 context 控制超时。

不要一开始就写复杂 worker pool。先知道每个 goroutine 怎么退出。

## 第 9 阶段：小项目

基础学完后，别继续刷语法。直接做小项目。

建议项目：

1. 命令行 Todo：增删改查任务，保存到 JSON 文件。
2. 简单 HTTP API：用户列表、用户详情、创建用户。
3. 权限判断 Demo：角色、菜单、按钮权限。
4. 日志解析工具：读取日志文件，统计错误数量。
5. Redis 队列 Demo：模拟任务入队、消费、失败重试。

这些项目比“看完一百篇语法教程”更有用。Go 是工程语言，必须在工程里学。

# 14. Go 学习里最容易走歪的地方

## 14.1 上来就学微服务

新手不需要先学微服务。你连 package、context、error、test 都没写顺，就去拆服务，只会制造分布式垃圾。

先写一个清楚的单体。边界清楚以后，未来真要拆服务也容易。

## 14.2 把 Go 写成 Java

常见坏味道：

```text
controller/
service/
serviceimpl/
manager/
factory/
bo/
vo/
dto/
converter/
assembler/
```

目录看起来很专业，实际每改一个字段穿十层。Go 项目应该少一点仪式感，多一点直接表达。

## 14.3 所有错误都 `return err`

直接返回底层 error，日志里会丢业务上下文。更好的写法是包装：

```go
return fmt.Errorf("load user profile %d: %w", userID, err)
```

## 14.4 所有东西都塞 `utils`

`utils` 最容易变垃圾桶。更好的命名是按领域：

```text
internal/token
internal/password
internal/upload
internal/permission
```

名字就是边界。边界不清，代码迟早烂。

## 14.5 乱开 goroutine

`go func()` 不是性能优化按钮。没有退出条件的 goroutine 会泄漏；没有错误回传的 goroutine 会吞错误；没有 context 的网络请求会挂死。

# 15. 最后给一张学习路线表

| 阶段 | 重点 | 能力标准 |
| --- | --- | --- |
| 1 | 环境、Hello World | 能运行 `.go` 文件 |
| 2 | 变量、常量、类型 | 能写基础计算和字符串处理 |
| 3 | if / for / switch / defer | 能写清楚的业务判断 |
| 4 | 函数和 error | 能把逻辑拆成函数并处理失败 |
| 5 | slice / map / struct | 能表达列表、映射和业务对象 |
| 6 | 指针和方法 | 能修改对象并封装行为 |
| 7 | interface | 能用小接口隔离依赖 |
| 8 | package / module | 能组织一个小项目 |
| 9 | goroutine / channel / context | 能写有退出路径的并发任务 |
| 10 | testing | 能用测试保护重构 |
| 11 | 小项目 | 能写一个能运行、能维护的小后端 |

# 结尾：Go 的核心不是“炫”，而是清楚

Go 学到最后，你会发现它真正厉害的地方不是语法多，也不是框架多，而是它逼你把事情写清楚。

- 变量是什么类型，写清楚。
- 错误在哪里发生，返回清楚。
- 包负责什么，边界清楚。
- goroutine 什么时候退出，生命周期清楚。
- HTTP handler、service、repository 分别做什么，职责清楚。

这就是我喜欢 Go 的原因。它不鼓励你堆魔法，也不鼓励你写一堆没人看得懂的抽象。对后台系统来说，这种简单、显式、可验证的风格，比“看起来很高级”更值钱。

如果你是新手，就按这条路线走。先别急着喊高并发，先把变量、函数、错误、结构体、包和测试写熟。基础稳了，后面学 Gin、GORM、Redis、RBAC、队列、SSE、WebSocket，都只是自然展开。

## 参考资料

- [菜鸟教程：Go 语言教程（全套目录）](https://www.runoob.com/go/go-tutorial.html)
- [菜鸟教程：Go 语言变量](https://www.runoob.com/go/go-variables.html)
- [A Tour of Go：Basics](https://go.dev/tour/basics/1)
- [Go 官方教程：Get started with Go](https://go.dev/doc/tutorial/getting-started)
- [Go 官方教程：Create a Go module](https://go.dev/doc/tutorial/create-module)

<!-- go-20260531-strengthening:BEGIN -->

# 2026-05-31 强化：Go 学习要尽早进入工程结构

前面讲了变量、类型、控制流、函数、slice、map、struct、interface、error、goroutine 和测试。这里补关键一层：**Go 不是靠框架学会的，Go 是靠 package、module、显式 error、context、测试和小接口学会的。**

官方 Go 入门很早就让你 `go mod init`。这不是细节，而是在告诉你：Go 代码不是一堆散落 `.go` 文件。代码属于 package，package 属于 module，module 用 `go.mod` 固定模块路径、Go 版本和依赖版本。

## 16. 不要把 `go mod init` 拖到最后

合理路线：

```text
1. go version / go run hello.go
2. package main / func main / import
3. go mod init example.com/learn-go
4. 变量、常量、类型、if/for/switch、函数
5. array / slice / map / struct
6. 方法、指针、接口
7. error 显式返回
8. package 拆分和 module 依赖
9. testing + go test
10. goroutine / channel
11. context 控制取消和超时
12. 再学 Gin、GORM、Redis、队列
```

一个练习项目可以这样起：

```bash
mkdir learn-go
cd learn-go
go mod init example.com/learn-go
```

目录别乱堆：

```text
learn-go/
├── go.mod
├── cmd/
│   └── article-check/
│       └── main.go
└── internal/
    └── article/
        ├── parser.go
        ├── rules.go
        └── rules_test.go
```

`cmd` 放进程入口，`internal/article` 放真正业务逻辑。别把 800 行全塞进 `main.go`。

## 17. package 命名：短、小写、别重复废话

Go 的导出名会和包名一起读。不要写：

```go
article.ArticleParser{}
```

更好的名字：

```go
article.Parser{}
```

标准库是 `http.Client`、`json.Decoder`、`bufio.Reader`，不是 `http.HttpClient`。这不是省字，是减少噪音。

一个文章检查模块的数据结构：

```go
package article

type Report struct {
    Path         string
    Title        string
    BodyChars    int
    HeadingCount int
    Warnings     []string
    Errors       []string
}
```

解析 frontmatter：

```go
package article

import "strings"

func SplitFrontmatter(text string) (map[string]string, string) {
    meta := map[string]string{}
    if !strings.HasPrefix(text, "---") {
        return meta, text
    }
    parts := strings.SplitN(text, "---", 3)
    if len(parts) < 3 {
        return meta, text
    }
    for _, line := range strings.Split(parts[1], "\n") {
        key, value, ok := strings.Cut(line, ":")
        if !ok {
            continue
        }
        meta[strings.TrimSpace(key)] = strings.Trim(strings.TrimSpace(value), `"`)
    }
    return meta, parts[2]
}
```

Go 逼你写清楚输入和输出。它不鼓励魔法。

## 18. error 是控制流，不是装饰品

烂写法：

```go
data, _ := os.ReadFile(path)
```

这等于把失败当成功。正确写法：

```go
func InspectFile(path string) (Report, error) {
    data, err := os.ReadFile(path)
    if err != nil {
        return Report{}, fmt.Errorf("read article %s: %w", path, err)
    }
    return InspectText(path, string(data)), nil
}
```

`%w` 保留底层错误，调用者还能用 `errors.Is` / `errors.As` 判断。Go 的好代码不是“不出错”，而是错误路径短、清楚、可测试。

## 19. 测试是内置工作流

Go 官方教程很早就讲 `_test.go`、`TestXxx`、`testing.T` 和 `go test`。没借口不写。

```go
package article

import (
    "strings"
    "testing"
)

func TestSplitFrontmatterReadsTitle(t *testing.T) {
    meta, body := SplitFrontmatter("---\ntitle: Go 学习\n---\n\n正文")
    if meta["title"] != "Go 学习" {
        t.Fatalf("title = %q", meta["title"])
    }
    if !strings.Contains(body, "正文") {
        t.Fatalf("body missing content: %q", body)
    }
}
```

运行：

```bash
go test ./...
```

优先测试这些东西：权限判断、金额计算、状态机、缓存 key、路由权限映射、字符串解析。后台系统最可怕的 bug 通常不是语法错，而是权限和状态错。

## 20. `context`：别让 goroutine 野生繁殖

没有生命周期控制的 goroutine 是泄漏源。服务端代码要用 `context.Context` 传递取消、超时和请求级信息：

```go
func FetchUser(ctx context.Context, id int64) (*User, error) {
    req, err := http.NewRequestWithContext(ctx, http.MethodGet, userURL(id), nil)
    if err != nil {
        return nil, err
    }
    resp, err := http.DefaultClient.Do(req)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    return decodeUser(resp.Body)
}
```

后台循环也要能停：

```go
func RunWorker(ctx context.Context, jobs <-chan Job) error {
    for {
        select {
        case <-ctx.Done():
            return ctx.Err()
        case job := <-jobs:
            if err := handleJob(ctx, job); err != nil {
                return err
            }
        }
    }
}
```

Go 并发的重点不是“到处 `go func()`”，而是资源生命周期清楚。

## 21. 从基础过渡到真实项目：看 `admin_back_go`

学完基础后，不要马上抄微服务。先看 `E:\admin_go\admin_back_go` 这种模块化单体：

```text
cmd/admin-api/main.go       -> API 进程入口
cmd/admin-worker/main.go    -> Worker 进程入口
internal/bootstrap/         -> 依赖装配根
internal/server/            -> Gin router 和模块路由聚合
internal/middleware/        -> AuthToken / PermissionCheck / OperationLog / CORS
internal/config/            -> 环境变量配置模型
internal/infra/             -> MySQL / Redis / JWT / Queue / Scheduler / Storage
internal/module/            -> auth / permission / user / payment / ai 等业务模块
database/migrations/        -> SQL 迁移
scripts/                    -> smoke / contract 检查
```

这比一上来学微服务健康：部署简单，事务边界清楚，本地测试容易跑，真的遇到扩容瓶颈再拆服务也不晚。

## 22. 学习验收清单

| 阶段 | 产出 | 验收 |
| --- | --- | --- |
| 基础 | `main.go` 能运行 | `go run .` |
| module | 项目依赖初始化 | `go mod init` / `go mod tidy` |
| package | 拆出 `internal/article` | `go test ./...` |
| error | I/O 都返回错误 | 不吞 `_ = err` |
| test | 关键逻辑有单测 | `go test ./...` 通过 |
| context | HTTP/worker 支持取消 | 超时能退出 |
| concurrency | goroutine 有关闭路径 | 无野生后台循环 |
| project | 看懂 `admin_back_go` | 能说清 `cmd/bootstrap/server/module/infra` |

## 23. 参考资料

- Get started with Go：<https://go.dev/doc/tutorial/getting-started>
- Create a Go module：<https://go.dev/doc/tutorial/create-module>
- Add a test：<https://go.dev/doc/tutorial/add-a-test>
- A Tour of Go：<https://go.dev/tour/>
- Effective Go：<https://go.dev/doc/effective_go>
- Go Modules Reference：<https://go.dev/doc/modules>
- Go Concurrency Patterns: Context：<https://go.dev/blog/context>

<!-- go-20260531-strengthening:END -->
