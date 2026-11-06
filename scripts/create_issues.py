"""Crea etiquetas, milestones e issues de GitHub desde tasks/tasks.yaml.

Uso:
    python scripts/create_issues.py --repo OWNER/REPO --dry-run
    python scripts/create_issues.py --repo OWNER/REPO

Idempotente: si ya existe un issue cuyo título empieza con "[ID]", lo reutiliza.
Requiere `gh` autenticado.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TASKS_FILE = ROOT / "tasks" / "tasks.yaml"

LABELS = {
    "tipo:claude": ("1f6feb", "La hace Claude Code"),
    "tipo:gabi": ("d93f0b", "Trabajo humano de Gabi"),
    "tipo:marcos": ("fbca04", "Necesita respuesta de Marcos"),
    "prioridad:alta": ("b60205", ""),
    "prioridad:media": ("e99695", ""),
    "prioridad:baja": ("f9d0c4", ""),
    "fuente-rota": ("000000", "Abierta por el chequeo de salud"),
}
for phase in range(5):
    LABELS[f"fase:{phase}"] = ("c5def5", f"Fase {phase}")
AREAS = ["decision", "infra", "datos", "scraping", "ia", "bot", "web", "agentes", "ops"]
for area in AREAS:
    LABELS[f"area:{area}"] = ("bfdadc", "")

TYPE_TEXT = {"claude": "Claude Code", "gabi": "Gabi", "marcos": "Marcos (vía Gabi)"}


def load() -> dict:
    data = yaml.safe_load(TASKS_FILE.read_text(encoding="utf-8"))
    validate(data)
    return data


def validate(data: dict) -> None:
    tasks = data["tasks"]
    ids = [t["id"] for t in tasks]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        sys.exit(f"IDs duplicados: {sorted(dupes)}")
    known = set(ids)
    for t in tasks:
        for dep in t.get("depends", []):
            if dep not in known:
                sys.exit(f"{t['id']} depende de {dep}, que no existe")
        for field in ("type", "phase", "area", "priority", "title", "scope", "acceptance"):
            if field not in t:
                sys.exit(f"{t['id']} no tiene '{field}'")
        if t["area"] not in AREAS:
            sys.exit(f"{t['id']} tiene área desconocida: {t['area']}")
    # Ciclos
    graph = {t["id"]: t.get("depends", []) for t in tasks}
    state: dict[str, int] = {}

    def visit(node: str, path: list[str]) -> None:
        if state.get(node) == 1:
            sys.exit(f"Ciclo de dependencias: {' -> '.join([*path, node])}")
        if state.get(node) == 2:
            return
        state[node] = 1
        for dep in graph[node]:
            visit(dep, [*path, node])
        state[node] = 2

    for node in graph:
        visit(node, [])


def gh(args: list[str], payload: dict | None = None) -> dict | list | None:
    cmd = ["gh", "api", *args]
    if payload is not None:
        cmd += ["--input", "-"]
    result = subprocess.run(
        cmd,
        input=json.dumps(payload) if payload is not None else None,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"gh api {' '.join(args)} falló: {result.stderr.strip()}")
    return json.loads(result.stdout) if result.stdout.strip() else None


def body_for(task: dict, numbers: dict[str, int], blocks: dict[str, list[str]]) -> str:
    def ref(task_id: str) -> str:
        return f"#{numbers[task_id]} ({task_id})" if task_id in numbers else task_id

    lines = [
        f"**ID:** {task['id']} · **Tipo:** {TYPE_TEXT[task['type']]} · "
        f"**Fase:** {task['phase']} · **Prioridad:** {task['priority']}",
        "",
        "## Alcance",
        task["scope"].strip(),
    ]
    if task.get("out"):
        lines += ["", "## Fuera de alcance", task["out"].strip()]
    lines += ["", "## Criterios de aceptación"]
    lines += [f"- [ ] {item}" for item in task["acceptance"]]
    if task.get("files"):
        lines += ["", "## Archivos", ", ".join(f"`{f}`" for f in task["files"])]
    deps = task.get("depends", [])
    lines += ["", "## Dependencias"]
    lines.append("Bloqueada por: " + (", ".join(ref(d) for d in deps) if deps else "ninguna"))
    lines.append("Bloquea: " + (", ".join(ref(b) for b in blocks[task["id"]]) or "ninguna"))
    lines += ["", "Especificación: `docs/SPEC.md` · Reglas: `CLAUDE.md`"]
    return "\n".join(lines)


def labels_for(task: dict) -> list[str]:
    return [
        f"tipo:{task['type']}",
        f"fase:{task['phase']}",
        f"area:{task['area']}",
        f"prioridad:{task['priority']}",
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    data = load()
    tasks = data["tasks"]
    blocks: dict[str, list[str]] = defaultdict(list)
    for t in tasks:
        for dep in t.get("depends", []):
            blocks[dep].append(t["id"])

    if args.dry_run:
        counts = defaultdict(int)
        for t in tasks:
            counts[t["type"]] += 1
        print(f"OK: {len(tasks)} tareas válidas, sin ciclos. Por tipo: {dict(counts)}")
        print(body_for(tasks[0], {}, blocks))
        return

    repo = args.repo

    # Etiquetas
    existing = {lbl["name"] for lbl in gh([f"repos/{repo}/labels", "--paginate"])}
    for name, (color, desc) in LABELS.items():
        if name not in existing:
            gh([f"repos/{repo}/labels", "-X", "POST"], {"name": name, "color": color, "description": desc})
    print("Etiquetas listas")

    # Milestones
    ms_numbers: dict[int, int] = {}
    current = gh([f"repos/{repo}/milestones?state=all&per_page=100"])
    by_title = {m["title"]: m["number"] for m in current}
    for ms in data["milestones"]:
        if ms["title"] in by_title:
            ms_numbers[ms["phase"]] = by_title[ms["title"]]
            continue
        created = gh(
            [f"repos/{repo}/milestones", "-X", "POST"],
            {"title": ms["title"], "due_on": f"{ms['due']}T23:59:59Z"},
        )
        ms_numbers[ms["phase"]] = created["number"]
    print("Milestones listos")

    # Issues existentes
    issues = gh([f"repos/{repo}/issues?state=all&per_page=100"]) or []
    numbers: dict[str, int] = {}
    ids: dict[str, int] = {}
    for issue in issues:
        title = issue["title"]
        if title.startswith("[") and "]" in title:
            numbers[title[1 : title.index("]")]] = issue["number"]
            ids[title[1 : title.index("]")]] = issue["id"]

    # Paso 1: crear los que faltan
    for t in tasks:
        if t["id"] in numbers:
            continue
        created = gh(
            [f"repos/{repo}/issues", "-X", "POST"],
            {
                "title": f"[{t['id']}] {t['title']}",
                "body": body_for(t, {}, blocks),
                "labels": labels_for(t),
                "milestone": ms_numbers[t["phase"]],
            },
        )
        numbers[t["id"]] = created["number"]
        ids[t["id"]] = created["id"]
        print(f"Creado #{created['number']} [{t['id']}]")

    # Paso 2: cuerpos con números reales y dependencias nativas
    for t in tasks:
        n = numbers[t["id"]]
        gh([f"repos/{repo}/issues/{n}", "-X", "PATCH"], {"body": body_for(t, numbers, blocks)})
        for dep in t.get("depends", []):
            try:
                gh(
                    [f"repos/{repo}/issues/{n}/dependencies/blocked_by", "-X", "POST"],
                    {"issue_id": ids[dep]},
                )
            except RuntimeError as err:
                if "already" not in str(err).lower():
                    print(f"Aviso: dependencia nativa {t['id']} <- {dep} no creada: {err}")
    print(f"Listo: {len(tasks)} issues con dependencias")


if __name__ == "__main__":
    main()
