# SPDX-License-Identifier: MIT
from pathlib import Path
import threading
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
        # Read any language-specific overrides from SolidLSPSettings
        ls_specific = solidlsp_settings.ls_specific_settings or {}
        # store a dict of language-specific settings for easier access in methods
        self.language_specific_settings = ls_specific.get(self.get_language_enum_instance(), {})

        process_launch_info = ProcessLaunchInfo(
            cmd=self._server_command(),
            cwd=repository_root_path,
        )
        super().__init__(config, logger, repository_root_path, process_launch_info, self.LANGUAGE_ID, solidlsp_settings)
        # create readiness events similar to other LS adapters
        self.server_ready = threading.Event()
        # Nim LSPs are typically ready after initialize
        self.server_ready.set()
        self.completions_available.set()

    def _start_server(self):
        """Start Nim LSP, send initialize request and wait for response."""

        def do_nothing(params):
            return

        def window_log_message(msg):
            # log server messages
            self.logger.log(f"LSP: window/logMessage: {msg}", logging.INFO)

        # register common handlers
        self.server.on_notification("window/logMessage", window_log_message)
        self.server.on_notification("$/progress", do_nothing)
        self.server.on_notification("textDocument/publishDiagnostics", do_nothing)

        self.logger.log("Starting Nim server process", logging.INFO)
        self.server.start()

        # Prepare initialization params
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

        self.logger.log(
            "Sending initialize request from LSP client to Nim LSP server and awaiting response",
            logging.INFO,
        )
        init_response = self.server.send.initialize(initialize_params)
        self.logger.log(f"Received initialize response from nim server: {init_response}", logging.DEBUG)

        # Basic capability checks (be lenient: different servers may report different capabilities)
        try:
            if "capabilities" in init_response:
                caps = init_response["capabilities"]
                # completion provider is commonly available
                if "completionProvider" in caps:
                    self.completions_available.set()
        except Exception:
            # don't fail here; fall through and mark server ready
            pass

        # Notify the server we are initialized
        self.server.notify.initialized({})

        # mark ready
        self.server_ready.set()

    # Command to start the server
    def _server_command(self) -> List[str]:
        # Allow override from config if provided
        cfg_cmd = self.language_specific_settings.get("nim_language_server_command")
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
        return self.language_specific_settings.get("nim_initialization_options")

    # Root detection: use repo root already determined by Solid-LSP
    def workspace_folders(self) -> Optional[List[Dict[str, str]]]:
        repo_path = Path(self.repository_root_path)
        return [{
            "uri": repo_path.as_uri(),
            "name": repo_path.name,
        }]
