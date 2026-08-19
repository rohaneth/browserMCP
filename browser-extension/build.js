const esbuild = require("esbuild");
const fs = require("fs");
const path = require("path");

const distDir = path.join(__dirname, "dist");
if (!fs.existsSync(distDir)) {
    fs.mkdirSync(distDir);
}

// Copy manifest
fs.copyFileSync(
    path.join(__dirname, "manifest.json"),
    path.join(distDir, "manifest.json")
);

esbuild.build({
    entryPoints: ["src/background/service_worker.ts", "src/content/content.ts"],
    bundle: true,
    outdir: "dist",
    format: "esm",
    target: ["es2022"],
    minify: false,
    sourcemap: true,
}).then(() => {
    console.log("Build complete.");
}).catch(() => process.exit(1));
