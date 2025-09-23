# SPDX-License-Identifier: MIT
from pathlib import Path
from typing import List, Optional, Dict, Any
import os
import logging

from solidlsp.ls import SolidLanguageServer
from solidlsp.ls_config import LanguageServerConfig
from solidlsp.ls_logger import LanguageServerLogger
from solidlsp.lsp_protocol_handler.server import ProcessLaunchInfo
from solidlsp.settings import SolidLSPSettings

class NimLanguageServer(SolidLanguageServer):
    """
    Minimal Nim LSP adapter for Serena / Solid-LSP.

    Launches `nimlangserver` (or `nimlsp`) from PATH and wires up basic capabilities.
    Change `DEFAULT_CMD` to ["nimlsp"] if you prefer that server.
    """
    LANGUAGE_ID = "nim"
    FILE_EXTENSIONS = [".nim", ".nims"]
    DEFAULT_CMD: List[str] = ["nimlangserver"]  # or: ["nimlsp"]

    def __init__(self, config: LanguageServerConfig, logger: LanguageServerLogger, repository_root_path: str, solidlsp_settings: SolidLSPSettings):
        process_launch_info = ProcessLaunchInfo(
            cmd=self._server_command(config.config),
            cwd=repository_root_path
        )
        super().__init__(config, logger, repository_root_path, process_launch_info, self.LANGUAGE_ID, solidlsp_settings)
        self.server_ready.set()
        self.completions_available.set()

    def _start_server(self):
        # Prepare initialization parameters
        root_uri = Path(self.repository_root_path).as_uri()
        init_options = self.initialization_options() or {}
        initialize_params = {
            "processId": os.getpid(),
            "rootPath": self.repository_root_path,
            "rootUri": root_uri,
            "capabilities": {},
            "initializationOptions": init_options,
            "workspaceFolders": self.workspace_folders(),
        }
        self.logger.log("Sending initialize request to Nim LSP server", logging.INFO)
        self.server.send.initialize(initialize_params)
        self.server.notify.initialized({})

    # Command to start the server
    def _server_command(self, config: Dict[str, Any]) -> List[str]:
        # Allow override from config if provided
        cfg_cmd = config.get("nim_language_server_command")
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
