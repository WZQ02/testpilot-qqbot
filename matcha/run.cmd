cd ..

set tmpdir=X:\temp
set botdir=%cd%

cd /d %tmpdir%

git clone %botdir%
cd testpilot_qqbot

copy /y %botdir%\matcha\.env.prod .env.prod

cd json
move /y templates\*.json .

nb run --reload