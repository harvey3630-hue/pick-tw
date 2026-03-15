@echo off
echo [1] 重建網站...
cd /d "D:\N8N全自動工作流\Pick-tw"
hugo --minify --baseURL "https://pick-tw.com"
if %errorlevel% neq 0 (echo 建置失敗！ & exit /b 1)

echo [2] 部署到 GitHub Pages...
cd public
git add -A
git commit -m "Deploy: %date% %time%"
git push -f origin HEAD:gh-pages

echo [3] 完成！網站已更新
pause
