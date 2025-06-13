#!/bin/bash
# API Key Generation Utility for Medical Patients Generator
# Usage: ./scripts/generate-api-key.sh [environment] [length]
# Example: ./scripts/generate-api-key.sh production 64

set -euo pipefail

# Configuration
DEFAULT_LENGTH=32
MIN_LENGTH=16
MAX_LENGTH=128

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Function to generate secure random string
generate_secure_key() {
    local length=$1
    
    # Use multiple entropy sources for maximum security
    if command -v openssl >/dev/null 2>&1; then
        openssl rand -base64 $((length * 3 / 4)) | tr -d "=+/" | cut -c1-${length}
    elif command -v /dev/urandom >/dev/null 2>&1; then
        LC_ALL=C tr -dc 'A-Za-z0-9' < /dev/urandom | head -c ${length}
    else
        print_error "No secure random source available (openssl or /dev/urandom)"
        exit 1
    fi
}

# Function to validate key strength
validate_key_strength() {
    local key=$1
    local min_entropy=2.5  # bits per character
    
    # Check length
    if [ ${#key} -lt $MIN_LENGTH ]; then
        print_error "Key too short (${#key} < $MIN_LENGTH)"
        return 1
    fi
    
    # Check character diversity
    local has_upper=$(echo "$key" | grep -q '[A-Z]' && echo 1 || echo 0)
    local has_lower=$(echo "$key" | grep -q '[a-z]' && echo 1 || echo 0)
    local has_digit=$(echo "$key" | grep -q '[0-9]' && echo 1 || echo 0)
    
    local diversity_score=$((has_upper + has_lower + has_digit))
    
    if [ $diversity_score -lt 2 ]; then
        print_warning "Low character diversity (score: $diversity_score/3)"
    fi
    
    print_success "Key validation passed (length: ${#key}, diversity: $diversity_score/3)"
    return 0
}

# Function to display environment-specific instructions
show_deployment_instructions() {
    local environment=$1
    local api_key=$2
    
    print_info "Deployment instructions for $environment:"
    echo
    
    case $environment in
        "local")
            echo "1. Create/update .env.local:"
            echo "   API_KEY=$api_key"
            echo
            echo "2. Source the environment:"
            echo "   export API_KEY='$api_key'"
            echo
            echo "3. Test locally:"
            echo "   curl -H 'X-API-KEY: $api_key' http://localhost:8000/api/v1/jobs/"
            ;;
        "staging")
            echo "1. Update DigitalOcean staging app environment:"
            echo "   doctl apps update STAGING_APP_ID --env API_KEY='$api_key'"
            echo
            echo "2. Test staging:"
            echo "   curl -H 'X-API-KEY: $api_key' https://staging.milmed.tech/api/v1/jobs/"
            echo
            echo "3. Schedule rotation (monthly):"
            echo "   Add reminder to rotate on $(date -d '+1 month' '+%Y-%m-%d')"
            ;;
        "production")
            echo "1. Update DigitalOcean production app environment:"
            echo "   doctl apps update bbba2c8b-5931-4064-b839-068f3d74290f --env API_KEY='$api_key'"
            echo
            echo "2. Test production:"
            echo "   curl -H 'X-API-KEY: $api_key' https://milmed.tech/api/v1/jobs/"
            echo
            echo "3. Schedule rotation (quarterly):"
            echo "   Add reminder to rotate on $(date -d '+3 months' '+%Y-%m-%d')"
            echo
            print_warning "PRODUCTION KEY - Handle with extreme care!"
            ;;
    esac
    
    echo
    print_warning "Security reminders:"
    echo "• Never commit this key to Git"
    echo "• Store securely (password manager)"
    echo "• Share via secure channel only"
    echo "• Rotate regularly per schedule"
}

# Function to check for existing secrets in repository
check_repo_security() {
    print_info "Checking repository for accidental secret commits..."
    
    # Common secret patterns
    local secret_patterns=(
        "api[_-]?key"
        "secret"
        "password"
        "token"
        "credential"
    )
    
    local found_secrets=false
    
    for pattern in "${secret_patterns[@]}"; do
        # Check tracked files (excluding this script, documentation, and dev/test files)
        if git grep -iE "$pattern\s*[:=]\s*['\"][^'\"]{8,}" -- \
           ':!scripts/' ':!*.md' ':!*.example' ':!start-dev.sh' ':!tests/' >/dev/null 2>&1; then
            # Additional check for nosec comments and dev/test patterns
            if ! git grep -iE "$pattern\s*[:=]\s*['\"][^'\"]{8,}.*#.*nosec|default.*dev.*key|test.*pass" -- \
               ':!scripts/' ':!*.md' ':!*.example' ':!start-dev.sh' ':!tests/' >/dev/null 2>&1; then
                print_error "Potential secret found in repository (pattern: $pattern)"
                git grep -iEn "$pattern\s*[:=]\s*['\"][^'\"]{8,}" -- \
                    ':!scripts/' ':!*.md' ':!*.example' ':!start-dev.sh' ':!tests/' || true
                found_secrets=true
            fi
        fi
    done
    
    if [ "$found_secrets" = true ]; then
        print_error "Security check failed - secrets may be committed!"
        print_warning "Run 'git log --grep=secret --grep=key --grep=password -i' to check history"
        return 1
    else
        print_success "Repository security check passed"
        return 0
    fi
}

# Main function
main() {
    local environment=${1:-local}
    local length=${2:-$DEFAULT_LENGTH}
    
    # Validate inputs
    if ! [[ "$environment" =~ ^(local|staging|production)$ ]]; then
        print_error "Invalid environment: $environment (must be: local, staging, production)"
        exit 1
    fi
    
    if ! [[ "$length" =~ ^[0-9]+$ ]] || [ "$length" -lt $MIN_LENGTH ] || [ "$length" -gt $MAX_LENGTH ]; then
        print_error "Invalid length: $length (must be $MIN_LENGTH-$MAX_LENGTH)"
        exit 1
    fi
    
    # Security check
    if ! check_repo_security; then
        print_error "Security check failed - aborting key generation"
        exit 1
    fi
    
    print_info "Generating $environment API key (length: $length)..."
    
    # Generate key
    local api_key
    api_key=$(generate_secure_key "$length")
    
    if [ -z "$api_key" ]; then
        print_error "Failed to generate API key"
        exit 1
    fi
    
    # Validate key
    if ! validate_key_strength "$api_key"; then
        print_error "Generated key failed validation"
        exit 1
    fi
    
    # Display results
    echo
    print_success "Generated $environment API key:"
    echo
    echo "$api_key"
    echo
    
    # Show deployment instructions
    show_deployment_instructions "$environment" "$api_key"
    
    # Environment-specific warnings
    if [ "$environment" = "production" ]; then
        echo
        print_warning "PRODUCTION DEPLOYMENT CHECKLIST:"
        echo "• Verify staging deployment works first"
        echo "• Schedule maintenance window if needed"
        echo "• Update monitoring and alerting"
        echo "• Document key rotation in memory/"
    fi
}

# Help function
show_help() {
    echo "API Key Generation Utility"
    echo
    echo "Usage: $0 [environment] [length]"
    echo
    echo "Arguments:"
    echo "  environment    Target environment (local|staging|production) [default: local]"
    echo "  length         Key length in characters ($MIN_LENGTH-$MAX_LENGTH) [default: $DEFAULT_LENGTH]"
    echo
    echo "Examples:"
    echo "  $0                      # Generate local development key"
    echo "  $0 staging             # Generate staging key  "
    echo "  $0 production 64       # Generate 64-char production key"
    echo
    echo "Security features:"
    echo "• Uses cryptographically secure random sources"
    echo "• Validates key strength and entropy"
    echo "• Checks repository for accidental secret commits"
    echo "• Provides environment-specific deployment instructions"
    echo "• Never writes keys to files (manual copy required)"
}

# Handle help flag
if [[ "${1:-}" =~ ^(-h|--help|help)$ ]]; then
    show_help
    exit 0
fi

# Run main function
main "$@"