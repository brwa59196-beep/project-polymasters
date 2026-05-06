@echo off
setlocal

set "TARGET_BRANCH=%~1"
if "%TARGET_BRANCH%"=="" set "TARGET_BRANCH=main"

where git >nul 2>nul
if errorlevel 1 (
    echo ERROR: git is not installed or is not available in PATH.
    echo Install Git for Windows, then run this script again.
    exit /b 1
)

if not exist pyproject.toml (
    echo ERROR: pyproject.toml was not found in the current folder.
    echo Run this script from the repository root, for example:
    echo   cd C:\Users\shtik\optionbot_codex
    exit /b 1
)

git rev-parse --is-inside-work-tree >nul 2>nul
if errorlevel 1 (
    echo ERROR: this folder is not a Git repository.
    echo Clone the GitHub repository first, then run this script inside it.
    exit /b 1
)

git remote get-url origin >nul 2>nul
if errorlevel 1 (
    echo ERROR: git remote 'origin' is not configured.
    echo Add it with:
    echo   git remote add origin https://github.com/brwa59196-beep/project-polymasters.git
    exit /b 1
)

git add .
git diff --cached --quiet
if errorlevel 1 (
    git commit -m "Update project files"
    if errorlevel 1 exit /b 1
) else (
    echo No local file changes to commit.
)

echo Pushing to origin/%TARGET_BRANCH%...
git push origin HEAD:%TARGET_BRANCH%
if errorlevel 1 (
    echo.
    echo Push failed. If Git asks for credentials, authenticate once with GitHub.
    echo Recommended: install GitHub CLI, run 'gh auth login', then re-run this script.
    exit /b 1
)

echo Done. Refresh GitHub to see the files on branch %TARGET_BRANCH%.
