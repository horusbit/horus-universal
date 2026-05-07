Set-Location "C:\Users\ecaam\Desktop\horus-universal"
git config user.email "horuseict@gmail.com"
git config user.name "horusbit"
git add -A
git commit -m "fix: backend limpio sin ImportError - UserProfile correcto en todos los modulos"
git push -u origin main --force
Write-Host "DONE" -ForegroundColor Green
pause
