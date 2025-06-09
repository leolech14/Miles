#!/bin/bash

# Miles Repository Branch Maintenance Script
# Cleans up old/stale feature branches

set -e

echo "🌿 Miles Repository Branch Maintenance"
echo "====================================="

echo "📊 Current branch status:"
git branch -a

echo ""
echo "🧹 Checking for stale branches..."

# Find merged feature branches that can be cleaned up
MERGED_BRANCHES=$(git branch -r --merged main | grep -E "feature/|fix/|hotfix/" | grep -v main | sed 's/origin\///' || true)

if [[ -z ${MERGED_BRANCHES} ]]; then
	echo "✅ No stale branches found."
else
	echo "🗑️  Found merged branches that can be cleaned up:"
	echo "${MERGED_BRANCHES}"

	echo ""
	read -p "Delete these merged branches? (y/N): " -n 1 -r
	echo
	if [[ ${REPLY} =~ ^[Yy]$ ]]; then
		echo "${MERGED_BRANCHES}" | xargs -I {} git push origin --delete {} 2>/dev/null || true
		echo "✅ Cleanup completed!"
	else
		echo "Skipped."
	fi
fi

echo ""
echo "📊 Final branch status:"
git branch -a

echo ""
echo "🎯 Branch strategy reminder:"
echo "- main: Production-ready code"
echo "- feature/*: New features from main"
echo "- fix/*: Bug fixes from main"
echo "- hotfix/*: Emergency fixes from main"
