patches
============================
Please do not apply these patches unless,
* You understand what they do.
* You understand how the license of the original software affects you if you
  do apply them.


web_socketio apache configuration
=================================

The server "python web_socketio/web_socketio/server.py -d mydb" must be run as
the same user as OpenERP.

Apache requires that the least specific URL be first. This is the opposite of
the documentation for web_socketio addon.

<VirtualHost *:80>
    ServerAdmin jssuzanne@anybox.fr
    ServerName www.myopenerp.fr
    <location />
            ProxyPreserveHost On
            ProxyPass http://localhost:8069/
            ProxyPassReverse http://localhost:8069/
    </location>
    <location /socket.io>
            ProxyPreserveHost On
            ProxyPass http://localhost:8068/socket.io
            ProxyPassReverse http://localhost:8068/socket.io
    </location>
    <location /socket.io/1/websocket>
            ProxyPreserveHost On
            ProxyPass ws://localhost:8068/socket.io/1/websocket
            ProxyPassReverse ws://localhost:8068/socket.io/1/websocket
    </location>

</VirtualHost>


web_socketio are needed for popup on call
=========================================
https://bitbucket.org/anybox/web_socketio/ (for 7.x use hg checkout default)



WARNING WARNING WARNING
=======================

Do not just close windows/tabs/browser sessions. This will cause the web_socketio
server to consume resources (memory and CPU). Additionally, it starts losing pop-up requests.
Eventually, it just stops. Click to dial and caller id look-up continue to work.

ALWAYS LOG OUT PROPERLY!

Additionally, any time you restart OpenERP, you MUST then restart the web_socketio
server. Restarting the proxy (apache or nginx), after restarting the others,
is a good idea.
