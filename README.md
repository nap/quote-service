Quotes-Service
==============

Quote from various famous personalities. This project is entended to be a standalone service, on a dedicated port, written in Python. It require the Tornado library for it's async socket management. 
Currently, the quote.json file contains over 17000 french quote from various author encoded with HTMLEntities.

JSON Object Schema
==================
```json
{
	"body": "<...omitted...>", 
	"author": "<...omitted...>", 
	"country": "France", 
	"iso": "fr", 
	"date": "<...omitted...>", 
	"id": 1
}
```

Dependency
==========
* Tornado: pip install tornado

Start
=====
```bash
unary$ python quote_service.py -h
Usage: python quote_service.py [quote_file] [port] [max_connections] [PADDING]
Default: python quote_service.py quote.json 8080 5000
Valid JSON (ex: filename.json) format: [{"key","value"}]

unary$ python quote_service.py quote.json 8080 5000 jsonp_func
Starting ... 
Serving 17039 quotes on port 8080.
Press Ctrl + C to quit. 
```

Output after HTTP GET will be:
```javascript
jsonp_func({"body": "<...omitted...>", "author": "Anonyme", "country": "Portugal", "iso": "pt", "date": "", "id": 3306});
```

License Terms
=============

	Copyright (C) 2012 Jean-Bernard Ratté (http://unary.ca)

	Permission is hereby granted, free of charge, to any person obtaining a copy 
	of this software and associated documentation files (the "Software"), to deal
	in the Software without restriction, including without limitation the rights
	to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
	copies of the Software, and to permit persons to whom the Software is 
	furnished to do so, subject to the following conditions:

	The above copyright notice and this permission notice shall be included in all
	copies or substantial portions of the Software.

	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
	IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
	FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
	AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
	LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
	OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE 
	SOFTWARE.