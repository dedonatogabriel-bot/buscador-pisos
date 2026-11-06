# buscador-pisos

Buscador de alquileres en CABA para Marcos: captura, valora y avisa.

- Reglas de trabajo y stack: [`CLAUDE.md`](CLAUDE.md)
- Especificación: [`docs/SPEC.md`](docs/SPEC.md)
- Decisiones: [`docs/DECISIONES.md`](docs/DECISIONES.md)
- Tareas: Issues del repo (fuente: [`tasks/tasks.yaml`](tasks/tasks.yaml))

## Arranque

```
uv sync
cp .env.example .env      # completar valores
uv run pre-commit install
uv run pytest
```
