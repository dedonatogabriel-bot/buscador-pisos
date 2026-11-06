---
name: siguiente-tarea
description: Toma la próxima issue de GitHub lista para Claude en este repo, la implementa en su rama, verifica el criterio de aceptación y abre el PR. Usar cuando Gabi pide "siguiente tarea", "seguí" o "/siguiente-tarea [ID]".
---

# Siguiente tarea

Un ciclo = una issue = una rama = un PR. Después parás.

## 1. Elegir

Si Gabi pasó un ID (por ejemplo `C-05`), usá esa issue. Si no:

```bash
gh issue list --label tipo:claude --state open --json number,title,labels,milestone --limit 100
```

Para cada candidata, leé su cuerpo (`gh issue view N`) y la línea "Bloqueada por".
Está lista si todas sus dependencias están cerradas (`gh issue view <dep> --json state`).
Elegí la lista con menor fase, después prioridad alta, después menor número.
Si ninguna está lista, decí qué issues humanas (`tipo:gabi`, `tipo:marcos`) bloquean y pará.

## 2. Entender

- Leé la issue completa, `CLAUDE.md` y las secciones de `docs/SPEC.md` que nombra.
- Leé los PRs mergeados de sus dependencias para conocer las interfaces reales.
- Si falta una decisión de negocio, comentá en la issue qué falta y pará. No inventes valores.
- Escribí un plan corto antes de tocar código.

## 3. Implementar

```bash
git checkout main && git pull
git checkout -b tarea/<id-en-minúsculas>-<slug>
```

- Respetá el alcance. Lo que quede fuera va como comentario en la issue o como issue nueva con `tipo:claude`.
- Tests primero cuando se pueda. Los adaptadores siempre con fixture HTML real.
- Nada de secretos en archivos versionados.

## 4. Verificar

- Corré `uv run ruff check .`, `uv run pytest` y lo que pida el criterio de aceptación.
- Si un criterio necesita la PC, una cuenta o datos reales que no tenés, dejalo marcado como pendiente para Gabi con el comando exacto que tiene que correr.

## 5. Entregar

```bash
gh pr create --title "[<ID>] <título>" --body-file -
```

El cuerpo del PR lleva:
- `Closes #N`
- Qué se hizo, en 3–6 líneas.
- Cada criterio de aceptación con su evidencia (salida de comando, consulta, captura) o "pendiente Gabi: <comando>".
- Decisiones tomadas y cosas fuera de alcance detectadas.

Después pará y avisale a Gabi el número de PR. No empieces otra issue hasta que Gabi lo pida.
