#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Sythos <sythos@gmail.com>
# Author: Sythos <sythos@gmail.com>
#
# MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Print the changelog section of one version, for example: release-notes.sh 0.2.0
# The command fails if the section does not exist or if it is empty.
set -euo pipefail

version="${1:?Give the version number, for example 0.2.0}"
changelog="${2:-CHANGELOG.md}"

notes=$(awk -v heading="## ${version} " '
  index($0, heading) == 1 { found = 1; next }
  /^## / { found = 0 }
  found { print }
' "${changelog}")

if [ -z "$(printf '%s' "${notes}" | tr -d '[:space:]')" ]; then
  echo "No changelog section for version ${version} in ${changelog}" >&2
  exit 1
fi

printf '%s\n' "${notes}"
