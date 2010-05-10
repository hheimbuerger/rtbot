import urllib

valid_expiration_values = ('N', '10M', '1H', '1D', '1M')

def postToPastebin(	message,
	title = "RTBot",
	subdomain = "rtbot",
	expire_date = "1D",
	format = "text"):
  
  if expire_date not in valid_expiration_values:
    raise Exception("invalid expire_date (must be one of %r, got %r instead)" % (valid_expiration_values, expire_date))
  
  request_dict = {	"paste_code":	message,
  	"paste_name":	title,
  	"paste_subdomain":	subdomain,
  	"paste_expire_date":	expire_date,
  	"paste_format":	format }
  request = urllib.urlencode(request_dict)
  result = urllib.urlopen("http://pastebin.com/api_public.php", request)
  return result.read() #either an error message or a pastebin url
    
  
  
  
