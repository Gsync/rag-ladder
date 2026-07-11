import asyncio
import json
from pathlib import Path
from typing import Any

import httpx

SEM = asyncio.Semaphore(8)


def _cache_name(package: str) -> str:
    return package.replace("/", "__")


async def fetch_cached(client: httpx.AsyncClient, url: str, cache_path: Path) -> dict[str, Any]:
    """Fetch 'url' as JSON, caching the result at 'cache_path'. Skips the network if cached."""
    if cache_path.exists():
        data: dict[str, Any] = json.loads(cache_path.read_text())
        return data
    async with SEM:
        for attempt in range(4):
            try:
                r = await client.get(url, timeout=20)
                r.raise_for_status()
                payload: dict[str, Any] = r.json()
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(json.dumps(payload))
                return payload
            except httpx.HTTPError:
                if attempt == 3:
                    raise
                await asyncio.sleep(2**attempt)
    raise RuntimeError(f"unreachable: {url}")


async def get_current_version(client: httpx.AsyncClient, package: str, raw_dir: Path) -> str:
    url = f"https://api.deps.dev/v3/systems/npm/packages/{package}"
    cache_path = raw_dir / f"{_cache_name(package)}__meta.json"
    data = await fetch_cached(client, url, cache_path)
    for v in data["versions"]:
        if v["isDefault"]:
            version: str = v["versionKey"]["version"]
            return version
    raise ValueError(f"no default version found for {package}")


async def get_dependencies(
    client: httpx.AsyncClient, package: str, version: str, raw_dir: Path
) -> dict[str, Any]:
    url = f"https://api.deps.dev/v3/systems/npm/packages/{package}/versions/{version}:dependencies"
    cache_path = raw_dir / f"{_cache_name(package)}__{version}__deps.json"
    return await fetch_cached(client, url, cache_path)


def extract_package_names(deps_response: dict[str, Any]) -> set[str]:
    return {node["versionKey"]["name"] for node in deps_response["nodes"]}


def load_seeds(seeds_path: Path) -> list[str]:
    return [line.strip() for line in seeds_path.read_text().splitlines() if line.strip()]


async def discover_packages(
    client: httpx.AsyncClient, seeds: list[str], raw_dir: Path, cap: int = 1500
) -> set[str]:
    discovered: set[str] = set(seeds)
    for seed in seeds:
        try:
            version = await get_current_version(client, seed, raw_dir)
            deps = await get_dependencies(client, seed, version, raw_dir)
        except httpx.HTTPError:
            continue
        discovered |= extract_package_names(deps)
        if len(discovered) >= cap:
            break
    return set(list(discovered)[:cap])


async def get_registry_info(
    client: httpx.AsyncClient, package: str, raw_dir: Path
) -> dict[str, Any]:
    url = f"https://registry.npmjs.org/{package}"
    cache_path = raw_dir / f"{_cache_name(package)}__registry.json"
    return await fetch_cached(client, url, cache_path)


async def fetch_text_cached(client: httpx.AsyncClient, url: str, cache_path: Path) -> str:
    """Fetch `url` as text, caching the result at `cache_path`. Skips the network if cached."""
    if cache_path.exists():
        return cache_path.read_text()
    async with SEM:
        for attempt in range(4):
            try:
                r = await client.get(url, timeout=20, follow_redirects=True)
                r.raise_for_status()
                text = r.text
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(text)
                return text
            except httpx.HTTPError:
                if attempt == 3:
                    raise
                await asyncio.sleep(2**attempt)
    raise RuntimeError(f"unreachable: {url}")


async def save_readme(client: httpx.AsyncClient, package: str, readmes_dir: Path) -> None:
    url = f"https://unpkg.com/{package}/README.md"
    cache_path = readmes_dir / f"{_cache_name(package)}.md"
    await fetch_text_cached(client, url, cache_path)


FEATURE_PACKAGES = {
    "left-pad",
    "axios",
    "express",
    "chalk",
    "debug",
    "zod",
    "date-fns",
    "commander",
    "dotenv",
    "uuid",
}


async def crawl(seeds_path: Path, raw_dir: Path, readmes_dir: Path) -> None:
    seeds = load_seeds(seeds_path)
    async with httpx.AsyncClient() as client:
        packages = await discover_packages(client, seeds, raw_dir)
        for package in packages:
            try:
                await get_registry_info(client, package, raw_dir)
            except httpx.HTTPError:
                continue
            if package in FEATURE_PACKAGES:
                try:
                    await save_readme(client, package, readmes_dir)
                except httpx.HTTPError:
                    continue