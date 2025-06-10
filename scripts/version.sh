#!/bin/bash
# Version management script for Military Medical Patient Generator

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get current version
get_current_version() {
    if [ -f VERSION ]; then
        cat VERSION
    else
        echo "0.0.0"
    fi
}

# Update version in all files
update_version_files() {
    local new_version=$1
    
    print_info "Updating version to $new_version in all files..."
    
    # Update VERSION file
    echo "$new_version" > VERSION
    
    # Update package.json
    if [ -f package.json ]; then
        sed -i.bak "s/\"version\": \".*\"/\"version\": \"$new_version\"/" package.json
        rm package.json.bak
    fi
    
    # Update pyproject.toml if it exists
    if [ -f pyproject.toml ]; then
        sed -i.bak "s/version = \".*\"/version = \"$new_version\"/" pyproject.toml
        rm pyproject.toml.bak
    fi
    
    print_info "Version updated in all files"
}

# Bump version
bump_version() {
    local bump_type=$1
    local current_version=$(get_current_version)
    
    # Parse current version
    IFS='.' read -ra VERSION_PARTS <<< "$current_version"
    local major=${VERSION_PARTS[0]:-0}
    local minor=${VERSION_PARTS[1]:-0}
    local patch=${VERSION_PARTS[2]:-0}
    
    case $bump_type in
        "major")
            major=$((major + 1))
            minor=0
            patch=0
            ;;
        "minor")
            minor=$((minor + 1))
            patch=0
            ;;
        "patch")
            patch=$((patch + 1))
            ;;
        *)
            print_error "Invalid bump type. Use: major, minor, or patch"
            exit 1
            ;;
    esac
    
    local new_version="$major.$minor.$patch"
    echo "$new_version"
}

# Create release
create_release() {
    local version=$1
    local changelog_entry="$2"
    
    print_info "Creating release $version..."
    
    # Check if we're on develop branch
    local current_branch=$(git branch --show-current)
    if [ "$current_branch" != "develop" ]; then
        print_warning "Not on develop branch. Current: $current_branch"
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Update version files
    update_version_files "$version"
    
    # Create release branch
    local release_branch="release/$version"
    git checkout -b "$release_branch"
    
    # Commit version changes
    git add VERSION package.json pyproject.toml CHANGELOG.md 2>/dev/null || true
    git commit -m "chore: Bump version to $version

$changelog_entry

🤖 Generated with version management script"
    
    print_info "Release branch '$release_branch' created"
    print_info "Next steps:"
    echo "  1. Test the release thoroughly"
    echo "  2. Push release branch: git push -u origin $release_branch"
    echo "  3. Create PR to main branch"
    echo "  4. After merge, create GitHub release"
    echo "  5. Merge main back to develop"
}

# Create GitHub release
create_github_release() {
    local version=$1
    local changelog_entry="$2"
    
    print_info "Creating GitHub release $version..."
    
    # Create tag
    git tag -a "v$version" -m "Release $version

$changelog_entry"
    
    # Push tag
    git push origin "v$version"
    
    # Create GitHub release if gh CLI is available
    if command -v gh &> /dev/null; then
        gh release create "v$version" \
            --title "Release $version" \
            --notes "$changelog_entry" \
            --latest
    else
        print_warning "GitHub CLI not installed. Create release manually at:"
        echo "https://github.com/$(git remote get-url origin | sed 's/.*github.com[:/]\([^/]*\/[^/]*\)\.git/\1/')/releases/new?tag=v$version"
    fi
}

# Main script
case "${1:-help}" in
    "current")
        echo "Current version: $(get_current_version)"
        ;;
    
    "bump")
        if [ -z "$2" ]; then
            print_error "Usage: $0 bump <major|minor|patch>"
            exit 1
        fi
        new_version=$(bump_version "$2")
        echo "Would bump from $(get_current_version) to $new_version"
        ;;
    
    "set")
        if [ -z "$2" ]; then
            print_error "Usage: $0 set <version>"
            exit 1
        fi
        update_version_files "$2"
        print_info "Version set to $2"
        ;;
    
    "release")
        if [ -z "$2" ]; then
            print_error "Usage: $0 release <major|minor|patch> [changelog_entry]"
            exit 1
        fi
        new_version=$(bump_version "$2")
        changelog_entry="${3:-Release $new_version}"
        create_release "$new_version" "$changelog_entry"
        ;;
    
    "tag")
        if [ -z "$2" ]; then
            print_error "Usage: $0 tag <version> [changelog_entry]"
            exit 1
        fi
        changelog_entry="${3:-Release $2}"
        create_github_release "$2" "$changelog_entry"
        ;;
    
    "help"|*)
        echo "Version management script for Military Medical Patient Generator"
        echo ""
        echo "Usage: $0 <command> [options]"
        echo ""
        echo "Commands:"
        echo "  current              Show current version"
        echo "  bump <type>          Show what the bumped version would be"
        echo "  set <version>        Set version in all files"
        echo "  release <type> [msg] Create release branch with version bump"
        echo "  tag <version> [msg]  Create GitHub release and tag"
        echo "  help                 Show this help"
        echo ""
        echo "Bump types: major, minor, patch"
        echo ""
        echo "Examples:"
        echo "  $0 current"
        echo "  $0 bump minor"
        echo "  $0 set 1.2.3"
        echo "  $0 release minor 'Add new features'"
        echo "  $0 tag 1.2.3 'Bug fixes and improvements'"
        ;;
esac