#!/usr/bin/python
import os, sys, pipes, commands, requests, signal

def child(username):
	# Send a GET request to our logserver to log disconnecting client
	# this might block if unavailable, so we must be detached from
	# pluto.
	url = 'https://logserver.example.com/delete/'
	payload = {'username': username}
	r = requests.get(url, data=payload)

	fp = open("/tmp/terminate.log","a")
	fp.write("Termination notification sent for %s\n"%username)
	fp.write("HTTP status code:%s\n"%r.status_code)
	fp.write(r.text)
	fp.write("\n")
	fp.close()
	os._exit(0)

if __name__ == '__main__':
	if len(sys.argv) < 2:
		# nothing to log
		sys.exit(0)

	username = sys.argv[1]
	if username != pipes.quote(username):
		sys.exit("bogus characters in username '%s', ignored termination request"%username)

	# Redirect standard file descriptors to ensure pluto does not block on us
	os.close(0)
	os.close(1)
	os.close(2)
	os.close(3) # pluto.log - workaround for bug #202

	# Do a double fork to decouple from the parent environment
	pid = os.fork()
	if pid > 0:
		# exit first parent
		sys.exit(0)

	os.chdir("/")
	os.setsid()
	os.umask(0)

	# do second fork
	pid = os.fork()
	if pid > 0:
		# exit from second parent
		sys.exit(0)

	# we're fully detached now - take as long as needed to do the work
	child(username)

