---
description: How to create a feature branch and PR for review
---

# Feature Branch & PR Workflow

Use this workflow when implementing new features to enable cross-model review.

## Steps

1. Create a feature branch from main:
```powershell
git checkout main
git pull origin main
git checkout -b feature/<feature-number>-<short-description>
```
Example: `git checkout -b feature/1.2-file-upload`

2. Make your changes and commit frequently with conventional commits:
```powershell
git add -A
git commit -m "feat(<scope>): <description>"
```

3. Push the feature branch to origin:
// turbo
```powershell
git push -u origin feature/<branch-name>
```

4. Create a Pull Request using GitHub CLI:
```powershell
gh pr create --title "feat(<scope>): <title>" --body "<description>" --base main
```

5. Share the PR URL with the user for cross-model review.

## Naming Conventions

- **Branches**: `feature/<feature-id>-<short-name>` (e.g., `feature/1.2-file-upload`)
- **Commits**: Use [Conventional Commits](https://www.conventionalcommits.org/)
  - `feat`: New feature
  - `fix`: Bug fix
  - `docs`: Documentation
  - `test`: Adding tests
  - `refactor`: Code refactoring

## Review Process

After PR is created:
1. User can share PR link with other AI models for review
2. Address any feedback with additional commits
3. Squash and merge when approved
