@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "ROOT=%%~fI"

set "INPUT=%~1"
if "%INPUT%"=="" set "INPUT=documentation.adoc"
set "OUTPUT=%~2"
if "%OUTPUT%"=="" set "OUTPUT=Milestone-2.pdf"

for %%I in ("%SCRIPT_DIR%section_role_propagator.rb") do set "EXT=%%~fI"
for %%I in ("%SCRIPT_DIR%.") do set "THEMES=%%~fsI"

pushd "%ROOT%"
call asciidoctor-pdf --failure-level ERROR -a pdf-themesdir="%THEMES%" -a pdf-theme=highlighting-theme.yml -r "%EXT%" "%INPUT%" -o "%OUTPUT%" 2>&1
set "RC=%ERRORLEVEL%"
popd
if not "%RC%"=="0" (
  echo asciidoctor-pdf failed with %RC% 1>&2
  exit /b %RC%
)
echo Built PDF: %OUTPUT% 1>&2
