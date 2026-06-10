#!/usr/bin/env python3
"""Railway startup script — generates config.yaml from env vars, then launches Guanaco.

Always overwrites config.yaml to ensure env var changes take effect.

Environment variables:
  OLLAMA_API_KEY    — Primary Ollama Cloud API key (required)
  OLLAMA_API_KEY_2  — Secondary Ollama Cloud API key (optional, for dual-account rotation)
  GUANACO_PORT      — Port to listen on (default: 8080)
  GUANACO_CONFIG_DIR— Config directory (default: /data)
"""

import json
import os
import sys
from pathlib import Path

def main():
    config_dir = Path(os.environ.get("GUANACO_CONFIG_DIR", "/data"))
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.yaml"

    primary_key = os.environ.get("OLLAMA_API_KEY", "")
    secondary_key = os.environ.get("OLLAMA_API_KEY_2", "")
    port = int(os.environ.get("GUANACO_PORT", os.environ.get("PORT", "8080")))

    if not primary_key:
        print("ERROR: OLLAMA_API_KEY environment variable is required.")
        print("Set it in Railway dashboard → Variables.")
        sys.exit(1)

    # Build ollama_accounts list for dual-account rotation
    accounts = []
    accounts.append({"name": "ollama", "api_key": primary_key})

    if secondary_key:
        accounts.append({"name": "account2", "api_key": secondary_key})
        print(f"🦙 Dual-account mode: primary + secondary key configured")
    else:
        print(f"🦙 Single-account mode: only primary key configured")

    # Build config as a dict (will be serialized to YAML)
    config = {
        "ollama_api_key": primary_key,
        "ollama_accounts": accounts,
        "router": {
            "host": "0.0.0.0",
            "port": port,
            "use_tailscale": False,
            "autostart": False,
            "auto_update": False,
            "allow_prerelease": False,
        },
        "llm": {
            "default_model": "gemma4:31b",
            "reranker_model": "nemotron-3-nano:30b",
            "scraper_model": "nemotron-3-nano:30b",
            "summary_model": "nemotron-3-nano:30b",
            "fallback_model": "gemma4:31b",
            "emulate_openai": True,
            "emulate_anthropic": True,
            "available_models": [
                "qwen3.5:397b", "qwen3-coder:480b", "qwen3-vl:235b", "qwen3-next:80b",
                "gpt-oss:120b", "gpt-oss:20b",
                "deepseek-v3.1:671b", "deepseek-v3.2", "deepseek-v4-pro", "deepseek-v4-flash",
                "gemma4:31b", "gemma3:27b",
                "glm-5.1", "glm-5", "gemini-3-flash-preview",
                "minimax-m3", "minimax-m2.7", "minimax-m2.5", "minimax-m2.1",
                "devstral-small-2:24b", "devstral-2:123b",
                "nemotron-3-super", "nemotron-3-nano:30b", "nemotron-3-ultra",
                "cogito-2.1:671b", "mistral-large-3:675b",
                "kimi-k2.5", "kimi-k2.6", "ministral-3:14b",
            ],
        },
        "fallback": {
            "enabled": False,
        },
        "providers": {
            "tavily":    {"enabled": True},
            "exa":       {"enabled": True},
            "searxng":   {"enabled": True},
            "firecrawl": {"enabled": True, "require_api_key": False},
            "serper":    {"enabled": True},
            "jina":      {"enabled": True},
            "cohere":    {"enabled": True},
            "brave":     {"enabled": True},
        },
        "cache": {
            "beta_mode": False,
            "exact_cache_ttl": 600,
            "session_prefix_ttl": 3600,
            "max_entries": 500,
            "dedup_enabled": True,
            "session_prefix_enabled": True,
            "exact_cache_enabled": True,
            "min_prompt_chars": 50,
        },
        "usage": {
            "session_cookie": "",
            "check_interval": 300,
            "redirect_on_full": False,
        },
    }

    # Always overwrite config.yaml to ensure env var changes take effect
    import yaml
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)

    print(f"✅ Config written to {config_path}")
    print(f"   Port: {port}")
    print(f"   Accounts: {len(accounts)}")
    for acc in accounts:
        print(f"   - {acc['name']}: {acc['api_key'][:8]}...{acc['api_key'][-4:]}")

    # Launch Guanaco via uvicorn with the factory pattern
    import uvicorn
    from guanaco.app import create_app
    from guanaco.config import load_config

    cfg = load_config(config_path)
    app = create_app(cfg)
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    main()