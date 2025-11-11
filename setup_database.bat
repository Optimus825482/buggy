@echo off
REM Buggy Call - Database Setup Script (Windows)
REM Bu script database migration sistemini otomatik olarak kurar

echo ============================================================
echo Buggy Call - Database Migration Setup
echo ============================================================
echo.

REM Check if flask is available
where flask >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [91mX Flask command not found![0m
    echo Please activate your virtual environment first:
    echo   venv\Scripts\activate
    exit /b 1
)

echo [92m✓ Flask found[0m
echo.

REM Step 1: Initialize migrations
echo [96mStep 1: Initializing migrations...[0m
if exist migrations (
    echo [93m! Migrations folder already exists[0m
    set /p response="Do you want to reinitialize? (yes/no): "
    if not "!response!"=="yes" (
        echo [91mX Aborted[0m
        exit /b 0
    )
    rmdir /s /q migrations
    echo [92m✓ Removed existing migrations[0m
)

flask db init
if %ERRORLEVEL% EQU 0 (
    echo [92m✓ Migrations initialized[0m
) else (
    echo [91mX Failed to initialize migrations[0m
    exit /b 1
)
echo.

REM Step 2: Create initial migration
echo [96mStep 2: Creating initial migration...[0m
flask db migrate -m "Initial migration - all models"
if %ERRORLEVEL% EQU 0 (
    echo [92m✓ Migration created[0m
) else (
    echo [91mX Failed to create migration[0m
    exit /b 1
)
echo.

REM Step 3: Apply migration
echo [96mStep 3: Applying migration to database...[0m
flask db upgrade
if %ERRORLEVEL% EQU 0 (
    echo [92m✓ Migration applied[0m
) else (
    echo [91mX Failed to apply migration[0m
    exit /b 1
)
echo.

REM Step 4: Verify
echo [96mStep 4: Verifying migration...[0m
flask db current
echo.

echo ============================================================
echo [92m✓ Database migration setup completed![0m
echo ============================================================
echo.
echo What was created:
echo   - migrations/ folder with Alembic configuration
echo   - Initial migration file in migrations/versions/
echo   - All database tables created
echo.
echo Useful commands:
echo   flask db current   - Show current migration
echo   flask db history   - Show migration history
echo   flask db upgrade   - Apply PENDING migrations
echo   flask db downgrade - Rollback last migration
echo.

pause
