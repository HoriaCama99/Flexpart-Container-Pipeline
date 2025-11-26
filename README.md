# FLEXPART Complete Application 2025

End-to-end CLI workflow for preparing, running, and validating FLEXPART ERA5 simulations via Dockerized FLEXPART and flex_extract images.

## Goals
- Single entrypoint CLI for ERA5 download, preprocessing, FLEXPART runs
- Modular Python package with strong validation and logging
- Docker build assets for FLEXPART (v10.4 default) and flex_extract convert2 wrapper
- Ready for future caching, multi-user, and API layers

## Structure
```
flexpart_complete_application_2025/
├── README.md
├── pyproject.toml
├── docker/
│   ├── flexpart/
│   └── flex_extract/
├── src/
│   └── flexpart_app/
│       ├── cli.py
│       ├── config.py
│       ├── models/
│       └── services/
├── scripts/
├── docs/
└── tests/
```

## Status
Scaffolding phase. CLI and service implementations upcoming.
