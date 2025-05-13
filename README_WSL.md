# WSL Configuration Guide for AI-Powered Development

Windows Subsystem for Linux (WSL) has become an essential development environment for Windows users, providing a seamless bridge between Windows and Linux development workflows. Beyond offering native Linux tooling, WSL enables access to powerful AI coding assistants like:

- [Amazon Q](https://aws.amazon.com/q/) – a comprehensive Generative AI Assistant that excels at automating repetitive development tasks across the entire software lifecycle. Amazon Q can perform in-depth code reviews to identify and fix [security vulnerabilities](https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/understand-code-issues.html), code smells, anti-patterns, and logical errors with auto-generated patches. It generates comprehensive documentation including READMEs and data flow diagrams by analyzing your entire codebase. Amazon Q also boosts test coverage by automatically writing unit tests with boundary conditions and edge cases, while self-debugging test errors.

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) - an Agentic Coding Tool by Anthropic that transforms development through its "Explore, plan, code, commit" workflow. According to Anthropic's [best practices guide](https://www.anthropic.com/engineering/claude-code-best-practices), Claude Code first explores your codebase, then uses different thinking intensities ("think" to "ultrathink") to create implementation plans before writing code. This methodical approach prevents rushing to solutions for complex problems, with Claude handling everything from initial exploration to final pull requests—all through natural language commands. This workflow particularly shines when thoughtful architecture is needed rather than quick code generation.

## Setting Up WSL for AI-Assisted Development

To use AI tools like Claude Code effectively with WSL, you'll need to set up your environment properly. Follow these steps to install the essential components:

1. **Install Windows Subsystem for Linux (WSL)**
   - Follow the [official Microsoft WSL setup guide](https://learn.microsoft.com/en-us/windows/wsl/setup/environment)
   - We recommend Ubuntu as the Linux distribution for compatibility

2. **Install Development Tools**
   - These tools are required for Claude Code and other AI assistants to function properly
   - **Python**: Follow [Microsoft's Python in WSL guide](https://learn.microsoft.com/en-us/windows/python/web-frameworks#install-windows-subsystem-for-linux)
   - **Node.js**: Follow [Microsoft's Node.js on WSL guide](https://learn.microsoft.com/en-us/windows/dev-environment/javascript/nodejs-on-wsl)

3. **Configure VS Code for WSL**
   - Follow the [VS Code with WSL tutorial](https://learn.microsoft.com/en-us/windows/wsl/tutorials/wsl-vscode)
   - This enables VS Code to seamlessly work with your WSL environment

These setup steps create the foundation needed for AI-powered development tools to effectively analyze and modify your codebase.

## Setting Up Git for WSL Development

This section addresses common Git issues when working with repositories in WSL and provides solutions for a streamlined development experience.

### Git User Configuration

When working with Git in WSL, you'll need to set up your user identity for commits:

```bash
# Configure your Git user information
git config user.email "your.email@example.com"  # Use your actual email
git config user.name "Your Name"                # Use your actual name
```

If you have authentication issues when pushing to repositories, configure Git to use the Windows credential manager:

```bash
# Configure Git to use Windows credential manager
git config --global credential.helper "/mnt/c/Program\ Files/Git/mingw64/bin/git-credential-manager.exe"
```

This allows you to use your Windows-stored credentials for Git operations in WSL.

### Common Issue: False "Modified Files"

When accessing Windows-based repositories through WSL's `/mnt/` paths, Git may incorrectly show numerous files as modified even when no changes have been made. This occurs due to:

1. **Line endings**: Windows uses CRLF (`\r\n`) while Linux uses LF (`\n`)
2. **File permissions**: WSL tracks executable bits that Windows Git ignores 

### Quick Fix Script

Run this script when working with a repository in WSL:

```bash
# Navigate to the repository root
cd /mnt/c/Users/your/path/to/repository

# Run the WSL Git fix script
./scripts/wsl-git-fix.sh
```

This script configures Git for WSL compatibility and resets any false modifications.

### Manual Configuration

If you prefer to understand what's happening, here are the key commands:

```bash
# Configure line ending behavior (only convert to LF when committing)
git config core.autocrlf input

# Ensure consistent line endings
git config core.eol lf

# Ignore file permission changes between Windows and WSL
git config core.fileMode false

# Reset the working directory to match the index (if needed)
# WARNING: This discards uncommitted changes!
git reset --hard
```

### Recommended `.gitattributes` File

For optimal cross-platform compatibility, add this `.gitattributes` file to your repository:

```bash
# Set default behavior to automatically normalize line endings
* text=auto

# Explicitly declare text files you want to always be normalized and converted
# to native line endings on checkout
*.js text
*.ts text
*.json text
*.md text
*.html text
*.css text
*.scss text
*.yml text
*.yaml text
*.xml text
*.txt text

# Declare files that will always have CRLF line endings on checkout
*.{cmd,[cC][mM][dD]} text eol=crlf
*.{bat,[bB][aA][tT]} text eol=crlf

# Declare files that will always have LF line endings on checkout
*.sh text eol=lf

# Denote all files that are truly binary and should not be modified
*.png binary
*.jpg binary
*.jpeg binary
*.gif binary
*.ico binary
*.zip binary
*.pdf binary
*.vsix binary
*.exe binary
```

This file helps maintain consistent line endings across platforms and should remain in your repository.

## VSCode Integration

For the best experience with VSCode and WSL:

1. Install the "Remote - WSL" extension in VSCode
2. Open your project through WSL by:
   - Clicking the green remote button in the bottom-left corner
   - Selecting "Remote-WSL: Open Folder in WSL..."
   - Navigating to your project folder

3. Add these settings to your VSCode `settings.json`:

```json
{
    "files.eol": "\n",
    "remote.WSL.fileWatcher.polling": true
}
```
