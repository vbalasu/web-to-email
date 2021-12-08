from chalice import Chalice

app = Chalice(app_name='web-to-email')

import boto3, json, base64, datetime
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, unquote_plus
def url_to_html(url):
    lam = boto3.client('lambda')
    function_name = 'web-to-png-pdf-ConvertFunction-KUR1ON362oK7'
    payload = bytes('{"queryStringParameters": {"url": "URL_GOES_HERE"}}'.replace('URL_GOES_HERE', url), 'utf-8')
    response = lam.invoke(FunctionName=function_name, Payload=payload, LogType='Tail')
    html = json.loads(response['Payload'].read())['body']
    return html

def html_to_email(html, email, url):
    soup = BeautifulSoup(html, 'html.parser')
    img = soup.find_all('img')[0]
    img_base64 = img.get_attribute_list('src')[0].split(',')[1]
    with open('/tmp/website.png', 'wb') as f:
        f.write(base64.b64decode(img_base64))
    pdf = soup.find_all('iframe')[0]
    pdf_base64 = pdf.get_attribute_list('src')[0].split(',')[1]
    with open('/tmp/website.pdf', 'wb') as f:
        f.write(base64.b64decode(pdf_base64))
    ses = boto3.client('ses')
    now = datetime.datetime.utcnow().isoformat()
    subject = f'{url} as of {now}'
    from email.message import EmailMessage
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = 'support@cloudmatica.com'
    msg['To'] = email
    with open('/tmp/website.png', 'rb') as f:
        file_data = f.read()
        file_name = f.name
    msg.add_attachment(file_data, maintype='image', subtype='png', filename=file_name)
    with open('/tmp/website.pdf', 'rb') as f:
        file_data = f.read()
        file_name = f.name
    msg.add_attachment(file_data, maintype='application', subtype='pdf', filename=file_name)
    ses.send_raw_email(RawMessage={'Data': msg.as_bytes()})

# USAGE: curl http://127.0.0.1:8000/email/vbalasu%40gmail.com/url/https%3A%2F%2Fgoogle.com
@app.route('/email/{email}/url/{url}')
def index(email, url):
    email = unquote_plus(email)
    url = unquote_plus(url)
    print(email, url)
    html = url_to_html(url)
    html_to_email(html, email, url)
    return {'success': f'Sent {url} to {email}'}

@app.schedule('rate(1 day)')
def rate_handler(event):
    import boto3
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(name='web-to-email-config')
    daily_reports = table.get_item(Key={'id': 'daily_reports'})['Item']['data']
    for r in daily_reports:
        print(r['email'], r['url'])
        index(r['email'], r['url'])

@app.route('/daily')
def daily():
    import boto3
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(name='web-to-email-config')
    daily_reports = table.get_item(Key={'id': 'daily_reports'})['Item']['data']
    for r in daily_reports:
        print(r['email'], r['url'])
        index(r['email'], r['url'])
    return {'success': 'daily reports sent'}

# The view function above will return {"hello": "world"}
# whenever you make an HTTP GET request to '/'.
#
# Here are a few more examples:
#
# @app.route('/hello/{name}')
# def hello_name(name):
#    # '/hello/james' -> {"hello": "james"}
#    return {'hello': name}
#
# @app.route('/users', methods=['POST'])
# def create_user():
#     # This is the JSON body the user sent in their POST request.
#     user_as_json = app.current_request.json_body
#     # We'll echo the json body back to the user in a 'user' key.
#     return {'user': user_as_json}
#
# See the README documentation for more examples.
#
