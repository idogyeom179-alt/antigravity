import requests
url = 'https://worklog-coral.vercel.app/app.js'
text = requests.get(url).text
print(text[:15000])
