-- wrk invokes init once per load-generator thread, not once per request.
function init(args)
  local file = assert(io.open(args[1], "rb"))
  local body = file:read("*a")
  file:close()
  wrk.method = "POST"
  wrk.headers["Content-Type"] = "application/octet-stream"
  wrk.body = body
end
