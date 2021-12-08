# web-to-email

This application builds upon web-to-png-pdf to deliver an email to the specified address with attachments containing the png and pdf version of a website.

The overall design is as follows:
1. Scheduled trigger is invoked each day
2. A Lambda function checks a Dynamodb table
3. The table returns a list of email addresses and urls
4. The lambda function loops through the list and invokes the web-to-png-pdf lambda for each item
5. The result of the lambda function is parsed using BeautifulSoup and save to files
6. An email message is composed with attachments and sent