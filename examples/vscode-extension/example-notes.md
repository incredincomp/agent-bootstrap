# Example Notes: VS Code Extension Repository

This document guides an agent performing discovery or bootstrap on a Visual Studio Code extension repository.

---

## Likely repository characteristics

- Primary language: TypeScript (overwhelmingly standard for modern VS Code extensions)
- Build system: `esbuild`, `webpack`, or `tsc` directly
- Package manager: `npm` or `yarn`; `pnpm` in some projects
- Dependency files: `package.json`, `package-lock.json` or `yarn.lock`
- Runtime: Node.js; VS Code Extension Host
- Test framework: `@vscode/test-electron` or `@vscode/test-cli` (integration), `mocha` or `jest` (unit)
- Extension manifest: `package.json` (also serves as extension manifest via `contributes`, `activationEvents`, `engines.vscode`)
- Publishing: `vsce` (VS Code Extension CLI) or `ovsx` for Open VSX
- Common structure:
  - `src/` — TypeScript source files
  - `out/` or `dist/` — compiled output (gitignored)
  - `test/` — test suite
  - `media/` or `resources/` — icons, webview assets
  - `.vscode/` — launch configs for debugging the extension

---

## What an agent should prioritize in discovery

1. **`package.json`:** This is the single most important file. It contains the extension manifest (`contributes`, `activationEvents`, `engines.vscode`), scripts, and dependencies all in one place. Read it first.
2. **Extension entry point:** `"main"` field in `package.json` points to the compiled entry point; trace back to `src/extension.ts` (the `activate()` function).
3. **Contribution points:** The `contributes` section of `package.json` defines all commands, menus, settings, keybindings, views — this is the public API of the extension.
4. **Activation events:** `activationEvents` (or `*` for always-on) determines when the extension code runs — important for understanding lifecycle.
5. **Build pipeline:** Check `scripts` in `package.json` for `compile`, `watch`, `package`, `vscode:prepublish`.
6. **VS Code API version:** `engines.vscode` in `package.json` — determines which VS Code APIs are available.
7. **Webview presence:** If `src/` contains a webview panel or custom editor, it has a significantly more complex build (separate HTML/CSS/JS bundle).

---

## Typical authoritative files

| File | Why authoritative |
|------|------------------|
| `package.json` | Extension manifest + build config + dependencies |
| `tsconfig.json` | TypeScript compiler config |
| `src/extension.ts` | Extension entry point (`activate()` / `deactivate()`) |
| `.vscodeignore` | Controls what is excluded from the published `.vsix` |
| `CHANGELOG.md` | Often required by the marketplace; tracks user-visible changes |
| `.vscode/launch.json` | Debug configuration for the Extension Development Host |

---

## Common traps

- **`out/` or `dist/` in the repo:** These are compiled artifacts. Do not read them as source. Find the corresponding `src/` file.
- **`package.json` dual role:** It is both the Node.js package manifest AND the VS Code extension manifest. Be careful when modifying it — both roles must remain valid.
- **VS Code API version drift:** Code written for an older `engines.vscode` version may use deprecated APIs. Check the target version before using new APIs.
- **Webview security:** Webview content must use a `ContentSecurityPolicy` nonce. Do not write webview code that bypasses the CSP.
- **Test environment:** VS Code extension integration tests run inside an Extension Development Host — they require a specific launch setup and cannot run in a standard Node.js test environment.
- **`vsce package` behavior:** The `.vscodeignore` file controls packaging. Missing files from the package is a common publish failure — check it if the published extension behaves differently than the dev environment.
- **Marketplace requirements:** A well-formed `README.md`, `CHANGELOG.md`, and publisher ID in `package.json` are required for marketplace publishing.

---

## Good first milestone after bootstrap

**Milestone 2 — Add unit tests for core command handlers**

Scope:
- Identify the primary command handler(s) registered in `activate()`
- Write unit tests using `mocha` or `jest` (without the Extension Host, mocking VS Code API where needed)
- Confirm tests run with `npm test` or the equivalent script
- Update `IMPLEMENTATION_TRACKER.md`

Why this milestone: VS Code extensions often have no unit tests, relying only on manual testing. Adding unit tests for command handlers is low-risk, high-value, and does not require the Extension Development Host.
