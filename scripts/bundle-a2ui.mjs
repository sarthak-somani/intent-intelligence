import { createHash } from "node:crypto";
import { promises as fs } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { execSync } from "node:child_process";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT_DIR = path.resolve(__dirname, "..");

const HASH_FILE = path.join(ROOT_DIR, "src/canvas-host/a2ui/.bundle.hash");
const OUTPUT_FILE = path.join(ROOT_DIR, "src/canvas-host/a2ui/a2ui.bundle.js");
const A2UI_RENDERER_DIR = path.join(ROOT_DIR, "vendor/a2ui/renderers/lit");
const A2UI_APP_DIR = path.join(ROOT_DIR, "apps/shared/OpenClawKit/Tools/CanvasA2UI");

const INPUT_PATHS = [
  path.join(ROOT_DIR, "package.json"),
  path.join(ROOT_DIR, "pnpm-lock.yaml"),
  A2UI_RENDERER_DIR,
  A2UI_APP_DIR,
];

async function walk(entryPath, files = []) {
  const st = await fs.stat(entryPath);
  if (st.isDirectory()) {
    const entries = await fs.readdir(entryPath);
    for (const entry of entries) {
      await walk(path.join(entryPath, entry), files);
    }
    return files;
  }
  files.push(entryPath);
  return files;
}

async function computeHash() {
  const files = [];
  for (const input of INPUT_PATHS) {
    if (await fs.access(input).then(() => true).catch(() => false)) {
      await walk(input, files);
    }
  }

  function normalize(p) {
    return p.split(path.sep).join("/");
  }

  files.sort((a, b) => normalize(a).localeCompare(normalize(b)));

  const hash = createHash("sha256");
  for (const filePath of files) {
    const rel = normalize(path.relative(ROOT_DIR, filePath));
    hash.update(rel);
    hash.update("\0");
    hash.update(await fs.readFile(filePath));
    hash.update("\0");
  }

  return hash.digest("hex");
}

async function main() {
  try {
    // Check if sources exist
    if (!await fs.access(A2UI_RENDERER_DIR).then(() => true).catch(() => false) ||
        !await fs.access(A2UI_APP_DIR).then(() => true).catch(() => false)) {
      console.log("A2UI sources missing; keeping prebuilt bundle.");
      process.exit(0);
    }

    const currentHash = await computeHash();

    if (await fs.access(HASH_FILE).then(() => true).catch(() => false)) {
      const previousHash = await fs.readFile(HASH_FILE, "utf-8");
      if (previousHash.trim() === currentHash && await fs.access(OUTPUT_FILE).then(() => true).catch(() => false)) {
        console.log("A2UI bundle up to date; skipping.");
        process.exit(0);
      }
    }

    console.log("Bundling A2UI...");

    // Run tsc
    console.log("Running tsc...");
    execSync(`pnpm -s exec tsc -p "${path.join(A2UI_RENDERER_DIR, "tsconfig.json")}"`, { stdio: "inherit", cwd: ROOT_DIR });

    // Run rolldown
    console.log("Running rolldown...");
    execSync(`pnpm exec rolldown -c "${path.join(A2UI_APP_DIR, "rolldown.config.mjs")}"`, { stdio: "inherit", cwd: ROOT_DIR });

    await fs.writeFile(HASH_FILE, currentHash);
    console.log("A2UI bundle created successfully.");

  } catch (error) {
    console.error("A2UI bundling failed.");
    console.error(error.message);
    process.exit(1);
  }
}

main();
