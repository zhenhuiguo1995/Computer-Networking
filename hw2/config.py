# defines the API in HTTP requests
EVAL_EXPRESSION = "evalexpression"
GET_TIME = "gettime"
STATUE = "status"
BAD_REQUEST = "400"
REQUEST_NOT_FOUND = "404"


# defines HTTP version
NON_PERSISTENT_HTTP = "1.0"
PERSISTENT_HTTP = "1.1"


# defines end of line signal
END_OF_LINE = b'\r\n'


# defines the regular expression pattern to be matched
REQUEST_LINE_PATTERN = "(?:GET/POST) (.*) HTTP/(.*)\r\n"
API_PATTERN = "/api/(.*)"
CONTENT_LENGTH_PATTERN = "Content-Length: (.*)\r\n"


# defines the Method name for HTTP requests
GET = "GET"
POST = "POST"

