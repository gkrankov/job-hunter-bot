@echo off
REM Ultra-simple git status check

cd /d "C:\Users\krank\job-hunter-bot.worktrees\copilot-worktree-2026-04-20T08-56-05"

echo.
echo ============================================
echo   GIT STATUS CHECK - SIMPLE VERSION
echo ============================================
echo.

REM Show status
echo CHECKING FOR UNCOMMITTED CHANGES...
echo.
git status --porcelain

REM Show if no output (clean working tree)
if %errorlevel% equ 0 (
    git status | findstr "working tree clean" > nul
    if %errorlevel% equ 0 (
        echo.
        echo ✅ CLEAN: No uncommitted changes
        echo.
        echo CHECKING IF PUSHED...
        echo.
        git log origin/main..HEAD --oneline
        if %errorlevel% equ 0 (
            echo.
            echo ✅ PUSHED: All commits are on remote
        ) else (
            echo.
            echo ⚠️  UNPUSHED: Run "git push"
        )
    )
) else (
    echo.
    echo ❌ CHANGES EXIST: Need to commit first
)

echo.
echo RECENT COMMIT:
git log -1 --oneline
echo.

echo BRANCH STATUS:
git branch -vv | findstr "main"
echo.
