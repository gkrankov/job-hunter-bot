@echo off
REM Check Git Status - Verify commit and push

cd /d "c:\Users\krank\job-hunter-bot.worktrees\copilot-worktree-2026-04-20T08-56-05"

echo.
echo ===== GIT STATUS CHECK =====
echo.

REM Check current git status
echo 1. Current Git Status:
echo ========================
git status
echo.

REM Check if there are uncommitted changes
echo 2. Files in working directory:
echo =============================
git status --short
echo.

REM Check recent commits (local)
echo 3. Recent Local Commits (last 5):
echo =================================
git log --oneline -5
echo.

REM Check if remote is set up
echo 4. Remote Configuration:
echo =======================
git remote -v
echo.

REM Compare local vs remote
echo 5. Local vs Remote Branches:
echo ============================
git branch -vv
echo.

REM Check if push is needed
echo 6. Commits to Push:
echo ===================
git log origin/main..HEAD --oneline 2>nul
if %errorlevel% equ 0 (
    echo Found commits ahead of remote.
) else (
    echo Local is up to date with remote.
)
echo.

REM Summary
echo.
echo ===== SUMMARY =====
echo.
for /f "tokens=*" %%A in ('git status --porcelain') do (
    set "has_changes=1"
)

if defined has_changes (
    echo STATUS: ❌ UNCOMMITTED CHANGES EXIST
    echo.
    echo You need to:
    echo 1. Run: git add .
    echo 2. Run: git commit -m "..."
    echo 3. Run: git push
    echo.
) else (
    echo STATUS: ✅ NO UNCOMMITTED CHANGES
    echo.
    
    for /f "tokens=*" %%B in ('git log origin/main..HEAD --oneline 2^>nul') do (
        set "needs_push=1"
    )
    
    if defined needs_push (
        echo ⚠️  COMMITS EXIST BUT NOT PUSHED
        echo.
        echo Run: git push
    ) else (
        echo ✅ ALL CHANGES COMMITTED AND PUSHED
    )
)
echo.
