# Skills y agents instalados

Selección **curada** desde cinco repos comunitarios (todos MIT). No se
instalaron completos a propósito: Claude Code carga la descripción de cada
skill/agent en el system prompt de **cada** sesión, así que instalar todo
habría costado ~73 000 tokens por sesión — lo contrario del objetivo.

| Repo | Disponible | Instalado | Criterio |
|---|---:|---:|---|
| [obra/superpowers](https://github.com/obra/superpowers) | 15 skills | **15** | Proceso agnóstico al stack; todo aplica |
| [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | 13 skills | **5** | La app tiene paleta de marca y UI propia |
| [VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents) | 179 agents | **8** | Solo los del stack real (JS/PWA/a11y/Android) |
| [Rtur2003/Claude-Code-Promts-Skills](https://github.com/Rtur2003/Claude-Code-Promts-Skills) | 12 skills | **6** | Meta-skills de auditoría y changelog |
| [affaan-m/ECC](https://github.com/affaan-m/ECC) | 903 skills | **1** | Solo `accessibility` (WCAG 2.2 AA) |
| | **1 122** | **35** | **~2 250 tokens/sesión (−97%)** |

## Qué quedó instalado

### Skills de proceso (superpowers, 15)
`brainstorming` · `writing-plans` · `executing-plans` · `test-driven-development` ·
`systematic-debugging` · `verification-before-completion` · `requesting-code-review` ·
`receiving-code-review` · `subagent-driven-development` · `dispatching-parallel-agents` ·
`using-git-worktrees` · `finishing-a-development-branch` · `writing-skills` ·
`using-superpowers` · `diagnosing-superpowers`

Los de mayor valor aquí: **`systematic-debugging`** (los builds de CI fallaron
3 veces seguidas por causas distintas) y **`verification-before-completion`**
(evita declarar terminado algo sin correr la verificación).

### Diseño y accesibilidad (6)
`uiux-pro-max` · `uiux-design` · `uiux-design-system` · `uiux-ui-styling` ·
`uiux-brand` · `accessibility` (WCAG 2.2 AA, de ECC)

### Auditoría y mantención (6)
`doc-link-audit` · `changelog-from-commits` · `deterministic-checks` ·
`skill-audit` · `capability-audit` · `find-prompt`

### Subagents (8)
`code-reviewer` · `javascript-pro` · `frontend-developer` · `accessibility-tester` ·
`mobile-developer` · `debugger` · `technical-writer` · `qa-expert`

## Qué se descartó y por qué

- **ECC completo (902 de 903 skills)**: el grueso es sobre agentes autónomos,
  cripto/trading, infra cloud y toolchains que este proyecto no usa. Costaba
  ~60 200 tokens por sesión.
- **Skills de healthcare de ECC** (`healthcare-cdss-patterns`,
  `healthcare-eval-harness`, `healthcare-emr-patterns`, `healthcare-phi-compliance`):
  parecían el hallazgo obvio para una app médica, pero son para **sistemas
  clínicos con datos de pacientes reales** — validación de dosis, scores tipo
  NEWS2/qSOFA, integración EMR, cumplimiento PHI. InternOS es una app de
  **estudio**: no maneja PHI, no prescribe, no se integra a ningún EMR. No aplican.
- **171 de 179 subagents**: Rust, Go, Java, Kubernetes, GraphQL, microservicios,
  PowerShell, Angular… nada de eso está en este stack.
- **`content-engine` (ECC)**: es para contenido de redes sociales, no para
  redacción médica.
- **`banner-design` y `slides` (ui-ux)**: la app no genera banners ni
  presentaciones.
- **Todos los hooks**. ECC trae ~40 hooks que se ejecutan en cada tool call
  (`before-shell-execution`, `before-submit-prompt`, etc.): latencia en cada
  operación y ejecución automática de código de terceros. El hook `SessionStart`
  de superpowers tampoco se instaló — las descripciones de los skills ya bastan
  para que se inviten solas.
- **Catálogos de Google Fonts y Phosphor Icons** (~2 MB) del skill `uiux-pro-max`:
  InternOS es offline-first y no puede cargar fuentes ni íconos desde CDN (usa
  SVG inline en `src/ui/iconos.js` y fuentes del sistema).

## Verificación hecha antes de instalar

- Licencias: los cinco repos son MIT → redistribución permitida con atribución.
- Escaneo de exfiltración (credenciales hacia curl/wget, `eval(fetch(...))`,
  `base64 -d | sh`): sin coincidencias.
- Dominios salientes en scripts: github.com, fuentes/íconos públicos y
  placeholders `example.com`. Nada sospechoso.
- Frontmatter de los 35 archivos instalados: 35/35 válidos (`name` + `description`).

## Cómo actualizar

Estos archivos son una copia puntual, no un submódulo. Para traer cambios
upstream hay que volver a clonar el repo de origen y copiar el skill concreto.
Conviene re-verificar el costo en contexto después de cada adición.
