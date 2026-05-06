---
title: "Python 基础学习手册：从语法入门到能写小项目"
published: 2026-05-06T10:00:00Z
draft: false
tags: [Python, 入门, 基础, 学习手册, 后端, 自动化]
description: "一篇写给 Python 新手的超详细基础学习手册：从环境安装、解释器、变量、数据结构、控制流、函数、模块、虚拟环境、文件处理、异常、面向对象、标准库、类型标注、测试，到能写一个真实小项目。"
category: Python
---

> **本文价值**：这不是“十分钟精通 Python”，也不是把所有语法硬塞成字典。它是一份适合新手从零开始照着走的 Python 学习手册：先把环境跑通，再学变量、类型、数据结构、控制流、函数、模块、虚拟环境、文件读写、异常、面向对象、标准库、类型标注和测试，最后用一个小项目把基础串起来。学 Python 不需要神化它，也不要小看它。它是工具，工具要能解决问题。

# 先说结论：Python 新手不要一上来就冲 AI 和框架

很多人学 Python，第一天就装一堆库，第二天就想爬虫，第三天就想写 AI 应用，第四天就开始问为什么 `pip install` 之后还是 `ModuleNotFoundError`。  

这不是 Python 难，是学习顺序烂。

Python 的学习顺序应该很朴素：

1. 先知道 Python 怎么安装、怎么运行、解释器是什么。
2. 再知道 `.py` 文件、命令行、交互式环境分别怎么用。
3. 再学变量、数字、字符串、布尔值、空值。
4. 再学 `list`、`tuple`、`dict`、`set`。
5. 再学 `if`、`for`、`while`、`match`。
6. 再学函数、参数、返回值、作用域。
7. 再学模块、包、`pip`、虚拟环境。
8. 再学文件读写、JSON、CSV。
9. 再学异常处理和日志。
10. 再学类、对象、继承、组合。
11. 再学常用标准库、类型标注和测试。
12. 最后才分方向：Web、自动化、爬虫、数据分析、AI 工程。

这条线看起来慢，其实最快。因为 Python 的语法很宽松，写得快，也很容易写烂。基础不稳时，框架会放大问题；基础稳了，再学 FastAPI、Django、Pandas、Playwright、PyTorch，都是自然展开。

本文参考 Python 官方教程、标准库文档和 Python Packaging User Guide 的基础路径，但不会照搬文档。官方文档负责定义事实，本文负责把这些事实整理成新手能真正走完的一条路线。

# 0. Python 到底是什么

Python 是一门解释型、动态类型、跨平台的编程语言。  

这句话拆开讲：

- **解释型**：你写的 `.py` 文件通常由 Python 解释器运行，不需要像 C / Go 那样先显式编译成二进制再执行。
- **动态类型**：变量本身不固定类型，值有类型。`name = "zgm"` 后，`name` 指向字符串；你后面也能让它指向数字，但不要滥用。
- **跨平台**：Windows、macOS、Linux 都能跑。
- **标准库丰富**：文件、路径、日期、JSON、正则、日志、HTTP、测试都有内置支持。
- **生态巨大**：Web、自动化、爬虫、数据分析、AI 都有成熟库。

Python 适合做什么？

| 方向 | 常见用途 |
| --- | --- |
| 自动化脚本 | 批量改文件、处理 Excel、调用接口、生成报表 |
| Web 后端 | Django、Flask、FastAPI |
| 爬虫 | requests、httpx、BeautifulSoup、Scrapy、Playwright |
| 数据处理 | pandas、numpy、matplotlib |
| AI / 机器学习 | PyTorch、TensorFlow、scikit-learn |
| 工具开发 | CLI 工具、运维脚本、代码生成器 |

Python 不适合什么？

- 不适合拿来炫语法。
- 不适合把所有逻辑都写进一个巨大的脚本文件。
- 不适合完全不管类型、不写测试、不管依赖环境。
- 不适合用“能跑”当作“能维护”的借口。

Python 的优点是快，缺点也是快。写得快，烂得也快。

# 1. 安装环境：先把解释器跑起来

新手第一步不要背语法，先让 Python 在你的机器上跑起来。

## 1.1 安装哪个版本

如果你是新手，直接安装 Python 3 的当前稳定版就行。不要装 Python 2，不要追预发布版本，也不要同时装十几个版本把自己绕晕。

在 2026 年 5 月这个时间点，Python 3.14 已经是当前主要特性版本线之一。新手只要记住一个原则：**从 python.org 下载稳定版 Python 3.x，别下载 alpha、beta、rc 预览版。**

安装完成后，在命令行检查：

```bash
python --version
```

Windows 上有时也可以用：

```bash
py --version
```

你应该看到类似：

```text
Python 3.x.x
```

不要在这里纠结小版本号。能跑，是第一目标。

## 1.2 第一个 Python 程序

新建一个文件：

```text
hello.py
```

写入：

```python
print("Hello, Python")
```

运行：

```bash
python hello.py
```

如果输出：

```text
Hello, Python
```

环境就通了。

## 1.3 交互式解释器

直接输入：

```bash
python
```

你会进入交互式环境：

```text
>>>
```

可以直接写：

```python
1 + 2
"hello".upper()
```

交互式环境适合试小东西，不适合写项目。真正的代码还是放进 `.py` 文件。

## 1.4 新手最常见的环境坑

第一个坑：装了 Python，但命令行说找不到。

原因通常是 PATH 没配置。Windows 安装时要勾选类似 “Add Python to PATH” 的选项。如果已经装完没勾，最省事的办法通常是重新运行安装器，选择修改安装，把 PATH 补上。

第二个坑：`pip install` 成功，但代码里 `import` 失败。

这通常不是库坏了，而是你安装包用的是一个 Python，运行代码用的是另一个 Python。最稳的写法是：

```bash
python -m pip install requests
python your_script.py
```

用同一个 `python` 去调用 `pip`，能少掉很多玄学问题。

第三个坑：全局安装一堆包。

全局环境不是垃圾桶。不同项目需要不同依赖，应该用虚拟环境隔离。后面会讲。

# 2. Python 文件和基本结构

Python 文件通常以 `.py` 结尾。

一个最小脚本：

```python
print("start")

name = "zgm"
age = 23

print(name, age)
print("end")
```

Python 从上往下执行。没有 `main()` 也能跑，但项目里建议写入口函数：

```python
def main():
    name = "zgm"
    age = 23
    print(name, age)


if __name__ == "__main__":
    main()
```

这段代码新手一开始看会觉得怪。先记住：

- `def main():` 定义主函数。
- `if __name__ == "__main__":` 表示这个文件被直接运行时才执行。
- 这样写方便以后把文件里的函数给别的文件导入，而不会一导入就乱执行。

这是一个好习惯。

# 3. 变量：名字指向值，不要乱起名

Python 声明变量很简单：

```python
name = "zgm"
age = 23
is_active = True
```

左边是变量名，右边是值。

Python 不需要写：

```python
string name = "zgm"
```

这是其他语言的风格，不是 Python。

## 3.1 变量名怎么写

推荐：

```python
user_name = "zgm"
order_count = 10
is_paid = False
```

不推荐：

```python
a = "zgm"
x1 = 10
flag = False
```

短变量不是不能用，但要看作用域。如果只在一两行里临时用，`i`、`n` 可以接受。业务变量别偷懒。

## 3.2 Python 是动态类型，但不是没有类型

```python
age = 23
age = "二十三"
```

这在 Python 里能运行，但这不代表你应该这样写。

坏处很明显：

```python
age = "23"
print(age + 1)
```

这会报错，因为字符串不能直接加整数。

动态类型给你自由，不是让你制造混乱。

## 3.3 常量怎么写

Python 没有真正强制不可变的常量。约定俗成用全大写：

```python
MAX_RETRY = 3
APP_NAME = "personal-blog-tool"
```

这只是约定，不是编译器强制。别人仍然可以改：

```python
MAX_RETRY = 100
```

所以 Python 项目里，约定和代码审查很重要。

# 4. 基本类型：先吃透常用的

Python 常用基础类型：

| 类型 | 示例 | 用途 |
| --- | --- | --- |
| `int` | `23` | 整数 |
| `float` | `3.14` | 小数 |
| `str` | `"hello"` | 字符串 |
| `bool` | `True` / `False` | 布尔值 |
| `NoneType` | `None` | 空值 |

## 4.1 数字

```python
count = 10
price = 19.9
total = count * price
print(total)
```

常见运算：

```python
print(10 + 3)  # 13
print(10 - 3)  # 7
print(10 * 3)  # 30
print(10 / 3)  # 3.333...
print(10 // 3) # 3，整除
print(10 % 3)  # 1，取余
print(2 ** 3)  # 8，幂
```

注意：`/` 永远得到浮点数，哪怕能整除。

```python
print(6 / 3)   # 2.0
print(6 // 3)  # 2
```

## 4.2 字符串

字符串可以用单引号或双引号：

```python
name = "zgm"
city = 'Nanjing'
```

多行字符串用三引号：

```python
message = """
第一行
第二行
第三行
"""
```

常见操作：

```python
name = "zgm"

print(name.upper())      # ZGM
print(name.startswith("z"))
print(len(name))
```

字符串拼接：

```python
first = "hello"
second = "python"
print(first + " " + second)
```

更推荐 f-string：

```python
name = "zgm"
age = 23
print(f"{name} is {age} years old")
```

f-string 是新手必须尽早掌握的东西。比 `+` 拼接清楚。

## 4.3 布尔值

```python
is_active = True
is_deleted = False
```

注意首字母大写：`True`、`False`。不是 `true`、`false`。

常见判断：

```python
age = 20
print(age >= 18)  # True
```

## 4.4 None

`None` 表示空值。

```python
user = None
```

判断是否为 `None`，用 `is`：

```python
if user is None:
    print("no user")
```

不要写：

```python
if user == None:
    print("no user")
```

能跑，但味道差。

# 5. 数据结构：list、tuple、dict、set

Python 真正项目里，最常用的不是复杂语法，而是这四个东西。

## 5.1 list：有顺序、可修改

```python
names = ["Tom", "Jerry", "Alice"]
```

读取：

```python
print(names[0])   # Tom
print(names[-1])  # Alice
```

添加：

```python
names.append("Bob")
```

删除：

```python
names.remove("Jerry")
```

遍历：

```python
for name in names:
    print(name)
```

带下标遍历：

```python
for index, name in enumerate(names):
    print(index, name)
```

切片：

```python
numbers = [1, 2, 3, 4, 5]

print(numbers[0:2])  # [1, 2]
print(numbers[:3])   # [1, 2, 3]
print(numbers[2:])   # [3, 4, 5]
```

新手要注意：list 是可变对象。

```python
a = [1, 2]
b = a
b.append(3)
print(a)  # [1, 2, 3]
```

`a` 和 `b` 指向同一个列表。不是复制。

如果要复制：

```python
b = a.copy()
```

## 5.2 tuple：有顺序、不可修改

```python
point = (10, 20)
```

读取：

```python
x = point[0]
y = point[1]
```

更常见的是解包：

```python
x, y = point
```

tuple 适合表达固定结构，比如坐标、函数返回多个值。

```python
def get_position():
    return 10, 20


x, y = get_position()
```

不要把 tuple 当成“不能改的 list”那么肤浅。它更像一个轻量的数据组合。

## 5.3 dict：键值映射，项目里极常用

```python
user = {
    "id": 1,
    "name": "zgm",
    "age": 23,
}
```

读取：

```python
print(user["name"])
```

如果 key 不存在，`user["xxx"]` 会报错。更稳的写法：

```python
nickname = user.get("nickname", "")
```

修改：

```python
user["age"] = 24
```

新增：

```python
user["email"] = "test@example.com"
```

遍历 key 和 value：

```python
for key, value in user.items():
    print(key, value)
```

dict 常用于：

- 表达 JSON 数据
- 表达配置
- 表达接口响应
- 做快速查找

## 5.4 set：去重和集合判断

```python
tags = {"Python", "Go", "Python"}
print(tags)  # {'Python', 'Go'}
```

set 会自动去重。

判断元素是否存在：

```python
if "Python" in tags:
    print("has python")
```

交集、并集、差集：

```python
a = {"Python", "Go", "PHP"}
b = {"Python", "JavaScript"}

print(a & b)  # 交集
print(a | b)  # 并集
print(a - b)  # 差集
```

权限、标签、分类、去重场景里，set 很好用。

# 6. 控制流：if、for、while、match

控制流就是程序怎么分支、怎么循环。

## 6.1 if

```python
age = 20

if age >= 18:
    print("adult")
else:
    print("child")
```

多个条件：

```python
score = 85

if score >= 90:
    print("A")
elif score >= 80:
    print("B")
elif score >= 60:
    print("C")
else:
    print("D")
```

Python 靠缩进表达代码块。缩进不是装饰，是语法。

坏写法：

```python
if score >= 60:
print("pass")
```

会直接报错。

## 6.2 条件表达式

简单分支可以写一行：

```python
age = 20
label = "adult" if age >= 18 else "child"
```

不要滥用。复杂逻辑老老实实写 `if`。

## 6.3 for

遍历列表：

```python
names = ["Tom", "Jerry", "Alice"]

for name in names:
    print(name)
```

遍历数字范围：

```python
for i in range(5):
    print(i)
```

输出 `0` 到 `4`。

指定起止：

```python
for i in range(1, 6):
    print(i)
```

输出 `1` 到 `5`。

带步长：

```python
for i in range(0, 10, 2):
    print(i)
```

输出偶数。

## 6.4 while

```python
count = 0

while count < 3:
    print(count)
    count += 1
```

`while` 适合“不知道要循环几次”的场景。新手最容易写出死循环：

```python
while True:
    print("bad")
```

除非你有明确退出条件，否则别乱写。

## 6.5 break 和 continue

`break` 结束循环：

```python
for number in [1, 2, 3, 4, 5]:
    if number == 3:
        break
    print(number)
```

`continue` 跳过当前循环：

```python
for number in [1, 2, 3, 4, 5]:
    if number % 2 == 0:
        continue
    print(number)
```

## 6.6 match

Python 3.10 之后有 `match`，类似其他语言的模式匹配。

```python
status = "paid"

match status:
    case "pending":
        print("待支付")
    case "paid":
        print("已支付")
    case "cancelled":
        print("已取消")
    case _:
        print("未知状态")
```

新手不用一开始就沉迷 `match`。先把 `if` 和 `dict` 映射写清楚。

# 7. 函数：把一段逻辑起个名字

函数是组织代码的基本单位。

```python
def greet(name):
    return f"Hello, {name}"


message = greet("zgm")
print(message)
```

## 7.1 参数和返回值

```python
def add(a, b):
    return a + b


result = add(1, 2)
```

函数应该做一件清楚的事。不要写这种：

```python
def handle_user_order_payment_notify_report():
    ...
```

名字已经长到离谱，说明职责混了。

## 7.2 默认参数

```python
def connect(host, port=3306):
    print(host, port)


connect("localhost")
connect("localhost", 3307)
```

注意：默认参数不要用可变对象。

坏写法：

```python
def add_item(item, items=[]):
    items.append(item)
    return items
```

这个 `items` 会在多次调用之间复用，容易出鬼。

好写法：

```python
def add_item(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items
```

## 7.3 关键字参数

```python
def create_user(name, age, city):
    return {
        "name": name,
        "age": age,
        "city": city,
    }


user = create_user(name="zgm", age=23, city="Nanjing")
```

参数多时，关键字参数更清楚。

## 7.4 *args 和 **kwargs

`*args` 接收多个位置参数：

```python
def total(*numbers):
    result = 0
    for number in numbers:
        result += number
    return result


print(total(1, 2, 3))
```

`**kwargs` 接收多个关键字参数：

```python
def print_profile(**profile):
    for key, value in profile.items():
        print(key, value)


print_profile(name="zgm", age=23)
```

新手不要滥用。业务函数参数应该尽量明确。

## 7.5 作用域

```python
name = "global"


def show():
    name = "local"
    print(name)


show()
print(name)
```

函数内部的 `name` 和外部的 `name` 不是一个东西。

不要为了省事到处用全局变量。全局变量让代码变得难测、难改、难追踪。

# 8. 列表推导式：好用，但别写成谜语

普通写法：

```python
numbers = [1, 2, 3, 4, 5]
squares = []

for number in numbers:
    squares.append(number * number)
```

列表推导式：

```python
squares = [number * number for number in numbers]
```

带条件：

```python
even_numbers = [number for number in numbers if number % 2 == 0]
```

这很好。

但不要写这种：

```python
result = [x.strip().lower() for row in rows for x in row if x and x.strip()]
```

能看懂，不代表好维护。超过一层循环或逻辑明显复杂时，老老实实拆开。

# 9. 模块、包、pip、虚拟环境

这是 Python 新手真正容易死的地方。

## 9.1 模块

一个 `.py` 文件就是一个模块。

比如 `math_utils.py`：

```python
def add(a, b):
    return a + b
```

在 `main.py` 中使用：

```python
from math_utils import add

print(add(1, 2))
```

## 9.2 包

包是一个目录，里面放多个模块。

```text
my_app/
  main.py
  user/
    __init__.py
    service.py
```

`user/service.py`：

```python
def get_user_name():
    return "zgm"
```

`main.py`：

```python
from user.service import get_user_name

print(get_user_name())
```

`__init__.py` 在现代 Python 里不总是必须，但新手先放着，少踩坑。

## 9.3 pip

`pip` 是 Python 包安装工具。

安装第三方库：

```bash
python -m pip install requests
```

查看已安装包：

```bash
python -m pip list
```

导出依赖：

```bash
python -m pip freeze > requirements.txt
```

安装依赖：

```bash
python -m pip install -r requirements.txt
```

记住：优先用 `python -m pip`，少用裸 `pip`。裸 `pip` 到底对应哪个 Python，有时会坑你。

## 9.4 虚拟环境

虚拟环境就是给每个项目单独放一套依赖。

创建：

```bash
python -m venv .venv
```

Windows PowerShell 激活：

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS / Linux 激活：

```bash
source .venv/bin/activate
```

激活后再安装依赖：

```bash
python -m pip install requests
```

退出虚拟环境：

```bash
deactivate
```

项目里不要提交 `.venv` 目录。它应该能被删除、重建。

`.gitignore` 里应该有：

```text
.venv/
__pycache__/
*.pyc
```

新手只要养成一个习惯：**一个项目一个 `.venv`。**

# 10. 文件读写：脚本最常用的能力

Python 很适合处理文件。

## 10.1 读取文本文件

```python
from pathlib import Path

path = Path("example.txt")
content = path.read_text(encoding="utf-8")

print(content)
```

推荐用 `pathlib.Path`，比手写字符串路径舒服。

## 10.2 写入文本文件

```python
from pathlib import Path

path = Path("output.txt")
path.write_text("Hello, Python", encoding="utf-8")
```

## 10.3 按行读取

```python
from pathlib import Path

path = Path("users.txt")

for line in path.read_text(encoding="utf-8").splitlines():
    print(line)
```

大文件不要一次性 `read_text()` 全读进内存，可以用：

```python
from pathlib import Path

path = Path("large.log")

with path.open("r", encoding="utf-8") as file:
    for line in file:
        print(line.rstrip())
```

`with` 会自动关闭文件。

## 10.4 JSON

JSON 是接口、配置、数据交换里最常见的格式。

读取 JSON：

```python
import json
from pathlib import Path

path = Path("user.json")
data = json.loads(path.read_text(encoding="utf-8"))

print(data["name"])
```

写入 JSON：

```python
import json
from pathlib import Path

user = {
    "id": 1,
    "name": "zgm",
    "skills": ["Python", "Go", "PHP"],
}

path = Path("user.json")
path.write_text(
    json.dumps(user, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
```

`ensure_ascii=False` 可以保留中文，不会变成一堆转义。

## 10.5 CSV

读取 CSV：

```python
import csv
from pathlib import Path

path = Path("users.csv")

with path.open("r", encoding="utf-8", newline="") as file:
    reader = csv.DictReader(file)
    for row in reader:
        print(row["name"], row["age"])
```

写入 CSV：

```python
import csv
from pathlib import Path

rows = [
    {"name": "Tom", "age": 20},
    {"name": "Jerry", "age": 21},
]

path = Path("users.csv")

with path.open("w", encoding="utf-8", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=["name", "age"])
    writer.writeheader()
    writer.writerows(rows)
```

文件处理是 Python 的基本功。很多真实工作不是写大系统，而是把一堆脏数据变干净。

# 11. 异常处理：不要让错误裸奔

错误一定会发生。文件不存在、接口超时、JSON 格式错、用户输入错，都很正常。

## 11.1 try / except

```python
try:
    number = int("abc")
except ValueError:
    print("不是合法数字")
```

不要这样写：

```python
try:
    number = int("abc")
except Exception:
    pass
```

这叫吞错误。代码看起来没报错，实际问题被你埋了。

## 11.2 捕获具体异常

```python
from pathlib import Path

path = Path("missing.txt")

try:
    content = path.read_text(encoding="utf-8")
except FileNotFoundError:
    print(f"文件不存在：{path}")
```

能捕获具体异常，就不要上来 `except Exception`。

## 11.3 finally

`finally` 一定会执行：

```python
try:
    print("do something")
finally:
    print("cleanup")
```

但文件、连接这类资源更推荐用 `with` 管理。

## 11.4 主动抛异常

```python
def divide(a, b):
    if b == 0:
        raise ValueError("b 不能为 0")
    return a / b
```

抛异常不是坏事。静默返回奇怪结果才坏。

# 12. 日志：别只会 print

`print` 适合学习和临时调试，不适合正式程序。

基本日志：

```python
import logging

logging.basicConfig(level=logging.INFO)

logging.info("program started")
logging.warning("something may be wrong")
logging.error("something failed")
```

带上下文：

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

user_id = 1001
logging.info("load user profile: user_id=%s", user_id)
```

日志要有上下文。不然线上看到一句 `failed`，跟没写一样。

# 13. 面向对象：类不是越多越好

Python 支持面向对象，但新手最容易把类当仪式感。

## 13.1 定义类

```python
class User:
    def __init__(self, user_id, name):
        self.user_id = user_id
        self.name = name

    def display_name(self):
        return f"{self.user_id}-{self.name}"


user = User(1, "zgm")
print(user.display_name())
```

解释：

- `class User` 定义类。
- `__init__` 是初始化方法。
- `self` 指当前对象。
- `self.name` 是对象属性。

## 13.2 dataclass

简单数据对象可以用 `dataclass`：

```python
from dataclasses import dataclass


@dataclass
class User:
    user_id: int
    name: str
    age: int


user = User(user_id=1, name="zgm", age=23)
print(user.name)
```

这比手写一堆 `__init__` 清楚。

## 13.3 继承

```python
class Animal:
    def speak(self):
        return "..."


class Dog(Animal):
    def speak(self):
        return "wang"
```

继承能用，但不要滥用。很多时候组合更简单。

## 13.4 组合优先

比如你要发送通知：

```python
class EmailSender:
    def send(self, message):
        print(f"email: {message}")


class NotificationService:
    def __init__(self, sender):
        self.sender = sender

    def notify(self, message):
        self.sender.send(message)
```

`NotificationService` 不需要继承 `EmailSender`。它只需要持有一个 sender。

好代码不是类越多越好。类是为了表达状态和行为，不是为了显得高级。

# 14. 常用标准库：先学这些就够了

Python 标准库很大，新手不需要全背。先掌握高频的。

## 14.1 pathlib

```python
from pathlib import Path

base_dir = Path("data")
file_path = base_dir / "users.json"

print(file_path.exists())
```

路径拼接用 `/`，比字符串拼接稳。

## 14.2 os

```python
import os

print(os.getenv("APP_ENV", "local"))
```

`os` 常用于环境变量、进程信息、系统相关操作。路径优先用 `pathlib`。

## 14.3 datetime

```python
from datetime import datetime

now = datetime.now()
print(now.strftime("%Y-%m-%d %H:%M:%S"))
```

日期时间很容易出坑：时区、格式、字符串转换都要小心。新手先掌握格式化和解析。

## 14.4 json

前面讲过，接口和配置经常用。

```python
import json

text = '{"name": "zgm"}'
data = json.loads(text)
```

## 14.5 re

正则：

```python
import re

text = "phone: 13800138000"
match = re.search(r"\d{11}", text)

if match:
    print(match.group())
```

正则强大，但别把业务规则全写成正则谜语。能用清楚的字符串方法解决，就别上正则。

## 14.6 argparse

写命令行工具会用到：

```python
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--name", required=True)

args = parser.parse_args()
print(f"hello {args.name}")
```

运行：

```bash
python main.py --name zgm
```

## 14.7 subprocess

调用外部命令：

```python
import subprocess

result = subprocess.run(
    ["python", "--version"],
    capture_output=True,
    text=True,
    check=True,
)

print(result.stdout)
```

不要随便把用户输入拼成 shell 命令。安全问题往往就从这里来。

# 15. 类型标注：Python 可以动态，但项目要清楚

Python 类型标注不会把 Python 变成 Java。它只是让代码更清楚。

## 15.1 基础类型标注

```python
name: str = "zgm"
age: int = 23
is_active: bool = True
```

函数：

```python
def add(a: int, b: int) -> int:
    return a + b
```

## 15.2 容器类型

```python
names: list[str] = ["Tom", "Jerry"]
scores: dict[str, int] = {"Tom": 90}
tags: set[str] = {"Python", "Go"}
point: tuple[int, int] = (10, 20)
```

## 15.3 可空类型

现代写法：

```python
def find_user_name(user_id: int) -> str | None:
    if user_id == 1:
        return "zgm"
    return None
```

调用时要处理 `None`：

```python
name = find_user_name(2)

if name is None:
    print("user not found")
else:
    print(name.upper())
```

## 15.4 TypedDict

如果你经常处理 dict，可以用 `TypedDict` 表达结构：

```python
from typing import TypedDict


class UserDict(TypedDict):
    id: int
    name: str
    age: int


def display_user(user: UserDict) -> str:
    return f"{user['id']}-{user['name']}"
```

类型标注不是为了装饰。它能让 IDE、静态检查工具和读代码的人更早发现问题。

# 16. 测试：不要靠手点验证

Python 自带 `unittest`，但新手和项目里更常用 `pytest`。

安装：

```bash
python -m pip install pytest
```

写一个函数 `calculator.py`：

```python
def add(a: int, b: int) -> int:
    return a + b
```

写测试 `test_calculator.py`：

```python
from calculator import add


def test_add():
    assert add(1, 2) == 3
```

运行：

```bash
python -m pytest
```

测试不是大型项目才需要。越是脚本，越容易因为“就改一行”把行为改坏。

## 16.1 测试什么

优先测试：

- 数据转换函数
- 文件解析函数
- 接口响应处理函数
- 金额、状态、权限等业务判断
- 容易被重构影响的核心逻辑

不要测试：

- 纯粹调用第三方库的一行包装
- 没有任何逻辑的 getter / setter
- 今天写明天删的临时代码

测试要服务现实，不是服务覆盖率数字。

# 17. 项目结构：别把所有代码塞进 main.py

一个小项目可以这样组织：

```text
python-learning-demo/
  .venv/
  .gitignore
  requirements.txt
  README.md
  main.py
  app/
    __init__.py
    config.py
    file_store.py
    service.py
  tests/
    test_service.py
```

含义：

- `main.py`：程序入口。
- `app/config.py`：配置读取。
- `app/file_store.py`：文件读写。
- `app/service.py`：业务逻辑。
- `tests/`：测试。
- `requirements.txt`：依赖列表。

不要一上来搞复杂架构。小项目先做到：

- 入口清楚。
- 业务逻辑和文件读写分开。
- 配置不要写死太多。
- 有基础测试。
- 依赖能重装。

# 18. 一个完整小项目：命令行待办清单

下面用一个小项目把基础串起来。

目标：

- 添加待办。
- 查看待办。
- 完成待办。
- 数据保存到 JSON 文件。

## 18.1 项目结构

```text
todo_app/
  main.py
  todo_store.py
  todo_service.py
  todos.json
```

## 18.2 数据格式

`todos.json`：

```json
[
  {
    "id": 1,
    "title": "学习 Python 变量",
    "done": false
  }
]
```

## 18.3 文件存储

`todo_store.py`：

```python
import json
from pathlib import Path


DATA_FILE = Path("todos.json")


def load_todos() -> list[dict]:
    if not DATA_FILE.exists():
        return []

    text = DATA_FILE.read_text(encoding="utf-8")

    if not text.strip():
        return []

    return json.loads(text)


def save_todos(todos: list[dict]) -> None:
    DATA_FILE.write_text(
        json.dumps(todos, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
```

这里做了几个必要判断：

- 文件不存在时返回空列表。
- 文件为空时返回空列表。
- 保存时用 UTF-8。
- 保存 JSON 时保留中文。

## 18.4 业务逻辑

`todo_service.py`：

```python
from todo_store import load_todos, save_todos


def list_todos() -> list[dict]:
    return load_todos()


def add_todo(title: str) -> dict:
    todos = load_todos()

    next_id = 1
    if todos:
        next_id = max(todo["id"] for todo in todos) + 1

    todo = {
        "id": next_id,
        "title": title,
        "done": False,
    }

    todos.append(todo)
    save_todos(todos)

    return todo


def complete_todo(todo_id: int) -> bool:
    todos = load_todos()

    for todo in todos:
        if todo["id"] == todo_id:
            todo["done"] = True
            save_todos(todos)
            return True

    return False
```

这段代码没有上来搞数据库，也没有搞框架。它先把“数据读取、业务处理、数据保存”这条线写清楚。

## 18.5 命令行入口

`main.py`：

```python
import argparse

from todo_service import add_todo, complete_todo, list_todos


def handle_list() -> None:
    todos = list_todos()

    if not todos:
        print("暂无待办")
        return

    for todo in todos:
        mark = "✓" if todo["done"] else " "
        print(f"{todo['id']}. [{mark}] {todo['title']}")


def handle_add(title: str) -> None:
    todo = add_todo(title)
    print(f"已添加：{todo['id']} - {todo['title']}")


def handle_done(todo_id: int) -> None:
    ok = complete_todo(todo_id)

    if ok:
        print("已完成")
    else:
        print("待办不存在")


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("list")

    add_parser = subparsers.add_parser("add")
    add_parser.add_argument("title")

    done_parser = subparsers.add_parser("done")
    done_parser.add_argument("id", type=int)

    args = parser.parse_args()

    if args.command == "list":
        handle_list()
    elif args.command == "add":
        handle_add(args.title)
    elif args.command == "done":
        handle_done(args.id)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
```

运行：

```bash
python main.py add "学习 Python 函数"
python main.py list
python main.py done 1
python main.py list
```

这个小项目覆盖了：

- 变量
- dict / list
- 函数
- 模块导入
- 文件读写
- JSON
- 条件判断
- 循环
- 命令行参数
- 简单业务逻辑

这比刷十个孤立语法例子有用。

# 19. Python 常见方向怎么继续学

基础学完后，再分方向。

## 19.1 Web 后端

路线：

1. HTTP 基础
2. JSON API
3. FastAPI 或 Django
4. 数据库：MySQL / PostgreSQL
5. ORM：SQLAlchemy / Django ORM
6. 鉴权：JWT / Session
7. 日志、配置、错误处理
8. 部署：Docker / Linux / Nginx

如果你目标是找后端工作，建议先学 FastAPI。它轻、类型友好、适合理解现代 API。

## 19.2 自动化脚本

路线：

1. pathlib / os / shutil
2. Excel / CSV / JSON
3. requests / httpx
4. argparse
5. logging
6. 定时任务
7. 打包成命令行工具

自动化最重要的是输入输出清楚。脚本也要能重复跑、能报错、能记录日志。

## 19.3 爬虫

路线：

1. HTTP 请求和响应
2. HTML 结构
3. requests / httpx
4. BeautifulSoup / lxml
5. Playwright
6. 反爬基础
7. 数据保存

爬虫不是“请求一下就完事”。要尊重网站规则，也要处理失败、重试、限速和数据清洗。

## 19.4 数据分析

路线：

1. numpy
2. pandas
3. matplotlib / seaborn
4. Jupyter
5. 数据清洗
6. 分组统计
7. 可视化

数据分析不是只会 `import pandas as pd`。真正难的是理解数据含义和清洗脏数据。

## 19.5 AI 工程

路线：

1. Python 基础
2. numpy
3. PyTorch 基础
4. API 调用
5. 向量数据库基础
6. Prompt 工程
7. RAG
8. 模型服务部署

AI 方向更不能跳基础。不会文件、JSON、异常、日志、HTTP、并发，做 AI 应用会到处漏水。

# 20. 新手最容易写烂的地方

## 20.1 一个文件写到底

坏味道：

```text
main.py  2000 行
```

这不是简单，这是失控。至少把文件读写、业务逻辑、入口拆开。

## 20.2 到处复制粘贴

看到三段相似代码，就该考虑函数。  
看到十段相似代码，还继续复制，就是坏品味。

## 20.3 吞异常

```python
try:
    do_something()
except Exception:
    pass
```

这是把错误埋到地雷里。迟早炸。

## 20.4 不用虚拟环境

全局安装依赖，今天能跑，明天另一个项目一装包就冲突。  
一个项目一个 `.venv`，这不是洁癖，是基本卫生。

## 20.5 函数太长

函数超过几十行就该警惕。不是绝对不能长，而是长函数通常在做多件事。

拆函数不是为了形式好看，是为了让每段逻辑能单独理解、单独测试。

## 20.6 命名含糊

坏命名：

```python
data = get_data()
handle(data)
```

好一点：

```python
users = load_users()
send_welcome_messages(users)
```

名字就是文档。名字烂，代码就烂一半。

## 20.7 过早上框架

不会函数、模块、异常、文件，就开始 Django / FastAPI。最后只会复制目录，不知道每层在干什么。

框架是放大器。基础好，框架放大生产力；基础差，框架放大混乱。

# 21. 最后给一张 Python 学习路线表

| 阶段 | 重点 | 能力标准 |
| --- | --- | --- |
| 1 | 安装、解释器、`.py` 文件 | 能运行脚本 |
| 2 | 变量、基础类型 | 能表达数字、字符串、布尔值和空值 |
| 3 | list / tuple / dict / set | 能处理列表、映射、去重 |
| 4 | if / for / while / match | 能写清楚的分支和循环 |
| 5 | 函数、参数、作用域 | 能把重复逻辑拆成函数 |
| 6 | 模块、包、pip | 能组织多个文件并安装依赖 |
| 7 | 虚拟环境 | 能让项目依赖隔离、可重建 |
| 8 | 文件、JSON、CSV | 能处理真实数据 |
| 9 | 异常和日志 | 能让错误可见、可追踪 |
| 10 | 类和 dataclass | 能表达业务对象 |
| 11 | 标准库 | 能独立写常见工具脚本 |
| 12 | 类型标注 | 能让代码更清楚 |
| 13 | pytest | 能用测试保护逻辑 |
| 14 | 小项目 | 能写一个可运行、可维护的小工具 |
| 15 | 分方向深入 | Web、自动化、爬虫、数据、AI |

# 结尾：Python 的核心不是“简单”，而是快而清楚

Python 容易入门，但不代表可以随便写。  

真正好的 Python 代码应该是：

- 文件结构清楚。
- 函数职责清楚。
- 数据格式清楚。
- 错误处理清楚。
- 依赖环境清楚。
- 输入输出清楚。

Python 最适合做什么？快速把想法变成工具，快速把数据处理干净，快速把接口和自动化跑起来。  

但“快”不是“乱”。  

如果你是新手，就按这份手册走。先别急着喊 AI、爬虫、Web 框架。先把变量、数据结构、函数、模块、文件、异常、虚拟环境和测试写熟。基础稳了，后面学 FastAPI、Django、Pandas、Playwright、PyTorch，都不会虚。

## 参考资料

- [Python 官方教程：The Python Tutorial](https://docs.python.org/3/tutorial/index.html)
- [Python 标准库：venv — Creation of virtual environments](https://docs.python.org/3/library/venv.html)
- [Python Packaging User Guide：Install packages in a virtual environment using pip and venv](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/)
- [Python.org：Python Source Releases](https://www.python.org/downloads/source/)
