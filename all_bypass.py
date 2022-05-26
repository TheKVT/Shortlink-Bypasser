import re, time, json, base64
import requests
import argparse
import cloudscraper
from urllib.parse import unquote 
from bs4 import BeautifulSoup
from urllib.parse import urlparse


# RECAPTCHA v3 BYPASS
def RecaptchaV3(ANCHOR_URL):
    url_base = 'https://www.google.com/recaptcha/'
    post_data = "v={}&reason=q&c={}&k={}&co={}"
    client = requests.Session()
    client.headers.update({
        'content-type': 'application/x-www-form-urlencoded'
    })
    matches = re.findall('([api2|enterprise]+)\/anchor\?(.*)', ANCHOR_URL)[0]
    url_base += matches[0]+'/'
    params = matches[1]
    res = client.get(url_base+'anchor', params=params)
    token = re.findall(r'"recaptcha-token" value="(.*?)"', res.text)[0]
    params = dict(pair.split('=') for pair in params.split('&'))
    post_data = post_data.format(params["v"], token, params["k"], params["co"])
    res = client.post(url_base+'reload', params=f'k={params["k"]}', data=post_data)
    answer = re.findall(r'"rresp","(.*?)"', res.text)[0]    
    return answer

ANCHOR_URL = 'https://www.google.com/recaptcha/api2/anchor?ar=1&k=6Lcr1ncUAAAAAH3cghg6cOTPGARa8adOf-y9zv2x&co=aHR0cHM6Ly9vdW8uaW86NDQz&hl=en&v=1B_yv3CBEV10KtI2HJ6eEXhJ&size=invisible&cb=4xnsug1vufyr'


#adfly Bypass
def decrypt_url(code):
    a, b = '', ''
    for i in range(0, len(code)):
        if i % 2 == 0: a += code[i]
        else: b = code[i] + b

    key = list(a + b)
    i = 0

    while i < len(key):
        if key[i].isdigit():
            for j in range(i+1,len(key)):
                if key[j].isdigit():
                    u = int(key[i]) ^ int(key[j])
                    if u < 10: key[i] = str(u)
                    i = j					
                    break
        i+=1
    
    key = ''.join(key)
    decrypted = b64decode(key)[16:-16]

    return decrypted.decode('utf-8')

def adfly_bypass(url):
    res = requests.get(url).text
    
    out = {'error': False, 'src_url': url}
    
    try:
        ysmm = re.findall("ysmm\s+=\s+['|\"](.*?)['|\"]", res)[0]
    except:
        out['error'] = True
        return out
        
    url = decrypt_url(ysmm)

    if re.search(r'go\.php\?u\=', url):
        url = b64decode(re.sub(r'(.*?)u=', '', url)).decode()
    elif '&dest=' in url:
        url = unquote(re.sub(r'(.*?)dest=', '', url))
    
    out['bypassed_url'] = url
    
    return out['bypassed_url']


#droplink Bypass

def droplink_bypass(url):
    client = requests.Session()
    res = client.get(url)

    ref = re.findall("action[ ]{0,}=[ ]{0,}['|\"](.*?)['|\"]", res.text)[0]

    h = {'referer': ref}
    res = client.get(url, headers=h)

    bs4 = BeautifulSoup(res.content, 'lxml')
    inputs = bs4.find_all('input')
    data = { input.get('name'): input.get('value') for input in inputs }

    h = {
        'content-type': 'application/x-www-form-urlencoded',
        'x-requested-with': 'XMLHttpRequest'
    }
    p = urlparse(url)
    final_url = f'{p.scheme}://{p.netloc}/links/go'

    time.sleep(3.1)
    res = client.post(final_url, data=data, headers=h).json()
    r = dict(res)
    return r['url']

#gplinks Bypass

def gplinks_bypass(url: str):
    client = cloudscraper.create_scraper(allow_brotli=False)
    p = urlparse(url)
    final_url = f'{p.scheme}://{p.netloc}/links/go'

    res = client.head(url)
    header_loc = res.headers['location']
    param = header_loc.split('postid=')[-1]
    req_url = f'{p.scheme}://{p.netloc}/{param}'

    p = urlparse(header_loc)
    ref_url = f'{p.scheme}://{p.netloc}/'

    h = { 'referer': ref_url }
    res = client.get(req_url, headers=h, allow_redirects=False)

    bs4 = BeautifulSoup(res.content, 'html.parser')
    inputs = bs4.find_all('input')
    data = { input.get('name'): input.get('value') for input in inputs }

    h = {
        'referer': ref_url,
        'x-requested-with': 'XMLHttpRequest',
    }
    time.sleep(10)
    res = client.post(final_url, headers=h, data=data)
    try:
        return res.json()['url'].replace('\/','/')
    except: return 'Something went wrong :('


#ouo.io / ouo.press Bypass

def ouo_bypass(url):
    client = requests.Session()
    tempurl = url.replace("ouo.press", "ouo.io")
    p = urlparse(tempurl)
    id = tempurl.split('/')[-1]
    
    res = client.get(tempurl)
    next_url = f"{p.scheme}://{p.hostname}/go/{id}"

    for _ in range(2):

        if res.headers.get('Location'):
            break

        bs4 = BeautifulSoup(res.content, 'lxml')
        inputs = bs4.form.find_all("input", {"name": re.compile(r"token$")})
        data = { input.get('name'): input.get('value') for input in inputs }
        
        ans = RecaptchaV3(ANCHOR_URL)
        data['x-token'] = ans
        
        h = {
            'content-type': 'application/x-www-form-urlencoded'
        }
        
        res = client.post(next_url, data=data, headers=h, allow_redirects=False)
        next_url = f"{p.scheme}://{p.hostname}/xreallcygo/{id}"

    return res.headers.get('Location')
    
#shorte.st Bypass

def sh_st_bypass(url):    
    client = requests.Session()
    client.headers.update({'referer': url})
    p = urlparse(url)
    
    res = client.get(url)

    sess_id = re.findall('''sessionId(?:\s+)?:(?:\s+)?['|"](.*?)['|"]''', res.text)[0]
    
    final_url = f"{p.scheme}://{p.netloc}/shortest-url/end-adsession"
    params = {
        'adSessionId': sess_id,
        'callback': '_'
    }
    time.sleep(5) # !important
    
    res = client.get(final_url, params=params)
    dest_url = re.findall('"(.*?)"', res.text)[1].replace('\/','/')
    
    return dest_url

def for_bypass(url):
   # This is only for links which just directly redirects to other url, just know  for what actually behind it ;)
    r = requests.get(url)
    return r.url

################################################ 



parser = argparse.ArgumentParser()
parser.add_argument('-i', '-u', '--url', nargs="?",
                    help="Short link to bypass", required=True)
parser.add_argument('-t', '--type', nargs="?",
                    help="Entered short link site name", required=True)
args = parser.parse_args()


URL = args.url
type = args.type
if type  == 'adfly' :
  print('You have seleted' , type)
  print("Entered_URL:", URL, '\n',"Bypassed_URL:",adfly_bypass(URL) )

elif type  == "droplink" :
   print('You have seleted' , type)
   print("Entered_URL:",URL,'\n',"Bypassed_URL:", droplink_bypass(URL))

elif type  == 'gplinks' :
   print('You have seleted' , type)
   print("Entered_URL:", URL, '\n',"Bypassed_URL:", gplinks_bypass(URL))

elif type  == "ouo" :
  print ('You have seleted' , type)
  print("Entered_URL:", URL, '\n',"Bypassed_URL:", ouo_bypass(URL))
elif type  == "sh_st":
  print ('You have seleted' , type)
  print("Entered_URL:", URL, '\n',"Bypassed_URL:", sh_st_bypass(URL))
elif type  == "simple":
  print('You have seleted' , type)
  print("Entered_URL:", URL, '\n',"Bypassed_URL:", for_bypass(URL))
else :
   print("Enter site name correctly only these are suppoted :",'\n',"adfly",'\n',"droplink",'\n',"gplinks",'\n','ouo','\n',"sh_st",'\n',"only redirect links")






















