# SPDX-License-Identifier: MIT
from pathlib import Path
from typing import List, Optional, Dict, Any


from solidlsp.ls import SolidLanguageServer

class NimLanguageServer(SolidLanguageServer):
    """
    Minimal Nim LSP adapter for Serena / Solid-LSP.

    Launches `nimlangserver` (or `nimlsp`) from PATH and wires up basic capabilities.
    Change `DEFAULT_CMD` to ["nimlsp"] if you prefer that server.
    """
    LANGUAGE_ID = "nim"
    FILE_EXTENSIONS = [".nim", ".nims"]
    DEFAULT_CMD: List[str] = ["nimlangserver"]  # or: ["nimlsp"]

    def __init__(self, config: Dict[str, Any], logger, repository_root_path: Path):
        super().__init__(config, logger, repository_root_path)

    # Command to start the server
    def _server_command(self) -> List[str]:
        # Allow override from config if provided
        cfg_cmd = self.config.get("nim_language_server_command")
        if cfg_cmd and isinstance(cfg_cmd, list):
            return cfg_cmd
        return self.DEFAULT_CMD

    # Language id sent in initialize()
    def language_id(self) -> str:
        return self.LANGUAGE_ID

    # Which files we treat as Nim
    def file_extensions(self) -> List[str]:
        return self.FILE_EXTENSIONS

    # Optionally pass initOptions through config
    def initialization_options(self) -> Optional[Dict[str, Any]]:
        return self.config.get("nim_initialization_options")

    # Root detection: use repo root already determined by Solid-LSP
    def workspace_folders(self) -> Optional[List[Dict[str, str]]]:
        return [{
            "uri": self.repository_root_path.as_uri(),
            "name": self.repository_root_path.name,
        }]
