cd ..

set tmpdir=X:\temp
set botdir=%cd%

cd /d %tmpdir%

git clone %botdir%
cd testpilot_qqbot

move /y matcha\.env.prod .env.prod
move /y matcha\paths.json json\paths.json

cd json
move /y templates\*.json .

nb run --reload