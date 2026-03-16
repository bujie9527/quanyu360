"""WP-CLI automation tool via SSH."""
from __future__ import annotations

import io
from typing import Any

import httpx
from pydantic import BaseModel
from pydantic import Field

from tools.runtime.base import BaseTool
from tools.runtime.base import ToolActionDefinition
from tools.runtime.base import ToolExecutionContext
from tools.runtime.base import ToolExecutionResult
from tools.runtime.base import ToolParameterDefinition

try:
    import paramiko
except Exception:  # pragma: no cover
    paramiko = None


class _RemoteParams(BaseModel):
    host: str
    port: int = 22
    ssh_user: str
    ssh_password: str | None = None
    ssh_private_key: str | None = None
    timeout: int = 60


class WpCliTool(BaseTool):
    name = "wpcli"
    description = "Install and bootstrap WordPress via SSH + WP-CLI."

    @property
    def actions(self) -> dict[str, ToolActionDefinition]:
        remote = [
            ToolParameterDefinition(name="host", type="string", description="SSH host"),
            ToolParameterDefinition(name="port", type="integer", required=False, description="SSH port"),
            ToolParameterDefinition(name="ssh_user", type="string", description="SSH user"),
            ToolParameterDefinition(name="ssh_password", type="string", required=False, description="SSH password"),
            ToolParameterDefinition(name="ssh_private_key", type="string", required=False, description="SSH private key PEM"),
            ToolParameterDefinition(name="timeout", type="integer", required=False, description="Timeout in seconds"),
        ]
        return {
            "create_db": ToolActionDefinition(
                name="create_db",
                description="Create MySQL database for WordPress site.",
                parameters=remote
                + [
                    ToolParameterDefinition(name="mysql_admin_user", type="string", description="MySQL admin user"),
                    ToolParameterDefinition(name="mysql_admin_password", type="string", description="MySQL admin password"),
                    ToolParameterDefinition(name="db_name", type="string", description="Database name"),
                ],
            ),
            "download_core": ToolActionDefinition(
                name="download_core",
                description="Run wp core download --path.",
                parameters=remote
                + [
                    ToolParameterDefinition(name="wp_cli_bin", type="string", required=False, description="wp cli binary"),
                    ToolParameterDefinition(name="path", type="string", description="Target WordPress directory"),
                ],
            ),
            "create_config": ToolActionDefinition(
                name="create_config",
                description="Run wp config create command.",
                parameters=remote
                + [
                    ToolParameterDefinition(name="wp_cli_bin", type="string", required=False, description="wp cli binary"),
                    ToolParameterDefinition(name="path", type="string", description="WordPress directory"),
                    ToolParameterDefinition(name="db_name", type="string", description="Database name"),
                    ToolParameterDefinition(name="db_user", type="string", description="Database user"),
                    ToolParameterDefinition(name="db_password", type="string", description="Database password"),
                    ToolParameterDefinition(name="db_host", type="string", required=False, description="Database host"),
                ],
            ),
            "core_install": ToolActionDefinition(
                name="core_install",
                description="Run wp core install command.",
                parameters=remote
                + [
                    ToolParameterDefinition(name="wp_cli_bin", type="string", required=False, description="wp cli binary"),
                    ToolParameterDefinition(name="path", type="string", description="WordPress directory"),
                    ToolParameterDefinition(name="url", type="string", description="Site url"),
                    ToolParameterDefinition(name="title", type="string", description="Site title"),
                    ToolParameterDefinition(name="admin_user", type="string", description="Admin username"),
                    ToolParameterDefinition(name="admin_password", type="string", description="Admin password"),
                    ToolParameterDefinition(name="admin_email", type="string", description="Admin email"),
                ],
            ),
            "create_app_password": ToolActionDefinition(
                name="create_app_password",
                description="Create WordPress application password for admin user.",
                parameters=remote
                + [
                    ToolParameterDefinition(name="wp_cli_bin", type="string", required=False, description="wp cli binary"),
                    ToolParameterDefinition(name="path", type="string", description="WordPress directory"),
                    ToolParameterDefinition(name="wp_user", type="string", required=False, description="WP username"),
                    ToolParameterDefinition(name="app_name", type="string", required=False, description="Application password label"),
                ],
            ),
            "update_site_credentials": ToolActionDefinition(
                name="update_site_credentials",
                description="Callback project-service and update WordPressSite credentials.",
                parameters=[
                    ToolParameterDefinition(name="project_service_url", type="string", description="Project service base URL"),
                    ToolParameterDefinition(name="site_id", type="string", description="WordPressSite ID"),
                    ToolParameterDefinition(name="username", type="string", description="WP username"),
                    ToolParameterDefinition(name="app_password", type="string", description="WP application password"),
                    ToolParameterDefinition(name="internal_api_key", type="string", required=False, description="X-Internal-Key header value"),
                ],
            ),
        }

    def execute(self, action: str, parameters: dict[str, Any], context: ToolExecutionContext) -> ToolExecutionResult:
        if action == "update_site_credentials":
            return self._update_site_credentials(parameters)
        if paramiko is None:
            return ToolExecutionResult(tool_name=self.name, action=action, success=False, error_message="paramiko is not installed.")

        try:
            if action == "create_db":
                db_name = parameters["db_name"].replace("`", "")
                cmd = (
                    f"MYSQL_PWD='{parameters['mysql_admin_password']}' "
                    f"mysql -u{parameters['mysql_admin_user']} "
                    f"-e \"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;\""
                )
            elif action == "download_core":
                wp = parameters.get("wp_cli_bin", "wp")
                cmd = f"{wp} core download --path='{parameters['path']}' --allow-root"
            elif action == "create_config":
                wp = parameters.get("wp_cli_bin", "wp")
                db_host = parameters.get("db_host", "localhost")
                cmd = (
                    f"{wp} config create --path='{parameters['path']}' --allow-root "
                    f"--dbname='{parameters['db_name']}' --dbuser='{parameters['db_user']}' "
                    f"--dbpass='{parameters['db_password']}' --dbhost='{db_host}' --skip-check"
                )
            elif action == "core_install":
                wp = parameters.get("wp_cli_bin", "wp")
                cmd = (
                    f"{wp} core install --path='{parameters['path']}' --allow-root "
                    f"--url='{parameters['url']}' --title='{parameters['title']}' "
                    f"--admin_user='{parameters['admin_user']}' --admin_password='{parameters['admin_password']}' "
                    f"--admin_email='{parameters['admin_email']}'"
                )
            elif action == "create_app_password":
                wp = parameters.get("wp_cli_bin", "wp")
                wp_user = parameters.get("wp_user", "admin")
                app_name = parameters.get("app_name", "AIWorker")
                cmd = f"{wp} user application-password create {wp_user} '{app_name}' --porcelain --path='{parameters['path']}' --allow-root"
            else:
                return ToolExecutionResult(tool_name=self.name, action=action, success=False, error_message=f"Unsupported action: {action}")

            output = self._run_ssh(command=cmd, parameters=parameters)
            success = output["exit_code"] == 0
            if action == "create_app_password" and success:
                output["app_password"] = output["stdout"].strip()
            return ToolExecutionResult(
                tool_name=self.name,
                action=action,
                success=success,
                output=output,
                error_message=None if success else (output["stderr"] or "remote command failed"),
            )
        except Exception as exc:
            return ToolExecutionResult(tool_name=self.name, action=action, success=False, error_message=str(exc))

    def _run_ssh(self, command: str, parameters: dict[str, Any]) -> dict[str, Any]:
        remote = _RemoteParams.model_validate(parameters)
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            kwargs: dict[str, Any] = {
                "hostname": remote.host,
                "port": remote.port,
                "username": remote.ssh_user,
                "timeout": remote.timeout,
            }
            if remote.ssh_private_key:
                kwargs["pkey"] = paramiko.pkey.PKey.from_private_key(io.StringIO(remote.ssh_private_key))
            else:
                kwargs["password"] = remote.ssh_password
            client.connect(**kwargs)
            _stdin, stdout, stderr = client.exec_command(command, timeout=remote.timeout)
            exit_code = stdout.channel.recv_exit_status()
            return {
                "stdout": stdout.read().decode("utf-8", errors="ignore"),
                "stderr": stderr.read().decode("utf-8", errors="ignore"),
                "exit_code": exit_code,
                "command": command,
            }
        finally:
            client.close()

    def _update_site_credentials(self, parameters: dict[str, Any]) -> ToolExecutionResult:
        import os
        base = str(parameters["project_service_url"]).rstrip("/")
        site_id = str(parameters["site_id"])
        payload = {
            "username": parameters["username"],
            "app_password": parameters["app_password"],
            "status": "active",
        }
        headers: dict[str, str] = {}
        internal_key = parameters.get("internal_api_key") or os.environ.get("INTERNAL_API_KEY")
        if internal_key:
            headers["X-Internal-Key"] = internal_key
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.patch(f"{base}/sites/{site_id}/credentials", json=payload, headers=headers)
                if resp.status_code >= 400:
                    return ToolExecutionResult(
                        tool_name=self.name,
                        action="update_site_credentials",
                        success=False,
                        output={"status_code": resp.status_code, "response_text": resp.text[:500]},
                        error_message=f"Project service error: {resp.status_code}",
                    )
            return ToolExecutionResult(
                tool_name=self.name,
                action="update_site_credentials",
                success=True,
                output={"site_id": site_id, "status": "active"},
            )
        except Exception as exc:
            return ToolExecutionResult(
                tool_name=self.name,
                action="update_site_credentials",
                success=False,
                error_message=str(exc),
            )
