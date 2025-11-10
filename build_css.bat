@echo off
echo Building production Tailwind CSS...
tailwindcss.exe -i static\css\input.css -o static\css\tailwind-built.css --minify
echo Done! Production CSS built successfully.
pause
