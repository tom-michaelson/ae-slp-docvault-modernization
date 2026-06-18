# Installation - Mac & Linux

Follow the steps below to install AWA on your Mac or Linux system. If you run into trouble, see our [FAQ](/introduction/faq) and [Troubleshooting](/introduction/troubleshooting) pages.

For all shell commands, use **Terminal, bash, zsh, or similar**.

## 1. Install dependencies

Choose your preferred package manager based on your system:

<!--@include: parts/dependency_check.md-->

### Python (>=3.12)

:::code-group

```bash[Homebrew (Mac)]
brew install python
```

```bash[apt (Ubuntu/Debian)]
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev
```

```bash[yum/dnf (RHEL/Fedora)]
sudo dnf install python3.12 python3.12-devel
```

```bash[Manual]
# Download and install from python.org
curl -O https://www.python.org/ftp/python/3.12.0/Python-3.12.0.tgz
```

:::

See [Python's installation instructions](https://www.python.org/downloads/) for detailed instructions.

### uv (>=0.7.13)

:::code-group

```bash[Homebrew (Mac)]
brew install uv
```

```bash[curl (Linux/Mac)]
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```bash[pip]
pip install uv
```

:::

See [uv's installation instructions](https://docs.astral.sh/uv/getting-started/installation/) for detailed instructions.

### make (>=4.4)

:::code-group

```bash[Homebrew (Mac)]
brew install make
```

```bash[apt (Ubuntu/Debian)]
sudo apt install build-essential
```

```bash[yum/dnf (RHEL/Fedora)]
sudo dnf install make gcc gcc-c++
```

:::

### Node (>=22.16)

:::code-group

```bash[Homebrew (Mac)]
brew install node
```

```bash[apt (Ubuntu/Debian)]
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs
```

```bash[yum/dnf (RHEL/Fedora)]
curl -fsSL https://rpm.nodesource.com/setup_22.x | sudo bash -
sudo dnf install -y nodejs
```

```bash[Manual]
# Download from nodejs.org or use nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 22
```

:::

See [Node's installation instructions](https://nodejs.org/en/download/) for detailed instructions.

### pnpm (>= 10.6.2)

:::code-group

```bash[Homebrew (Mac)]
brew install pnpm
```

```bash[npm (Linux/Mac)]
npm install -g pnpm
```

```bash[curl (Linux/Mac)]
curl -fsSL https://get.pnpm.io/install.sh | sh -
```

:::

See [pnpm's installation instructions](https://pnpm.io/installation) for detailed instructions.

### Temporal CLI (>= 1.3.0)

:::code-group

```bash[Homebrew (Mac)]
brew install temporal
```

```bash[Manual (Linux)]
# Download for your platform:
# Linux amd64: https://temporal.download/cli/archive/latest?platform=linux&arch=amd64
# Linux arm64: https://temporal.download/cli/archive/latest?platform=linux&arch=arm64

# Example for Linux amd64:
curl -sSf https://temporal.download/cli.sh | sh
```

:::

See [Temporal's installation instructions](https://docs.temporal.io/cli/setup-cli) for detailed instructions.

### Docker

If you would like to use `docker compose` to run the application and supporting services, Docker is required.

:::code-group

```bash[Homebrew (Mac)]
brew install docker docker-compose colima
colima start
docker run hello-world
```

```bash[apt (Ubuntu/Debian)]
# Install Docker
sudo apt update
sudo apt install apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add user to docker group (requires logout/login)
sudo usermod -aG docker $USER
```

```bash[yum/dnf (RHEL/Fedora)]
sudo dnf install docker docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

:::

<!--@include: parts/clone_to_end.md-->

## Troubleshooting

<!--@include: parts/troubleshooting-all.md-->
