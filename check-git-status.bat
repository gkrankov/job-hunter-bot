@echo off
REM Simple diagnostic to show commit status clearly

cd /d "c:\Users\krank\job-hunter-bot.worktrees\copilot-worktree-2026-04-20T08-56-05"

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║          GIT COMMIT & PUSH STATUS DIAGNOSTIC              ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Check for uncommitted changes
git status --porcelain > "%temp%\git_status.txt"

REM Check if commits need to be pushed
git log origin/main..HEAD --oneline > "%temp%\git_unpushed.txt" 2>nul

REM Count uncommitted files
for /f %%a in ('find /c /v "" ^< "%temp%\git_status.txt"') do set "uncommitted=%%a"

REM Count unpushed commits
for /f %%b in ('find /c /v "" ^< "%temp%\git_unpushed.txt"') do set "unpushed=%%b"

echo.
echo 📊 ANALYSIS:
echo ════════════
echo Uncommitted changes: %uncommitted%
echo Unpushed commits: %unpushed%
echo.

if %uncommitted% GTR 0 (
    echo ❌ STATUS: UNCOMMITTED CHANGES EXIST
    echo.
    echo Files with changes:
    type "%temp%\git_status.txt"
    echo.
    echo ACTION REQUIRED:
    echo 1. git add .
    echo 2. git commit -m "Tier 1 Improvements..."
    echo 3. git push
    echo.
) else if %unpushed% GTR 0 (
    echo ⚠️  STATUS: COMMITTED BUT NOT PUSHED
    echo.
    echo Commits waiting to be pushed:
    type "%temp%\git_unpushed.txt"
    echo.
    echo ACTION REQUIRED:
    echo Run: git push
    echo.
) else (
    echo ✅ STATUS: ALL CHANGES COMMITTED AND PUSHED!
    echo.
    echo Last commit:
    git log -1 --oneline
    echo.
    echo ✨ You're all set! Users can now use:
    echo    - python job_hunter.py validate
    echo    - python job_hunter.py run --top 5
    echo.
)

echo.
echo 📋 RECENT COMMITS:
echo ══════════════════
git log --oneline -3
echo.

echo 🔗 REMOTE STATUS:
echo ═════════════════
git branch -vv | findstr "main"
echo.

REM Cleanup
del "%temp%\git_status.txt"
del "%temp%\git_unpushed.txt"

echo Done.
echo.
