# Docker Scripts

This folder contains Docker scripts to build packages for various Linux
distros. Currently it can output packages for Fedora latest.

To use, run the Make command from the top-level folder of this git repo:

```bash
make rpm
```

Final output RPMs will be placed in `docker/dist/`
