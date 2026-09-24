# UHG

There are 4400 pdf files. Too large for a git commit. Only src


step 1: build a exploratory UI which crawls the files and reads which ones need OCR. 
Use threads, precrawl and boot up with past crawl info. This data isn't going to change. No use in recrawling. 
```
cd /Users/dc/united
.venv/bin/python -m streamlit run streamlit_app.py
```

