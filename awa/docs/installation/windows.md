# Installation - Windows

Follow the steps below to install AWA on your Windows PC. If you run into trouble, see our [FAQ](/introduction/faq) and [Troubleshooting](/introduction/troubleshooting) pages.

:::danger Windows Development Experience Warning

While AWA supports native Windows development, **we strongly recommend using Windows Subsystem for Linux (WSL)** for the best developer experience. WSL provides:

- Better compatibility with Unix-based tools
- Improved performance for file operations
- More reliable dependency management
- Seamless integration with Linux-based workflows

If you choose to develop on native Windows, you may encounter additional setup complexity and compatibility issues.

:::

## WSL Setup (Preferred Method)

For the optimal development experience, we recommend setting up WSL first:

1. **Install WSL**: Follow Microsoft's official WSL installation guide: [https://learn.microsoft.com/en-us/windows/wsl/install](https://learn.microsoft.com/en-us/windows/wsl/install)
2. **Install Ubuntu or your preferred Linux distribution** from the Microsoft Store
3. **Follow our [Mac & Linux installation guide](/installation/mac-linux)** once WSL is set up

## Native Windows Setup

If you prefer to develop directly on Windows, follow the steps below. For all shell commands, use **PowerShell**.

## 1. Install dependencies

[Scoop](https://scoop.sh/) is recommended as the easiest way to install and manage dependencies. But you can use whatever method you prefer (e.g. [Chocolatey](https://chocolatey.org/), [WinGet](https://winget.run/)).

<!--@include: parts/dependency_check.md-->

### Python (>=3.12)

:::code-group

```bash[Scoop]
scoop install main/python
```

```bash[WinGet]
winget install python --version 3.12.0
```

```bash[Chocolatey]
choco install python --version 3.12.0
```

:::

:::warning Can't install Python globally?
In some restrictive client environments, you may not be able to install Python globally. In this case, you might potentially be able to install Python via `uv` (below).

1. Install `uv` (see below)
2. Run `uv python install 3.12`

See uv's documentation for more details: [Installing Python](https://docs.astral.sh/uv/guides/install-python/).
:::

See [Python's installation instructions](https://www.python.org/downloads/) for detailed instructions.

### uv (>=0.7.13)

:::code-group

```bash[Scoop]
scoop install main/uv
```

```bash[PowerShell]
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

:::

See [uv's installation instructions](https://docs.astral.sh/uv/getting-started/installation/) for detailed instructions.

### make (>=4.4)

:::code-group

```bash[Scoop]
scoop install main/make
```

```markdown[WinGet]
(not available via WinGet)
```

```bash[Chocolatey]
choco install make
```

:::

See [make's installation instructions](https://learn.microsoft.com/en-us/windows/wsl/install) for detailed instructions.

### Node (>=22.16)

:::code-group

```bash[Scoop]
scoop install main/nodejs
```

```bash[WinGet]
winget install -e --id OpenJS.NodeJS
```

```bash[Chocolatey]
choco install nodejs
```

:::

Or see [Node's installation instructions](https://nodejs.org/en/download/) for detailed instructions.

### pnpm (>= 10.6.2)

:::code-group

```bash[Scoop]
scoop install main/pnpm
```

```bash[WinGet]
winget install -e --id pnpm.pnpm
```

```bash[Chocolatey]
choco install pnpm
```

:::

Or see [pnpm's installation instructions](https://pnpm.io/installation) for detailed instructions.

### Temporal CLI (>= 1.3.0)

:::code-group

```bash[Scoop]
scoop install main/temporal-cli
```

```markdown[Manual]
1. Download for your platform:

- [Windows amd64](https://temporal.download/cli/archive/latest?platform=windows&arch=amd64)
- [Windows arm64](https://temporal.download/cli/archive/latest?platform=windows&arch=arm64)

2. Unzip the file and place `temporal.exe` where you want to keep it.

3. Add the `temporal.exe` binary to your `PATH` environment variable ([instructions](https://www.architectryan.com/2018/03/17/add-to-the-path-on-windows-10/))
```

:::

See [Temporal's installation instructions](https://docs.temporal.io/cli/setup-cli) for detailed instructions.

<!--@include: parts/clone_to_end.md-->

## Troubleshooting

<!--@include: parts/troubleshooting-all.md-->
