#!/usr/bin/env python3
"""
Simple GitHub Token Setup Script
Gets repository owner and automatically retrieves GitHub app installation ID
and GitHub PAT secret ID, then saves the GitHub token to Google Cloud Secret Manager.
"""

import subprocess
import sys
import tempfile
import secrets
import string
import os


def run_command(cmd, capture_output=False, check=True):
    """Run a command and handle output."""
    try:
        result = subprocess.run(cmd, capture_output=capture_output, text=True, check=check)
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {' '.join(cmd)}")
        print(f"Error: {e}")
        raise


def gcloud_cmd():
    return 'gcloud.cmd' if os.name == 'nt' else 'gcloud'


def get_github_app_installation_id(repository_owner, repo_name):
    """Get GitHub App Installation ID for Google Cloud Build."""
    print("🔍 To get your GitHub App Installation ID for Google Cloud Build:")
    print("1. Go to: https://github.com/settings/installations")
    print("2. Find 'Google Cloud Build' in the list")
    print("3. Click on it to see the installation details")
    print("4. Look at the URL - it should be like: https://github.com/settings/installations/12345678")
    print("5. The number at the end (12345678) is your installation ID")
    print("\nAlternatively, you can install Google Cloud Build GitHub App if not installed:")
    print("- Go to: https://github.com/marketplace/google-cloud-build")
    print("- Click 'Set up a plan' and install it on your repositories")
    
    # Try to get it programmatically first
    try:
        result = run_command([
            'gh', 'api', '/user/installations',
            '--jq', '.installations[] | select(.app_slug=="google-cloud-build") | .id'
        ], capture_output=True)
        installation_id = result.stdout.strip()
        if installation_id and installation_id != 'null':
            print(f"\n✅ Found Google Cloud Build installation ID: {installation_id}")
            return installation_id
    except subprocess.CalledProcessError:
        pass
    
    # If automatic detection fails, ask user to enter manually
    print(f"\n❌ Could not automatically detect Google Cloud Build installation ID")
    manual_id = input("Please enter your Google Cloud Build GitHub App Installation ID: ").strip()
    
    if manual_id and manual_id.isdigit():
        return manual_id
    else:
        print("❌ Invalid installation ID. Please enter a numeric ID.")
        return None


def get_github_token():
    """Get GitHub token from GitHub CLI."""
    try:
        result = run_command(['gh', 'auth', 'token'], capture_output=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        print("❌ Failed to get GitHub token from CLI")
        print("Please run: gh auth login")
        return None


def create_or_update_secret(secret_id, secret_value, project_id):
    """Create or update a secret in Google Cloud Secret Manager."""
    print(f"🔐 Creating/updating secret: {secret_id}")
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
        temp_file.write(secret_value)
        temp_file.flush()
        
        try:
            # First try to add a new version to existing secret
            run_command([
                gcloud_cmd(), 'secrets', 'versions', 'add', secret_id,
                '--data-file', temp_file.name,
                f'--project={project_id}'
            ])
            print(f"✅ Updated existing secret: {secret_id}")
        except subprocess.CalledProcessError:
            # If adding version fails (secret doesn't exist), create it
            try:
                run_command([
                    gcloud_cmd(), 'secrets', 'create', secret_id,
                    '--data-file', temp_file.name,
                    f'--project={project_id}',
                    '--replication-policy', 'automatic'
                ])
                print(f"✅ Created new secret: {secret_id}")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to create/update secret: {e}")
                raise


def main():
    """Main function."""
    print("🔑 GitHub Token Setup")
    print("====================")
    
    # Get required inputs from user
    repository_owner = input("Enter repository owner: ").strip()
    repo_name = input("Enter repository name: ").strip()
    project_id = input("Enter Google Cloud project ID: ").strip()
    
    if not repository_owner or not repo_name or not project_id:
        print("❌ Repository owner, repository name, and project ID are required")
        sys.exit(1)
    
    # Generate a random 6-character alphanumeric string for path_id
    path_id = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(6))
    
    # Generate the github_pat_secret_id
    github_pat_secret_id = f"git-{repo_name}-github-oauthtoken-{path_id}"
    
    # Get GitHub App Installation ID
    print("\n🔍 Getting GitHub App Installation ID...")
    github_app_installation_id = get_github_app_installation_id(repository_owner, repo_name)
    if not github_app_installation_id:
        print("⚠️  Could not retrieve GitHub App Installation ID, using placeholder")
        github_app_installation_id = "placeholder-id"
    else:
        print(f"✅ Retrieved GitHub App Installation ID: {github_app_installation_id}")
    
    # Print the three required variables in the requested format
    print("\n" + "="*60)
    print(f'repository_owner           = "{repository_owner}"')
    print(f'github_app_installation_id = "{github_app_installation_id}"')
    print(f'github_pat_secret_id       = "{github_pat_secret_id}"')
    print("="*60)
    
    # Check if GitHub CLI is available and get token
    try:
        run_command(['gh', '--version'], capture_output=True)
        print("\n✅ GitHub CLI is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("\n❌ GitHub CLI not found. Please install it first.")
        sys.exit(1)
    
    # Get GitHub token automatically
    github_token = get_github_token()
    if not github_token:
        sys.exit(1)
    print("✅ Retrieved GitHub token from CLI")
    
    # Check if gcloud is available
    try:
        run_command([gcloud_cmd(), '--version'], capture_output=True)
        print("✅ Google Cloud CLI is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Google Cloud CLI not found. Please install it first.")
        sys.exit(1)
    
    # Set the project
    try:
        run_command([gcloud_cmd(), 'config', 'set', 'project', project_id])
        print(f"✅ Set active project to {project_id}")
    except subprocess.CalledProcessError:
        print(f"❌ Failed to set project {project_id}")
        sys.exit(1)
    
    # Enable Secret Manager API
    try:
        run_command([gcloud_cmd(), 'services', 'enable', 'secretmanager.googleapis.com', f'--project={project_id}'])
        print("✅ Enabled Secret Manager API")
    except subprocess.CalledProcessError:
        print("❌ Failed to enable Secret Manager API")
        sys.exit(1)
    
    # Save GitHub token to Secret Manager using the generated secret ID
    try:
        create_or_update_secret(github_pat_secret_id, github_token, project_id)
        print(f"\n🎉 Successfully saved GitHub token to Secret Manager!")
        print(f"Secret ID: {github_pat_secret_id}")
        print(f"Secret Value: GitHub token (saved securely)")
        print(f"Project: {project_id}")
        
        print(f"\n📋 Copy these values for later use:")
        print("="*60)
        print(f'repository_owner           = "{repository_owner}"')
        print(f'github_app_installation_id = "{github_app_installation_id}"')
        print(f'github_pat_secret_id       = "{github_pat_secret_id}"')
        print("="*60)
    except Exception as e:
        print(f"\n❌ Failed to save token: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()