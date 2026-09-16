// Type-check page probes in isolated programs, one program per probe group.
//
// A monolithic `tsc` program makes every ambient declaration visible to every probe. That
// lets a probe accidentally depend on a sibling group's page fixture and stay green until it
// runs in a page where that fixture is absent. The manifest names the few intentional shared
// declarations; group-local `.d.ts` files remain local by construction.
import { readdirSync, readFileSync } from "node:fs";
import { dirname, isAbsolute, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

/**
 * @typedef {{
 *   path: string,
 *   commonDeclarations?: string[],
 *   dependencies?: Record<string, string[]>,
 * }} ProbeRoot
 * @typedef {{name: string, sources: string[], declarations?: string[]}} StandaloneProgram
 * @typedef {{probeRoots: ProbeRoot[], standalonePrograms?: StandaloneProgram[]}} Manifest
 * @typedef {{name: string, sources: string[], files: string[]}} TypeProgram
 */

const repository = fileURLToPath(new URL("../../../", import.meta.url));

/**
 * Resolve a manifest path without allowing it to escape the selected root.
 * @param {string} root
 * @param {string} path
 */
function inside(root, path) {
  const absolute = resolve(root, path);
  const fromRoot = relative(root, absolute);
  if (fromRoot === ".." || fromRoot.startsWith(`..${process.platform === "win32" ? "\\" : "/"}`)) {
    throw new Error(`path escapes the type-check root: ${path}`);
  }
  return absolute;
}

/**
 * Return matching files below a directory, in stable order, refusing symlink traversal.
 * @param {string} directory
 * @param {readonly string[]} suffixes
 */
function filesBelow(directory, suffixes) {
  /** @type {string[]} */
  const found = [];
  for (const entry of readdirSync(directory, { withFileTypes: true }).sort((a, b) =>
    a.name.localeCompare(b.name),
  )) {
    const path = resolve(directory, entry.name);
    if (entry.isSymbolicLink()) {
      throw new Error(`probe type-check does not follow symlinks: ${path}`);
    }
    if (entry.isDirectory()) {
      found.push(...filesBelow(path, suffixes));
    } else if (entry.isFile() && suffixes.some((suffix) => entry.name.endsWith(suffix))) {
      found.push(path);
    }
  }
  return found;
}

/**
 * Read and minimally validate the manifest before it controls compiler inputs.
 * @param {string} path
 * @returns {Manifest}
 */
function readManifest(path) {
  const value = /** @type {unknown} */ (JSON.parse(readFileSync(path, "utf8")));
  if (typeof value !== "object" || value === null || !("probeRoots" in value)) {
    throw new Error(`${path}: expected an object with probeRoots`);
  }
  const manifest = /** @type {Manifest} */ (value);
  if (!Array.isArray(manifest.probeRoots)) {
    throw new Error(`${path}: probeRoots must be an array`);
  }
  return manifest;
}

/**
 * Expand one manifest into the exact independent programs the compiler receives.
 * @param {string} root
 * @param {Manifest} manifest
 * @returns {TypeProgram[]}
 */
function programsFromManifest(root, manifest) {
  /** @type {TypeProgram[]} */
  const programs = [];
  const ownedSources = new Set();
  for (const specification of manifest.probeRoots) {
    const probeRoot = inside(root, specification.path);
    const common = (specification.commonDeclarations ?? []).map((path) => inside(root, path));
    const entries = readdirSync(probeRoot, { withFileTypes: true });
    const ungroupedSources = entries
      .filter((entry) => entry.isFile() && entry.name.endsWith(".js"))
      .map((entry) => entry.name);
    if (ungroupedSources.length > 0) {
      throw new Error(
        `${specification.path}: probes must belong to a group directory: ${ungroupedSources.join(", ")}`,
      );
    }
    const rootDeclarations = entries
      .filter((entry) => entry.isFile() && entry.name.endsWith(".d.ts"))
      .map((entry) => resolve(probeRoot, entry.name));
    const missingCommon = rootDeclarations.filter((path) => !common.includes(path));
    if (missingCommon.length > 0) {
      throw new Error(
        `${specification.path}: root declarations are not listed as common: ${missingCommon.join(", ")}`,
      );
    }
    const groups = entries
      .filter((entry) => entry.isDirectory())
      .sort((a, b) => a.name.localeCompare(b.name));
    const groupNames = new Set(groups.map((entry) => entry.name));
    for (const dependencyGroup of Object.keys(specification.dependencies ?? {})) {
      if (!groupNames.has(dependencyGroup)) {
        throw new Error(`${specification.path}: dependencies name no group: ${dependencyGroup}`);
      }
    }
    for (const group of groups) {
      const directory = resolve(probeRoot, group.name);
      const sources = filesBelow(directory, [".js"]);
      const declarations = filesBelow(directory, [".d.ts"]);
      if (sources.length === 0) {
        if (declarations.length > 0) {
          throw new Error(`${specification.path}/${group.name}: declarations have no probes`);
        }
        continue;
      }
      const dependencies = (specification.dependencies?.[group.name] ?? []).map((path) =>
        inside(root, path),
      );
      for (const source of sources) {
        if (ownedSources.has(source)) {
          throw new Error(`probe source belongs to more than one program: ${source}`);
        }
        ownedSources.add(source);
      }
      programs.push({
        name: `${specification.path}/${group.name}`,
        sources,
        files: [...sources, ...declarations, ...common, ...dependencies],
      });
    }
  }
  for (const standalone of manifest.standalonePrograms ?? []) {
    const sources = standalone.sources.map((path) => inside(root, path));
    for (const source of sources) {
      if (ownedSources.has(source)) {
        throw new Error(`probe source belongs to more than one program: ${source}`);
      }
      ownedSources.add(source);
    }
    programs.push({
      name: standalone.name,
      sources,
      files: [...sources, ...(standalone.declarations ?? []).map((path) => inside(root, path))],
    });
  }
  if (programs.length === 0) {
    throw new Error("probe type-check manifest selected no programs");
  }
  return programs;
}

/**
 * Load the shared strict compiler options while replacing its source selection.
 * @param {string} configPath
 * @returns {ts.CompilerOptions}
 */
function compilerOptions(configPath) {
  const read = ts.readConfigFile(configPath, ts.sys.readFile);
  if (read.error) {
    throw new Error(ts.flattenDiagnosticMessageText(read.error.messageText, "\n"));
  }
  const parsed = ts.parseJsonConfigFileContent(
    read.config,
    ts.sys,
    dirname(configPath),
    undefined,
    configPath,
  );
  const errors = parsed.errors.filter((diagnostic) => diagnostic.code !== 18003);
  if (errors.length > 0) {
    throw new Error(ts.formatDiagnostics(errors, diagnosticHost(dirname(configPath))));
  }
  return {
    ...parsed.options,
    noEmit: true,
    incremental: false,
    composite: false,
    // The pinned compiler's own DOM and ES declarations are identical in every group.
    // Checking them once per group dominates this gate; group and dependency `.d.ts` files
    // are not default libraries and remain fully checked.
    skipDefaultLibCheck: true,
  };
}

/**
 * The stable path and newline policy TypeScript uses for diagnostics.
 * @param {string} root
 * @returns {ts.FormatDiagnosticsHost}
 */
function diagnosticHost(root) {
  return {
    getCanonicalFileName: (path) => path,
    getCurrentDirectory: () => root,
    getNewLine: () => "\n",
  };
}

/**
 * Type-check every program, sharing parsed library and source files without sharing scope.
 * @param {string} root
 * @param {TypeProgram[]} programs
 * @param {ts.CompilerOptions} options
 */
function checkPrograms(root, programs, options) {
  const host = ts.createCompilerHost(options);
  const getSourceFile = host.getSourceFile.bind(host);
  /** @type {Map<string, ts.SourceFile>} */
  const cache = new Map();
  host.getSourceFile = (fileName, languageVersion, onError, shouldCreateNewSourceFile) => {
    if (!shouldCreateNewSourceFile && cache.has(fileName)) {
      return cache.get(fileName);
    }
    const source = getSourceFile(fileName, languageVersion, onError, shouldCreateNewSourceFile);
    if (source && !shouldCreateNewSourceFile) {
      cache.set(fileName, source);
    }
    return source;
  };

  let failed = false;
  for (const group of programs) {
    const program = ts.createProgram(group.files, options, host);
    const diagnostics = ts.getPreEmitDiagnostics(program);
    if (diagnostics.length === 0) {
      continue;
    }
    failed = true;
    process.stderr.write(`\n${group.name}:\n`);
    process.stderr.write(ts.formatDiagnostics(diagnostics, diagnosticHost(root)));
  }
  return failed ? 1 : 0;
}

/**
 * Parse the deliberately small command surface.
 * @param {string[]} argv
 * @returns {{root: string, manifest: string, config: string, listSources: boolean}}
 */
function argumentsFrom(argv) {
  let root = repository;
  let manifest = "packing/devtools/probe-typecheck.json";
  let config = "tsconfig.base.json";
  let listSources = false;
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === "--list-sources") {
      listSources = true;
    } else if (argument === "--root" || argument === "--manifest" || argument === "--config") {
      const value = argv[index + 1];
      if (value === undefined) {
        throw new Error(`${argument} needs a value`);
      }
      index += 1;
      if (argument === "--root") {
        root = resolve(value);
      } else if (argument === "--manifest") {
        manifest = value;
      } else {
        config = value;
      }
    } else {
      throw new Error(`unknown argument: ${argument}`);
    }
  }
  return {
    root,
    manifest: isAbsolute(manifest) ? manifest : inside(root, manifest),
    config: isAbsolute(config) ? config : inside(root, config),
    listSources,
  };
}

try {
  const options = argumentsFrom(process.argv.slice(2));
  const programs = programsFromManifest(options.root, readManifest(options.manifest));
  if (options.listSources) {
    const sources = programs
      .flatMap((program) => program.sources)
      .map((path) => relative(options.root, path).replaceAll("\\", "/"))
      .sort();
    process.stdout.write(`${JSON.stringify(sources)}\n`);
  } else {
    process.exitCode = checkPrograms(options.root, programs, compilerOptions(options.config));
  }
} catch (error) {
  process.stderr.write(`${error instanceof Error ? error.message : String(error)}\n`);
  process.exitCode = 1;
}
