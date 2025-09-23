# SPDX-License-Identifier: MIT
from pathlib import Path
from typing import List, Optional, Dict, Any


from solidlsp.ls import SolidLanguageServer

class NimLanguageServer(SolidLanguageServer):
    def _start_server(self):
        # Start the Nim language server process
        from solidlsp.lsp_protocol_handler.server import ProcessLaunchInfo
        import os
        import pathlib
        import logging

        cmd = self._server_command()
        cwd = str(self.repository_root_path)
        self.logger.log(f"Starting Nim language server with command: {cmd} in {cwd}", logging.INFO)
        self.server.start_process(ProcessLaunchInfo(cmd=cmd, cwd=cwd))

        # Prepare initialization parameters
        root_uri = pathlib.Path(cwd).as_uri()
        init_options = self.initialization_options() or {}
        initialize_params = {
            "processId": os.getpid(),
            "rootPath": cwd,
            "rootUri": root_uri,
            "capabilities": {},
            "initializationOptions": init_options,
            "workspaceFolders": self.workspace_folders(),
        }
        self.logger.log("Sending initialize request to Nim LSP server", logging.INFO)
        init_response = self.server.send.initialize(initialize_params)
        self.server.notify.initialized({})
        self.server_ready.set()
        self.completions_available.set()
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
