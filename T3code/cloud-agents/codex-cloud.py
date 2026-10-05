#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["websockets>=15,<17"]
# ///
"""Terminal adapter for current Codex Cloud's authenticated app-server transport.

Uses the existing Codex ChatGPT login. No browser, browser cookies, API key,
legacy cloud-task endpoint, or local worker process is involved.
"""
import argparse
import asyncio
import json
import os
from pathlib import Path
import sys
import time
import uuid

import websockets

ENDPOINT = "wss://codex-cloud-backend.chatgpt.com/"
STATE = Path(os.environ.get("CLOUD_STATE_DIR", str(Path.home() / ".codex/cloud-agents")))


class CloudError(Exception):
    pass


def private_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    # Create with private permissions, including while being written.
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "w") as f:
        json.dump(value, f, indent=2)
    path.chmod(0o600)


def registry():
    path = STATE / "environments.json"
    return json.loads(path.read_text()) if path.exists() else {}


def environment(name):
    data = registry()
    if name in data:
        return data[name]
    if "~asenvcfg_" in name:
        return {"id": name}
    raise CloudError(f"Unregistered current environment: {name}. Use environments add with its published config ID.")


def credentials():
    path = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "auth.json"
    try:
        tokens = json.loads(path.read_text())["tokens"]
        return tokens["access_token"], tokens["account_id"]
    except (OSError, KeyError, TypeError, ValueError):
        raise CloudError("A file-backed ChatGPT Codex login is required. Run codex login; credentials are read in memory.") from None


class Client:
    def __init__(self):
        self.next_id = 0
        self.events = []

    async def __aenter__(self):
        token, account = credentials()
        try:
            self.ws = await websockets.connect(
                ENDPOINT, subprotocols=["codex-app-server", "codex-client.browser", "openai-bearer." + token],
                additional_headers={"ChatGPT-Account-Id": account}, origin="https://chatgpt.com", open_timeout=20,
                max_size=32 * 1024 * 1024,
            )
        except Exception:
            # Exception representations from transports can contain request headers.
            raise CloudError("Cloud connection failed. Check network and codex login status; no request was submitted.") from None
        try:
            await self.rpc("initialize", {
                "clientInfo": {"name": "cloud-agents-cli", "title": "Cloud Agents CLI", "version": "0.1.0"},
                "capabilities": {"experimentalApi": True, "requestAttestation": False,
                                 "optOutNotificationMethods": ["rawResponseItem/completed"]},
            })
            await self.ws.send(json.dumps({"method": "initialized"}))
        except BaseException:
            await self.ws.close()
            raise
        return self

    async def __aexit__(self, *_):
        await self.ws.close()

    async def rpc(self, method, params, timeout=120):
        self.next_id += 1
        request_id = self.next_id
        await self.ws.send(json.dumps({"id": request_id, "method": method, "params": params}))
        try:
            async with asyncio.timeout(timeout):
                while True:
                    msg = json.loads(await self.ws.recv())
                    if msg.get("id") == request_id and "method" not in msg:
                        if "error" in msg:
                            raise CloudError(f"{method}: {msg['error'].get('message', 'request rejected')}")
                        return msg.get("result", {})
                    self.events.append(msg)
        except (TimeoutError, websockets.ConnectionClosed):
            raise CloudError(f"{method}: response lost or timed out; outcome may be unknown. Inspect task status/history and any saved submission before retrying.") from None

    async def read(self, thread):
        return (await self.rpc("thread/read", {"threadId": thread, "includeTurns": False}))["thread"]

    async def page(self, method, params, all_pages=False):
        data = []
        while True:
            result = await self.rpc(method, params)
            data.extend(result.get("data", []))
            cursor = result.get("nextCursor")
            if not all_pages or cursor is None:
                return {**result, "data": data}
            params = {**params, "cursor": cursor}


def task_url(thread):
    return f"https://chatgpt.com/local/{thread}?hostId=local"


def brief(path):
    text = Path(path).read_text()
    if not text.strip():
        raise CloudError("The brief is empty.")
    return text


async def validate_model(client, model, effort):
    models = (await client.page("model/list", {"includeHidden": True, "limit": 100}, True))["data"]
    selected = next((m for m in models if model in (m.get("id"), m.get("model"))), None)
    if selected is None:
        raise CloudError(f"Model {model} is unavailable in current Codex Cloud. Choose an explicit replacement.")
    allowed = [e["reasoningEffort"] for e in selected.get("supportedReasoningEfforts", [])]
    if effort not in allowed:
        raise CloudError(f"Effort {effort} is unavailable for {model}; supported: {', '.join(allowed)}.")


async def dispatch(client, args):
    config = environment(args.env)
    text = brief(args.brief)
    if args.branch and args.branch != config.get("branch"):
        raise CloudError("This adapter uses the published repository refs. The requested base differs from the registered published branch; update/publish the environment first.")
    if args.repo and args.repo != config.get("repo"):
        raise CloudError("The environment's registered repository does not match the checkout.")
    await validate_model(client, args.model, args.effort)
    # Persist intent before sending. Never automatically retry a mutating RPC.
    submission = STATE / "submissions" / f"{int(time.time())}-{uuid.uuid4().hex}.json"
    record = {"environment": config["id"], "model": args.model, "effort": args.effort,
              "brief": str(Path(args.brief).resolve()), "branch": config.get("branch"), "repo": config.get("repo"),
              "phase": "starting", "createdAt": int(time.time())}
    private_json(submission, record)
    print(f"Submission record: {submission}", file=sys.stderr, flush=True)
    start = await client.rpc("thread/start", {
        "model": args.model, "config": {"model_reasoning_effort": args.effort},
        "environments": [{"environmentConfigId": config["id"]}], "deferredEnvironment": True,
        "pluginsMcp": {"productSku": "codex"},
    })
    thread = start["thread"]
    record.update(threadId=thread["id"], url=task_url(thread["id"]), phase="created")
    private_json(submission, record)
    print(f"Created {thread['id']} {record['url']}", file=sys.stderr, flush=True)
    ids = [e.get("environmentConfigId") for e in thread.get("environments", [])]
    if config["id"] not in ids or start.get("model") != args.model or start.get("reasoningEffort") != args.effort:
        raise CloudError("Created thread settings did not match. Its ID is saved; no task brief was sent.")
    record["phase"] = "submitting"
    private_json(submission, record)
    result = await client.rpc("turn/start", {"threadId": thread["id"], "input": [
        {"type": "text", "text": text, "text_elements": []}], "model": args.model, "effort": args.effort})
    record.update(phase="admitted", turnId=result["turn"]["id"], status=result["turn"]["status"])
    private_json(submission, record)
    return {**record, "submissionRecord": str(submission)}


async def status(client, thread):
    metadata = await client.read(thread)
    turns = await client.page("thread/turns/list", {"threadId": thread, "limit": 1, "sortDirection": "desc"})
    return {"thread": metadata, "latestTurn": next(iter(turns["data"]), None), "url": task_url(thread)}


async def run(args):
    if args.command == "environments":
        data = registry()
        if args.action == "add":
            if "~asenvcfg_" not in args.config_id:
                raise CloudError("Use a current published ~asenvcfg_ config ID.")
            data[args.name] = {"id": args.config_id, "repo": args.repo, "branch": args.branch}
            private_json(STATE / "environments.json", data)
        return {"registeredEnvironments": data, "source": "local registry; dispatch verifies the cloud config"}
    async with Client() as client:
        if args.command == "models":
            return await client.page("model/list", {"includeHidden": True, "limit": 100}, True)
        if args.command == "exec":
            return await dispatch(client, args)
        if args.command == "list":
            result = await client.page("thread/list", {"limit": 100, "sourceKinds": [], "sortKey": "updated_at"}, True)
            result["data"] = [t for t in result["data"] if any(e.get("environmentConfigId") for e in t.get("environments", []))]
            if args.env:
                config = environment(args.env)["id"]
                result["data"] = [t for t in result["data"] if any(e.get("environmentConfigId") == config for e in t.get("environments", []))]
            return result
        if args.command == "status":
            return await status(client, args.thread)
        if args.command == "diff":
            thread = await client.read(args.thread)
            environments = thread.get("environments", [])
            if len(environments) != 1 or args.base.startswith("-"):
                raise CloudError("Choose a single environment and a valid diff base.")
            result = await client.rpc("command/exec", {"environmentId": environments[0]["environmentId"],
                "command": ["git", "diff", "--binary", args.base, "--"], "cwd": args.cwd, "timeoutMs": 30000})
            if result.get("exitCode") != 0:
                raise CloudError(f"git diff failed: {result.get('stderr', '')}")
            return result.get("stdout", "")
        if args.command in ("turns", "items"):
            params = {"threadId": args.thread, "limit": 100, "sortDirection": args.order}
            if args.command == "items" and args.turn:
                params["turnId"] = args.turn
            return await client.page(f"thread/{args.command}/list", params, args.all)
        if args.command == "followup":
            current = await status(client, args.thread)
            last = current["latestTurn"]
            if last and last["status"] == "inProgress":
                raise CloudError("Task is running. Inspect it before steering or queuing through rpc; followup starts an idle turn.")
            thread = current["thread"]
            model = args.model or thread.get("model")
            effort = args.effort or thread.get("reasoningEffort")
            if not model or not effort:
                raise CloudError("Recorded task settings are missing; provide --model and --effort.")
            await validate_model(client, model, effort)
            await client.rpc("thread/resume", {"threadId": args.thread, "excludeTurns": True})
            return await client.rpc("turn/start", {"threadId": args.thread, "input": [
                {"type": "text", "text": brief(args.brief), "text_elements": []}], "model": model, "effort": effort})
        if args.command == "stop":
            current = await status(client, args.thread)
            turn = current["latestTurn"]
            if not turn or turn["status"] != "inProgress":
                return {"status": "already stopped", "threadId": args.thread}
            await client.rpc("thread/resume", {"threadId": args.thread, "excludeTurns": True})
            return await client.rpc("turn/interrupt", {"threadId": args.thread, "turnId": turn["id"]})
        if args.command == "archive":
            return await client.rpc("thread/archive", {"threadId": args.thread})
        if args.command == "rpc":
            return await client.rpc(args.method, json.loads(Path(args.params).read_text()))
        if args.command == "watch":
            await client.rpc("thread/resume", {"threadId": args.thread, "excludeTurns": True})
            deadline = time.monotonic() + args.seconds
            def relevant(msg):
                return not msg.get("method", "").startswith("rawResponseItem/") and msg.get("params", {}).get("threadId", args.thread) == args.thread
            for msg in client.events:
                if relevant(msg): print(json.dumps(msg), flush=True)
            while time.monotonic() < deadline:
                try:
                    msg = json.loads(await asyncio.wait_for(client.ws.recv(), deadline - time.monotonic()))
                except TimeoutError:
                    break
                if relevant(msg): print(json.dumps(msg), flush=True)
            return {"status": "detached", "threadId": args.thread}


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("models")
    e = sub.add_parser("environments")
    es = e.add_subparsers(dest="action", required=True)
    es.add_parser("list")
    add = es.add_parser("add")
    add.add_argument("name"); add.add_argument("config_id")
    add.add_argument("--repo", required=True); add.add_argument("--branch", required=True)
    ex = sub.add_parser("exec")
    ex.add_argument("--env", required=True); ex.add_argument("--brief", required=True)
    ex.add_argument("--model", required=True); ex.add_argument("--effort", required=True)
    ex.add_argument("--branch"); ex.add_argument("--repo")
    li = sub.add_parser("list"); li.add_argument("--env")
    diff = sub.add_parser("diff"); diff.add_argument("thread")
    diff.add_argument("--cwd", required=True); diff.add_argument("--base", default="origin/main")
    for name in ["status", "turns", "items", "followup", "stop", "archive", "watch"]:
        cmd = sub.add_parser(name); cmd.add_argument("thread")
        if name in ("turns", "items"):
            cmd.add_argument("--all", action="store_true"); cmd.add_argument("--order", choices=["asc", "desc"], default="asc")
        if name == "items": cmd.add_argument("--turn")
        if name == "followup":
            cmd.add_argument("--brief", required=True); cmd.add_argument("--model"); cmd.add_argument("--effort")
        if name == "watch": cmd.add_argument("--seconds", type=int, default=30)
    rpc = sub.add_parser("rpc"); rpc.add_argument("method"); rpc.add_argument("--params", required=True)
    return p


if __name__ == "__main__":
    try:
        result = asyncio.run(run(parser().parse_args()))
        if isinstance(result, str): print(result, end="")
        else: print(json.dumps(result, indent=2))
    except (CloudError, OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    except Exception:
        print("Cloud transport failed; credentials are omitted. For a mutating request, inspect its submission record before retrying.", file=sys.stderr)
        sys.exit(1)
