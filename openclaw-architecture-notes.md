# OpenClaw Architecture Notes

Started: 2026-02-15 (Free Will Mode)
Goal: Understand the core architecture of OpenClaw (Agent, Session, Sandbox).

## Table of Contents
1. [Agent Execution Flow](##agent-execution-flow)
2. [Tool Management](##tool-management)
3. [Sandbox Architecture](##sandbox-architecture)
4. [Session Management](##session-management)
5. [Key Insights](##key-insights)

## 1. Agent Execution Flow

The core execution logic resides in `src/agents/pi-embedded-runner/`.

*   **Entry Point**: `runEmbeddedPiAgent` (`src/agents/pi-embedded-runner/run.ts`)
    *   Handles high-level orchestration: resolving lanes, workspace, models, and auth profiles.
    *   Manages the "Attempt Loop" (retrying with different auth profiles or after context overflow).
    *   Delegates the actual run to `runEmbeddedAttempt`.

*   **Attempt Logic**: `runEmbeddedAttempt` (`src/agents/pi-embedded-runner/run/attempt.ts`)
    *   **Environment Setup**: Resolves workspace, sandbox context, and skills.
    *   **Tool Creation**: Calls `createOpenClawCodingTools` to register all available tools.
    *   **System Prompt**: Builds the prompt using `buildEmbeddedSystemPrompt`, injecting runtime info, skills, and documentation.
    *   **Session Initialization**: Opens the session using `SessionManager`.
    *   **Agent Creation**: Instantiates the agent using `createAgentSession` (from `@mariozechner/pi-coding-agent`).
    *   **Execution**: Calls `activeSession.prompt()` to start the LLM interaction.
    *   **Subscription**: Uses `subscribeEmbeddedPiSession` to handle real-time events (streaming, tool calls, results).

## 2. Tool Management

Tools are centrally registered in `src/agents/pi-tools.ts`.

*   **Registry**: `createOpenClawCodingTools`
    *   Aggregates tools from multiple sources.
    *   Applies security policies (owner-only, allowlists).
    *   Wraps tools for sandbox/workspace protection (e.g., preventing access outside the workspace).

*   **Tool Categories**:
    *   **Base Tools**: `read`, `write`, `edit` (from `@mariozechner/pi-coding-agent`).
    *   **Bash Tools**: `exec`, `process` (`src/agents/bash-tools.ts`) - handles command execution, potentially inside a Docker container.
    *   **OpenClaw Tools**: `browser`, `canvas`, `nodes`, `cron`, `message`, `gateway`, etc. (`src/agents/openclaw-tools.ts`).
    *   **Plugin Tools**: Dynamically loaded from plugins.

## 3. Sandbox Architecture

Sandbox logic is managed by `src/agents/sandbox/`.

*   **Context Resolution**: `resolveSandboxContext` (`src/agents/sandbox/context.ts`)
    *   Determines if a session should be sandboxed.
    *   Ensures the Docker container is running (`ensureSandboxContainer`).
    *   Ensures the browser container is running (`ensureSandboxBrowser`).
    *   Creates a filesystem bridge (`createSandboxFsBridge`) to allow the agent to interact with files inside the container seamlessly.

*   **Isolation**:
    *   Tools like `exec` and `fs` are wrapped to operate within the container when the sandbox is enabled.
    *   The workspace directory is mounted into the container.

## 4. Session Management

*   **SessionManager**: Handles the persistence and retrieval of conversation history.
*   **State**: Tracks messages, tool outputs, and variables.
*   **Compaction**: `runEmbeddedPiAgent` handles context overflow by compacting the session (summarizing or truncating old messages).

## 5. Key Insights

*   **Modular Design**: The separation between the runner, tools, and sandbox is clean. Adding new tools or changing the execution logic is straightforward.
*   **Safety First**: Sandbox and tool wrappers heavily enforce boundaries (workspace root, container isolation).
*   **Resilience**: The architecture includes robust handling for context overflows (compaction), auth failures (profile rotation), and tool errors.
*   **Embedded Nature**: The agent is designed to be "embedded," meaning it runs within the OpenClaw runtime and shares resources/config, rather than being a completely standalone process.
