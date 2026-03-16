Update quotes command:

python3 /home/ubuntu/.openclaw/workspace/ClawProject/us-market-radar/update-quotes.py

Then publish:

cd /home/ubuntu/.openclaw/workspace/ClawProject
git add us-market-radar/data/quotes.json us-market-radar/update-quotes.py
git commit -m "Refresh US Market Radar quotes"
git push origin main
