#!/bin/zsh
set -euo pipefail

repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
app_name="Founder Atlas.app"
build_dir="$repo_dir/dist"
app_dir="$build_dir/$app_name"
resource_dir="$app_dir/Contents/Resources"
node_binary="${NODE_BINARY:-$(command -v node)}"

cd "$repo_dir/web"
npm run build

rm -rf "$app_dir"
mkdir -p "$app_dir/Contents/MacOS" "$resource_dir/web" "$resource_dir/content"
ditto "$repo_dir/web/.next/standalone" "$resource_dir/web"
mkdir -p "$resource_dir/web/.next"
ditto "$repo_dir/web/.next/static" "$resource_dir/web/.next/static"
ditto "$repo_dir/web/public" "$resource_dir/web/public"
rsync -a --exclude='*.transcript.json' --exclude='questions/log.jsonl' "$repo_dir/content/" "$resource_dir/content/"
cp -L "$node_binary" "$resource_dir/node"
chmod 755 "$resource_dir/node"

clang -O2 -fobjc-arc "$repo_dir/macos/FounderAtlasApp.m" -framework Cocoa -framework WebKit -o "$app_dir/Contents/MacOS/FounderAtlasApp"
clang -O2 -fobjc-arc "$repo_dir/macos/generate-icon.m" -framework Cocoa -o "$build_dir/generate-icon"
"$build_dir/generate-icon" "$build_dir/icon-1024.png"
iconset="$build_dir/FounderAtlas.iconset"
mkdir -p "$iconset"
for size in 16 32 128 256 512; do
  sips -z "$size" "$size" "$build_dir/icon-1024.png" --out "$iconset/icon_${size}x${size}.png" >/dev/null
  double=$((size * 2))
  sips -z "$double" "$double" "$build_dir/icon-1024.png" --out "$iconset/icon_${size}x${size}@2x.png" >/dev/null
done
iconutil -c icns "$iconset" -o "$resource_dir/AppIcon.icns"

cat > "$app_dir/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleName</key><string>Founder Atlas</string>
  <key>CFBundleDisplayName</key><string>Founder Atlas</string>
  <key>CFBundleIdentifier</key><string>com.founderatlas.local</string>
  <key>CFBundleExecutable</key><string>FounderAtlasApp</string>
  <key>CFBundleIconFile</key><string>AppIcon</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleShortVersionString</key><string>1.0</string>
  <key>CFBundleVersion</key><string>1</string>
  <key>NSHighResolutionCapable</key><true/>
  <key>NSAppTransportSecurity</key><dict><key>NSAllowsLocalNetworking</key><true/></dict>
</dict></plist>
PLIST

codesign --force --deep --sign - "$app_dir" >/dev/null
echo "$app_dir"
