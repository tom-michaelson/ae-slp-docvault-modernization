# Installation - Docker

You can run AWA and all related supporting services via Docker.

## 1. Install Docker and Docker Compose

Slalom currently doesn't support running [Docker Desktop](https://www.docker.com/products/docker-desktop/) (though this is the easiest solution, if your client provides a license).

### MacOS

- **Docker**: Your best option is likely [colima](https://github.com/abiosoft/colima). Follow instructions in the Colima docs to get it installed.
- **Docker Compose**: Compose can be installed via [Homebrew](https://formulae.brew.sh/formula/docker-compose).

#### Colima Config

If you already have Colima running, you must first stop it with:

```bash
colima stop
```

Then use the following command to start Colima with the correct configuration (you can increase CPU and memory resources, but use these as the minimum values):

```bash
colima start --network-address --cpu 4 --memory 8
```

Per [this open Colima issue](https://github.com/abiosoft/colima/issues/1067), you may also need to start with the following flags:

```bash
colima start --network-address --cpu 4 --memory 8 --vm-type vz --mount-type virtiofs
```

To confirm it's running, run `colima status`.

If you want to avoid having to use the parameters every time you launch Colima, create a config file here: `~/.colima/_templates/default.yaml`

```yaml
# ~/.colima/_templates/default.yaml

cpu: 4
disk: 120
memory: 8
network:
  address: true
  dnsHosts:
    host.docker.internal: host.lima.internal
```

### Windows

On Windows, you likely want to use [Rancher Desktop](https://rancherdesktop.io/), which should mostly be a drop-in replacement for Docker Desktop.

## 2. Run AWA and supporting services with Docker

Continue with our [Docker Deployment](/deployment/docker) guide to get AWA up and running with Docker.
