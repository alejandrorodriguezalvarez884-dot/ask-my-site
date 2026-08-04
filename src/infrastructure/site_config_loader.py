from pathlib import Path

import yaml

from src.domain.models.entities import SiteConfig


def load_site_config(path: Path) -> SiteConfig:
    if not path.exists():
        raise FileNotFoundError(
            f"Site config not found at {path}. Copy config/site.example.yaml to "
            "config/site.yaml and fill it in with your own information."
        )
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return SiteConfig.model_validate(data)
