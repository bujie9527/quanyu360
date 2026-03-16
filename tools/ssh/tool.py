"""SSH command execution tool."""
from __future__ import annotations

from pydantic import BaseModel
from pydantic import Field

from tools.runtime.base import StructuredTool
from tools.runtime.base import ToolActionDefinition
from tools.runtime.base import ToolExecutionContext
from tools.runtime.base import ToolExecutionResult
from tools.runtime.base import ToolParameterDefinition

try:
    import paramiko
except Exception:  # pragma: no cover
    paramiko = None


class SshExecParams(BaseModel):
    host: str = Field(min_length=1)
    port: int = Field(default=22, ge=1, le=65535)
    username: str = Field(min_length=1)
    password: str | None = None
    private_key: str | None = None
    command: str = Field(min_length=1)
    timeout: int = Field(default=30, ge=1, le=600)


class SshCommandTool(StructuredTool):
    name = "ssh_command"
    description = "Execute a shell command on remote host via SSH."
    action_models = {"exec": SshExecParams}

    @property
    def actions(self) -> dict[str, ToolActionDefinition]:
        return {
            "exec": ToolActionDefinition(
                name="exec",
                description="Execute remote command and return stdout/stderr/exit_code.",
                parameters=[
                    ToolParameterDefinition(name="host", type="string", description="SSH host"),
                    ToolParameterDefinition(name="port", type="integer", required=False, description="SSH port"),
                    ToolParameterDefinition(name="username", type="string", description="SSH user"),
                    ToolParameterDefinition(name="password", type="string", required=False, description="SSH password"),
                    ToolParameterDefinition(name="private_key", type="string", required=False, description="PEM private key content"),
                    ToolParameterDefinition(name="command", type="string", description="Command to execute"),
                    ToolParameterDefinition(name="timeout", type="integer", required=False, description="Command timeout seconds"),
                ],
            )
        }

    def handle(self, action: str, payload: SshExecParams, context: ToolExecutionContext) -> ToolExecutionResult:
        if paramiko is None:
            return ToolExecutionResult(
                tool_name=self.name,
                action=action,
                success=False,
                error_message="paramiko is not installed.",
            )

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            kwargs: dict = {
                "hostname": payload.host,
                "port": payload.port,
                "username": payload.username,
                "timeout": payload.timeout,
            }
            if payload.private_key:
                import io as _io
                kwargs["pkey"] = paramiko.pkey.PKey.from_private_key(_io.StringIO(payload.private_key))
            else:
                kwargs["password"] = payload.password
            client.connect(**kwargs)
            stdin, stdout, stderr = client.exec_command(payload.command, timeout=payload.timeout)
            exit_code = stdout.channel.recv_exit_status()
            out = stdout.read().decode("utf-8", errors="ignore")
            err = stderr.read().decode("utf-8", errors="ignore")
            return ToolExecutionResult(
                tool_name=self.name,
                action=action,
                success=exit_code == 0,
                output={"stdout": out, "stderr": err, "exit_code": exit_code},
                error_message=None if exit_code == 0 else (err or f"Command exited with {exit_code}"),
            )
        except Exception as exc:
            return ToolExecutionResult(
                tool_name=self.name,
                action=action,
                success=False,
                error_message=str(exc),
            )
        finally:
            client.close()
