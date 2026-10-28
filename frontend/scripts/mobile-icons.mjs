import { readFileSync, writeFileSync } from "node:fs";
import { Resvg } from "@resvg/resvg-js";

const svg = readFileSync(new URL("../public/icons/icon-512.svg", import.meta.url), "utf8");
function render(path, size, source = svg) {
  writeFileSync(new URL(path, import.meta.url), new Resvg(source, { fitTo: { mode: "width", value: size } }).render().asPng());
}
for (const [density, size] of Object.entries({ mdpi: 48, hdpi: 72, xhdpi: 96, xxhdpi: 144, xxxhdpi: 192 })) {
  for (const kind of ["ic_launcher", "ic_launcher_round"]) render(`../android/app/src/main/res/mipmap-${density}/${kind}.png`, size);
  const foreground = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><g transform="translate(85 85) scale(.667)">${svg.replace(/<\/?svg[^>]*>/g, "")}</g></svg>`;
  render(`../android/app/src/main/res/mipmap-${density}/ic_launcher_foreground.png`, Math.round(size * 2.25), foreground);
}
render("../ios/App/App/Assets.xcassets/AppIcon.appiconset/AppIcon-512@2x.png", 1024, svg.replace('rx="110"', 'rx="0"'));
console.log("FreshSense icons generated for Android and iPhone.");
