#!/bin/bash
# 版本一致性校验：VERSION、.skillhub.json、README、CHANGELOG 四处必须一致
set -euo pipefail

RED="[0;31m"
GREEN="[0;32m"
YELLOW="[0;33m"
NC="[0m"

fail() { echo -e "${RED}FAIL${NC}: $1"; exit 1; }
info() { echo -e "${GREEN}PASS${NC}: $1"; }
warn() { echo -e "${YELLOW}WARN${NC}: $1"; }

# 1. 读取 VERSION
if [[ ! -f VERSION ]]; then
  fail "VERSION file not found"
fi
version="$(tr -d '[:space:]' < VERSION)"
[[ -n "$version" ]] || fail "VERSION file is empty"

# 2. 读取 .skillhub.json
if [[ -f .skillhub.json ]]; then
  skillhub_version="$(python3 -c 'import json,sys; print(json.load(open(".skillhub.json",encoding="utf-8"))["version"])')"
  [[ "$version" == "$skillhub_version" ]] || fail "VERSION ($version) != .skillhub.json ($skillhub_version)"
else
  warn ".skillhub.json not found, skipping check"
fi

# 3. 检查 README 版本标记
if [[ -f README.md ]]; then
  readme_versions="$(python3 -c '
import re, sys
text = open("README.md", encoding="utf-8").read()
matches = re.findall(r"(?:当前版本|Version)[：:]\s*\*{0,2}(v?[\d][\w.\-]*)\*{0,2}", text)
for m in matches:
    print(m)
')"
  if [[ -n "$readme_versions" ]]; then
    while IFS= read -r readme_version; do
      readme_version="$(echo "$readme_version" | tr -d '[:space:]')"
      [[ "$version" == "$readme_version" ]] || fail "VERSION ($version) != README ($readme_version)"
    done <<< "$readme_versions"
  else
    warn "README.md has no version marker"
  fi
else
  warn "README.md not found"
fi

# 4. 检查 CHANGELOG
if [[ -f CHANGELOG.md ]]; then
  # Normalize version for CHANGELOG lookup (remove v prefix for matching)
  ver_nov="${version#v}"
  changelog_has_version="$(grep -cE "^## ${version}$|^## ${ver_nov}$|^## ${version}[ (]|^## ${ver_nov}[ (]" CHANGELOG.md || true)"
  [[ "$changelog_has_version" != "0" ]] || fail "CHANGELOG.md has no section for $version"
else
  fail "CHANGELOG.md not found"
fi

info "version metadata is consistent: $version"

