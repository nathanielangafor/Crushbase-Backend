tmux kill-session -t crushbase_backend
rm -r "Crushbase-Backend/" 

git clone https://github.com/nathanielangafor/Crushbase-Backend.git
cd Crushbase-Backend/
nano .env
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
tmux new -s crushbase_backend
python3 -m API.app
